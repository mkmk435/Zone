"""Canonical assembly round-trip for the LLM morphing mode.

The LLM never receives raw bytes: it receives a label-annotated Intel-syntax
listing of the payload code and must return a complete, morphed replacement.
This module is the bridge in both directions:

* ``from_zone()`` extracts the code and the (already extracted) data blob from
  a :class:`pobf.Zone` instance and renders the code as assembly.  Every direct
  branch target becomes a label and every reference into the data blob uses a
  ``DATA_*`` label, so a later layout change cannot leave a stale displacement.
* ``assemble()`` appends the data definitions (the LLM is not allowed to touch
  them), cleans the model output and assembles everything with Keystone.
* ``validate()`` performs the checks that do not require executing the payload:
  full disassembly coverage, branch targets on instruction boundaries, data
  references still inside the blob, and the ``RET_*`` adjacency used by getpc
  idioms.

The module is deliberately independent from the API client so it can be tested
offline.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

from capstone import (Cs, CS_ARCH_X86, CS_GRP_CALL, CS_GRP_JUMP, CS_MODE_32,
                      CS_MODE_64)
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KS_MODE_64


class LLMPayloadError(RuntimeError):
    """Raised when the payload cannot be rendered/assembled/validated."""


# Direct branches that Keystone resolves through a label.  ``loop`` and the
# jcxz family keep their rel8 encoding, so the prompt tells the model to expand
# them when the distance can grow.
_BRANCH_MNEMONICS = {
    "call", "jmp", "ja", "jae", "jb", "jbe", "jc", "je", "jg", "jge", "jl",
    "jle", "jna", "jnae", "jnb", "jnbe", "jnc", "jne", "jng", "jnge", "jnl",
    "jnle", "jno", "jnp", "jns", "jnz", "jo", "jp", "jpe", "jpo", "js", "jz",
    "loop", "loope", "loopne", "loopnz", "loopz", "jcxz", "jecxz", "jrcxz",
}

# Instructions that are safe filler: they do not modify registers or flags and
# do not touch the stack.  Used only by the structural check.
_NOP_MNEMONICS = {"nop", "pause"}


@dataclass
class DataPiece:
    """One contiguous data section inside the appended blob."""

    index: int
    offset: int          # offset from the start of the blob
    length: int
    data: bytes
    stub_offset: Optional[int] = None   # 32-bit getpc stub before the section
    callee: Optional[int] = None        # code address the stub calls


@dataclass
class CanonicalPayload:
    arch: str
    code: bytes
    blob: bytes
    source: str
    data_source: str
    pieces: List[DataPiece] = field(default_factory=list)
    labels: List[int] = field(default_factory=list)
    ret_labels: List[int] = field(default_factory=list)
    comments: dict = field(default_factory=dict)
    data_base: int = 0          # original address of the data blob

    @property
    def code_start(self) -> int:
        return 0

    @property
    def data_start(self) -> int:
        # data is appended immediately after the code in the canonical layout
        return len(self.code)


@dataclass
class AssembledPayload:
    payload: bytes
    code: bytes
    code_len: int
    source: str


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    similarity: float = 1.0
    code_len: int = 0
    instruction_count: int = 0

    def summary(self) -> str:
        status = "ok" if self.ok else "failed"
        parts = [f"static validation {status}",
                 f"{self.code_len} code bytes",
                 f"{self.instruction_count} instructions",
                 f"similarity {self.similarity:.2f}"]
        return ", ".join(parts)


def _mode(arch: str) -> int:
    if arch == "x64":
        return CS_MODE_64
    if arch == "x86":
        return CS_MODE_32
    raise LLMPayloadError(f"unsupported architecture: {arch}")


def _ks_mode(arch: str) -> int:
    if arch == "x64":
        return KS_MODE_64
    if arch == "x86":
        return KS_MODE_32
    raise LLMPayloadError(f"unsupported architecture: {arch}")


def _disassembler(arch: str) -> Cs:
    cs = Cs(CS_ARCH_X86, _mode(arch))
    cs.detail = True
    return cs


def _is_direct_branch(insn) -> bool:
    if not insn.operands or insn.operands[0].type != X86_OP_IMM:
        return False
    # Capstone does not put every loop/jcxz form in CS_GRP_JUMP, so the
    # mnemonic set is a required fallback.
    return (bool(insn.group(CS_GRP_JUMP))
            or bool(insn.group(CS_GRP_CALL))
            or insn.mnemonic.lower() in _BRANCH_MNEMONICS)


def _fmt_bytes(data: bytes) -> str:
    return ", ".join(f"0x{byte:02x}" for byte in data)


def _label(prefix: str, address: int) -> str:
    return f"{prefix}_{address:x}"


def _data_label(piece_index: int, delta: int = 0) -> str:
    label = f"DATA_{piece_index}"
    if delta:
        label += f" + {delta}"
    return label


def _piece_containing(pieces: Sequence[DataPiece], offset: int) -> Optional[DataPiece]:
    for piece in pieces:
        if piece.stub_offset is not None and offset == piece.stub_offset:
            return piece
        if piece.offset <= offset < piece.offset + piece.length:
            return piece
    return None


def _label_for_offset(pieces: Sequence[DataPiece], offset: int) -> Optional[str]:
    for piece in pieces:
        if piece.stub_offset is not None and offset == piece.stub_offset:
            return f"DATA_STUB_{piece.index}"
        if piece.offset <= offset < piece.offset + piece.length:
            return _data_label(piece.index, offset - piece.offset)
    return None


def build_data_source(pieces: Sequence[DataPiece], blob: bytes) -> str:
    """Render the appended data as assembly, including 32-bit getpc stubs."""
    if not blob:
        return ""
    lines: List[str] = []
    cursor = 0
    for piece in sorted(pieces, key=lambda item: item.offset):
        if piece.stub_offset is not None:
            if piece.stub_offset < cursor:
                raise LLMPayloadError(
                    f"data section {piece.index} overlaps the previous one")
            if piece.stub_offset > cursor:
                lines.append(f"    .byte {_fmt_bytes(blob[cursor:piece.stub_offset])}")
            if piece.callee is None:
                raise LLMPayloadError(
                    f"data section {piece.index} has no getpc callee")
            lines.append(f"DATA_STUB_{piece.index}:")
            lines.append(f"    call L_{piece.callee:x}")
            cursor = piece.stub_offset + 5
        if piece.offset < cursor:
            raise LLMPayloadError(
                f"data section {piece.index} overlaps the previous one")
        if piece.offset > cursor:
            lines.append(f"    .byte {_fmt_bytes(blob[cursor:piece.offset])}")
        lines.append(f"DATA_{piece.index}:")
        lines.append(f"    .byte {_fmt_bytes(piece.data)}")
        cursor = piece.offset + piece.length
    if cursor < len(blob):
        lines.append(f"    .byte {_fmt_bytes(blob[cursor:])}")
    if cursor > len(blob):
        raise LLMPayloadError("data sections exceed the data blob")
    return "\n".join(lines)


def from_zone(zone, arch: str) -> CanonicalPayload:
    """Build the canonical listing from a Zone instance.

    ``zone`` must already have run data extraction and ``finalize_data_refs``
    when the payload contains data.
    """
    code = b"".join(instr.new_instruction.bytes for instr in zone.instructions)
    if not zone.extracted_data and not zone.morph_applied \
            and len(code) == zone.sweep_coverage:
        code += zone.sweep_tail

    blob = b""
    pieces: List[DataPiece] = []
    if zone.extracted_data:
        if not zone.data_refs_finalized:
            raise LLMPayloadError(
                "finalize_data_refs() must run before from_zone()")
        blob = zone.final_data_blob or b""
        data_start = zone.final_code_len + len(zone.final_data_pad)
        for index, section in enumerate(zone.extracted_data):
            offset = section["new_address"] - data_start
            piece = DataPiece(index=index, offset=offset,
                              length=len(section["bytes"]),
                              data=bytes(section["bytes"]))
            for fixup in zone.data_ref_fixups:
                is_stub = (fixup.get("kind") == "getpc_stub"
                           or (arch == "x86"
                               and fixup.get("kind") == "getpc"
                               and "callee" in fixup))
                if fixup.get("section") == index and is_stub:
                    piece.stub_offset = offset - 5
                    piece.callee = fixup.get("callee")
                    break
            pieces.append(piece)

    fixups = list(zone.data_ref_fixups) if zone.extracted_data else []
    return canonicalize(code, blob, arch, pieces, fixups,
                        data_start=(zone.final_code_len
                                    + len(zone.final_data_pad))
                        if zone.extracted_data else len(code))


def canonicalize(code: bytes, blob: bytes, arch: str,
                 pieces: Sequence[DataPiece] = (),
                 fixups: Sequence[dict] = (),
                 data_start: Optional[int] = None) -> CanonicalPayload:
    """Render ``code`` as label-based Intel assembly.

    ``fixups`` are the records produced by ``Zone.extract_data()``; they tell
    us which instruction/operand references the data blob, including ``imm``
    and ``abs`` references that cannot be recognised from the bytes alone.
    """
    if not code:
        raise LLMPayloadError("empty payload")
    cs = _disassembler(arch)
    insns = list(cs.disasm(code, 0))
    covered = sum(insn.size for insn in insns)
    if covered != len(code):
        # Keep undecodable gaps as data.  This should be rare after -xd.
        pass

    data_start = len(code) if data_start is None else data_start
    pieces = list(pieces)
    fixups = list(fixups)

    addresses = {insn.address: insn for insn in insns}
    fixup_by_source = {}
    for fixup in fixups:
        fixup_by_source.setdefault(int(fixup["source"]), []).append(fixup)

    branch_targets = set()
    ret_labels = set()
    comments = {}

    # RIP-relative references to code (jump tables, function pointers) are
    # relocatable too: label the target if it is an instruction boundary.
    for insn in insns:
        for operand in insn.operands:
            if operand.type != X86_OP_MEM or operand.mem.base != X86_REG_RIP:
                continue
            target = insn.address + insn.size + operand.mem.disp
            if target in addresses:
                branch_targets.add(target)

    for insn in insns:
        if _is_direct_branch(insn):
            target = insn.operands[0].imm
            if 0 <= target < len(code):
                branch_targets.add(target)
            if insn.mnemonic == "call" and 0 <= target < len(code):
                target_insn = addresses.get(target)
                next_address = insn.address + insn.size
                if target == next_address or (
                        target_insn is not None
                        and target_insn.mnemonic == "pop"):
                    # Classic getpc: the return address pushed by the call is
                    # used as a code/data base by the pop.  It must stay
                    # immediately after the call.
                    ret_labels.add(next_address)
                    comments[insn.address] = (
                        "GETPC: the instruction labelled RET_ must stay "
                        "immediately after this call")
        if insn.address in fixup_by_source:
            for fixup in fixup_by_source[insn.address]:
                if fixup.get("kind") == "getpc_stub":
                    callee = fixup.get("callee")
                    if callee is not None:
                        branch_targets.add(int(callee))

    # Data labels referenced by the appended data stubs must exist in code.
    for piece in pieces:
        if piece.callee is not None:
            branch_targets.add(piece.callee)

    def replace_rip(text: str, label: str) -> str:
        # Capstone may print small displacements in decimal (`[rip + 5]`) and
        # larger ones in hex (`[rip + 0x5f]`).
        return re.sub(r"\[rip\s*[+-]\s*(?:0x[0-9a-fA-F]+|\d+)\]",
                      f"[rip + {label}]", text)

    def replace_abs(text: str, label: str) -> str:
        return re.sub(r"\[\s*(?:0x[0-9a-fA-F]+|\d+)\s*\]",
                      f"[{label}]", text)

    def replace_imm(text: str, value: int, label: str) -> str:
        # Capstone prints immediates as 0x... or as a decimal literal.  Match
        # the value, masking to the address width used by the payload.
        def repl(match):
            literal_text = match.group(0)
            try:
                literal = (int(literal_text, 16) if literal_text.lower()
                           .startswith("0x") else int(literal_text, 10))
            except ValueError:
                return literal_text
            if literal == value or (literal & 0xFFFFFFFF) == (value & 0xFFFFFFFF):
                return label
            return literal_text
        return re.sub(r"0x[0-9a-fA-F]+|\b\d+\b", repl, text, count=1)

    def apply_fixup(text: str, insn, fixup: dict) -> str:
        kind = fixup.get("kind")
        section_index = int(fixup.get("section", 0))
        delta = int(fixup.get("delta", 0))
        if kind == "getpc_stub" or (kind == "getpc" and arch == "x86"
                                    and "callee" in fixup):
            return re.sub(r"0x[0-9a-fA-F]+|\b\d+\b",
                          f"DATA_STUB_{section_index}", text, count=1)
        label = _data_label(section_index, delta)
        if kind in ("rip", "getpc"):
            return replace_rip(text, label)
        if kind == "abs":
            return replace_abs(text, label)
        if kind == "imm":
            section = None
            # The fixup does not carry the final address; the caller passes
            # the original instruction text whose immediate is stale, so use
            # the data section address from the piece table when possible.
            for piece in pieces:
                if piece.index == section_index:
                    section = piece
                    break
            if section is None:
                return text
            value = data_start + section.offset + delta
            return replace_imm(text, value, label)
        return text

    def fallback_memory(text: str, insn) -> str:
        for operand in insn.operands:
            if operand.type != X86_OP_MEM:
                continue
            if operand.mem.base == X86_REG_RIP:
                target = insn.address + insn.size + operand.mem.disp
                label = _label_for_offset(pieces, target - data_start)
                if label:
                    return replace_rip(text, label)
                if target in addresses:
                    return replace_rip(text, _label("L", target))
            elif operand.mem.base == 0 and operand.mem.index == 0:
                target = operand.mem.disp
                label = _label_for_offset(pieces, target - data_start)
                if label:
                    return replace_abs(text, label)
        return text

    def format_instruction(insn) -> str:
        text = f"{insn.mnemonic} {insn.op_str}".strip()
        for fixup in fixup_by_source.get(insn.address, ()):
            text = apply_fixup(text, insn, fixup)
        if _is_direct_branch(insn):
            target = insn.operands[0].imm
            if 0 <= target < len(code):
                text = re.sub(r"0x[0-9a-fA-F]+|\b\d+\b",
                              _label("L", target), text, count=1)
        else:
            text = fallback_memory(text, insn)
        return text

    entries = []
    cursor = 0
    for insn in insns:
        if cursor < insn.address:
            gap = code[cursor:insn.address]
            entries.append(("gap", cursor, gap, None))
        entries.append(("insn", insn.address, bytes(insn.bytes), insn))
        cursor = insn.address + insn.size
    if cursor < len(code):
        entries.append(("gap", cursor, code[cursor:], None))

    lines: List[str] = ["_start:"]
    for kind, address, raw, insn in entries:
        if address in branch_targets:
            lines.append(f"L_{address:x}:")
        if address in ret_labels:
            lines.append(f"RET_{address:x}:")
        if kind == "gap":
            lines.append(f"    .byte {_fmt_bytes(raw)}  ; undecodable gap")
            continue
        text = format_instruction(insn)
        comment = comments.get(address)
        suffix = f"  ; {comment}" if comment else ""
        lines.append(f"    {text}{suffix}")

    source = "\n".join(lines)
    data_source = build_data_source(pieces, blob)
    return CanonicalPayload(arch=arch, code=code, blob=blob, source=source,
                            data_source=data_source, pieces=pieces,
                            labels=sorted(branch_targets),
                            ret_labels=sorted(ret_labels), comments=comments,
                            data_base=data_start)


def clean_llm_source(text: str, arch: str) -> str:
    """Extract the assembly block from a model response and normalise it."""
    if not text:
        raise LLMPayloadError("the model returned an empty response")
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")

    # Prefer a fenced block that contains the entry label.
    fenced = re.findall(r"```(?:asm|assembly|x86|x86asm|nasm|intel)?\s*\n(.*?)```",
                        text, flags=re.IGNORECASE | re.DOTALL)
    candidates = fenced if fenced else [text]
    chosen = None
    for candidate in candidates:
        if "_start:" in candidate:
            chosen = candidate
            break
    if chosen is None:
        chosen = max(candidates, key=len)

    drop = re.compile(
        r"^\s*(?:\.?(?:intel_syntax|att_syntax|text|section|globl|global|"
        r"code64|code32|model|data|bss|extern|type|size|org|align|default)\b|"
        r"(?:bits|use16|use32|use64|format|segment|section|global|extern)\b)",
        re.IGNORECASE)

    lines: List[str] = []
    for line in chosen.splitlines():
        stripped = line.strip()
        if drop.match(stripped):
            continue
        if stripped.startswith("```"):
            continue
        lines.append(line.rstrip())

    # Start at the entry label; prose before it is not assembly.
    start = next((index for index, line in enumerate(lines)
                  if line.strip().lower().startswith("_start:")), None)
    if start is None:
        lines.insert(0, "_start:")
    elif start:
        lines = lines[start:]
    # Keystone symbols are case-sensitive.  Normalise the labels that the
    # tool itself generated so a model that upper-cases them still assembles.
    source = "\n".join(lines).strip()
    source = re.sub(
        r"\b(L|RET|DATA_STUB|DATA)_([0-9A-Fa-f]+)\b",
        lambda match: f"{match.group(1)}_{match.group(2).lower()}", source)
    source = re.sub(r"(?im)^\s*_start\s*:", "_start:", source)
    if not source:
        raise LLMPayloadError("the model response contains no assembly")

    # Keystone abbreviations: `pushf` is 16-bit on x86, and the 32-bit
    # disassembler spells pushad/popad as pushal/popal.  Normalise both.
    def word_replace(pattern: str, replacement: str) -> None:
        nonlocal source
        source = re.sub(pattern, replacement, source)

    if arch == "x64":
        word_replace(r"\bpushf\b", "pushfq")
        word_replace(r"\bpopf\b", "popfq")
        word_replace(r"\bpushfd\b", "pushfq")
        word_replace(r"\bpopfd\b", "popfq")
    else:
        word_replace(r"\bpushf\b", "pushfd")
        word_replace(r"\bpopf\b", "popfd")
        word_replace(r"\bpushfq\b", "pushfd")
        word_replace(r"\bpopfq\b", "popfd")
        word_replace(r"\bpushad\b", "pushad")
        word_replace(r"\bpopad\b", "popad")
    return source


def _strip_assembly_comments(source: str) -> str:
    """Keystone treats ``;`` as part of the mnemonic, so comments go away."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r";[^\n]*", "", source)
    source = re.sub(r"(?://|#)[^\n]*", "", source)
    return source


def assemble(source: str, canonical: CanonicalPayload) -> AssembledPayload:
    """Assemble the model output plus the protected data blob."""
    cleaned = _strip_assembly_comments(
        clean_llm_source(source, canonical.arch))
    full = cleaned
    if canonical.data_source:
        full = cleaned.rstrip() + "\n" + _strip_assembly_comments(
            canonical.data_source) + "\n"
    ks = Ks(KS_ARCH_X86, _ks_mode(canonical.arch))
    try:
        encoding, _count = ks.asm(full, 0)
    except Exception as error:  # Keystone raises KsError
        raise LLMPayloadError(f"Keystone rejected the assembly: {error}") from error
    if not encoding:
        raise LLMPayloadError("Keystone produced no bytes")
    payload = bytes(encoding)
    if len(payload) < len(canonical.blob):
        raise LLMPayloadError(
            "assembled output is shorter than the data blob")
    code_len = len(payload) - len(canonical.blob)
    code = payload[:code_len]

    # The section bytes must be byte-identical (the 32-bit getpc stubs are
    # re-encoded and therefore checked separately).
    for piece in canonical.pieces:
        start = code_len + piece.offset
        end = start + piece.length
        if payload[start:end] != piece.data:
            raise LLMPayloadError(
                f"data section {piece.index} was corrupted by assembly")
    for piece in canonical.pieces:
        if piece.stub_offset is None:
            continue
        stub = payload[code_len + piece.stub_offset:
                       code_len + piece.stub_offset + 5]
        if len(stub) != 5 or stub[0] != 0xE8:
            raise LLMPayloadError(
                f"data stub for section {piece.index} is not a call")
    return AssembledPayload(payload=payload, code=code, code_len=code_len,
                            source=full)


def _normalise_mnemonic(insn) -> str:
    mnemonic = insn.mnemonic.lower()
    return mnemonic


def _normalise_operand_text(text: str) -> str:
    # Labels and numeric addresses change with the layout; keep the shape.
    text = re.sub(r"\b(?:L|RET)_[0-9a-f]+\b", "#", text)
    text = re.sub(r"\bDATA(?:_STUB)?_[0-9]+\b", "#", text)
    text = re.sub(r"0x[0-9a-fA-F]+", "#", text)
    text = re.sub(r"\b\d+\b", "#", text)
    return re.sub(r"\s+", " ", text).strip()


def _instruction_signature(insn) -> str:
    return f"{_normalise_mnemonic(insn)} {_normalise_operand_text(insn.op_str)}"


def _is_nop_like(insn) -> bool:
    mnemonic = insn.mnemonic.lower()
    if mnemonic in _NOP_MNEMONICS:
        return True
    # `mov r, r`, `lea r, [r + 0]`, `xchg r, r` are flag-neutral fillers.
    if mnemonic == "mov" and insn.op_str:
        parts = [part.strip() for part in insn.op_str.split(",")]
        return len(parts) == 2 and parts[0] == parts[1]
    if mnemonic == "xchg" and insn.op_str:
        parts = [part.strip() for part in insn.op_str.split(",")]
        return len(parts) == 2 and parts[0] == parts[1]
    if mnemonic == "lea" and insn.op_str:
        match = re.match(
            r"^([a-z0-9]+),\s*\[([a-z0-9]+)(?:\s*\+\s*(?:0x0|0))?\]$",
            insn.op_str)
        return bool(match and match.group(1) == match.group(2))
    return False


def _is_subsequence(needle: Sequence[str],
                    haystack: Sequence[str]) -> bool:
    iterator = iter(haystack)
    return all(item in iterator for item in needle)


def _missing_signatures(original: Sequence[str],
                        output: Sequence[str]) -> List[str]:
    matcher = difflib.SequenceMatcher(None, original, output, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    if matched >= len(original):
        return []
    missing = []
    cursor = 0
    for block in matcher.get_matching_blocks():
        for index in range(cursor, block.a):
            missing.append(original[index])
        cursor = block.a + block.size
    for index in range(cursor, len(original)):
        missing.append(original[index])
    return missing



def _referenced_data_offsets(insns, data_base: int, data_len: int,
                             arch: str):
    """Multiset of blob offsets referenced by a code stream."""
    from collections import Counter
    refs = Counter()
    end = data_base + data_len
    mask = 0xFFFFFFFF if arch == "x86" else 0xFFFFFFFFFFFFFFFF
    for insn in insns:
        for operand in insn.operands:
            if operand.type == X86_OP_MEM:
                if operand.mem.base == X86_REG_RIP:
                    target = insn.address + insn.size + operand.mem.disp
                elif operand.mem.base == 0 and operand.mem.index == 0:
                    target = operand.mem.disp
                else:
                    continue
                target &= mask
                if data_base <= target < end:
                    refs[target - data_base] += 1
            elif operand.type == X86_OP_IMM:
                value = operand.imm & mask
                if data_base <= value < end:
                    refs[value - data_base] += 1
        if _is_direct_branch(insn):
            target = insn.operands[0].imm & mask
            if data_base <= target < end:
                refs[target - data_base] += 1
    return refs


def validate(assembled: AssembledPayload, canonical: CanonicalPayload,
             technique: str = "eq",
             min_similarity: Optional[float] = None) -> ValidationReport:
    """Static checks on the assembled payload (no execution)."""
    report = ValidationReport(ok=True, code_len=assembled.code_len)
    cs = _disassembler(canonical.arch)
    insns = list(cs.disasm(assembled.code, 0))
    covered = sum(insn.size for insn in insns)
    report.instruction_count = len(insns)
    if covered != len(assembled.code):
        report.errors.append(
            f"output code is not fully disassembled: {covered}/{len(assembled.code)} bytes")
    starts = {insn.address for insn in insns}

    data_end = assembled.code_len + len(canonical.blob)
    stub_ranges = []
    for piece in canonical.pieces:
        if piece.stub_offset is not None:
            start = assembled.code_len + piece.stub_offset
            stub_ranges.append((start, start + 5))

    for insn in insns:
        if _is_direct_branch(insn):
            target = insn.operands[0].imm
            if 0 <= target < assembled.code_len and target not in starts:
                report.errors.append(
                    f"branch at {insn.address:#x} targets {target:#x}, "
                    "which is not an instruction boundary")
            if target < 0 or target >= data_end:
                report.warnings.append(
                    f"branch at {insn.address:#x} targets outside the payload: "
                    f"{target:#x}")
            if assembled.code_len <= target < data_end:
                in_stub = any(target == start for start, _end in stub_ranges)
                if not in_stub:
                    report.errors.append(
                        f"branch at {insn.address:#x} enters the data blob at "
                        f"{target:#x}; only DATA_STUB_* entries are executable")
        for operand in insn.operands:
            if operand.type != X86_OP_MEM:
                continue
            if operand.mem.base == X86_REG_RIP:
                target = insn.address + insn.size + operand.mem.disp
            elif operand.mem.base == 0 and operand.mem.index == 0:
                target = operand.mem.disp
            else:
                continue
            if 0 <= target < assembled.code_len:
                if target not in starts:
                    report.warnings.append(
                        f"memory reference at {insn.address:#x} points inside "
                        f"code at {target:#x} (not an instruction boundary)")
            elif assembled.code_len <= target < data_end:
                continue
            else:
                report.warnings.append(
                    f"memory reference at {insn.address:#x} points outside "
                    f"the payload: {target:#x}")

    # RET_* labels must stay immediately after their call.
    lines = [line.strip() for line in assembled.source.splitlines()
             if line.strip() and not line.strip().startswith(";")]
    for address in canonical.ret_labels:
        label = f"RET_{address:x}:"
        if not any(line == label for line in lines):
            report.errors.append(
                f"missing {label}; getpc return-address labels must be "
                "preserved")
    for index, line in enumerate(lines):
        match = re.match(r"^(RET_[0-9a-f]+):$", line)
        if not match:
            continue
        previous = lines[index - 1] if index else ""
        if not previous.lower().startswith("call"):
            report.errors.append(
                f"{match.group(1)} is not immediately after a call "
                f"(previous line: {previous!r})")

    original_insns = list(_disassembler(canonical.arch).disasm(
        canonical.code, 0))

    # Every data reference of the original must still be present in the
    # morphed stream.  A model that drops a `lea rcx, [rip + DATA_0]` would
    # otherwise silently change the payload's strings/arguments.
    if canonical.blob:
        original_refs = _referenced_data_offsets(
            original_insns, canonical.data_base, len(canonical.blob),
            canonical.arch)
        output_refs = _referenced_data_offsets(
            insns, assembled.code_len, len(canonical.blob), canonical.arch)
        missing_refs = original_refs - output_refs
        if missing_refs:
            details = ", ".join(
                f"DATA offset {offset:#x} x{count}"
                for offset, count in list(missing_refs.items())[:6])
            report.errors.append(
                "data references disappeared from the payload: " + details)

    def count_mnemonics(sequence, names):
        return sum(1 for insn in sequence if insn.mnemonic.lower() in names)

    ret_names = {"ret", "retf", "iret", "iretd", "iretq"}
    if count_mnemonics(insns, ret_names) != count_mnemonics(original_insns,
                                                           ret_names):
        report.errors.append(
            "the number of return instructions changed: "
            f"{count_mnemonics(original_insns, ret_names)} -> "
            f"{count_mnemonics(insns, ret_names)}")
    dangerous = {"int3", "ud2", "hlt", "int", "into", "syscall", "sysenter",
                 "cli", "sti", "in", "out", "wrmsr", "rdmsr", "lgdt", "lidt",
                 "lldt", "ltr", "invlpg", "invept", "invvpid"}
    for mnemonic in dangerous:
        if (count_mnemonics(insns, {mnemonic})
                > count_mnemonics(original_insns, {mnemonic})):
            report.errors.append(
                f"the morphed payload introduces `{mnemonic}`, which the "
                "original did not contain")

    # Structural similarity: compare the mnemonic/signature stream.  The
    # caller decides whether the threshold is appropriate for the technique.
    original = [insn for insn in original_insns]
    if technique == "nop":
        original = [insn for insn in original if not _is_nop_like(insn)]
        output = [insn for insn in insns if not _is_nop_like(insn)]
    else:
        output = insns
    original_signatures = [_instruction_signature(insn) for insn in original]
    output_signatures = [_instruction_signature(insn) for insn in output]
    if original_signatures:
        matcher = difflib.SequenceMatcher(
            None, original_signatures, output_signatures, autojunk=False)
        report.similarity = matcher.ratio()
    else:
        report.similarity = 1.0

    if technique in ("nop", "bcf") and original_signatures:
        missing = _missing_signatures(original_signatures, output_signatures)
        # bcf inserts whole blocks between the originals; nop must not change
        # the original stream at all.
        tolerance = 0 if technique == "nop" else 2
        if len(missing) > tolerance:
            report.errors.append(
                f"{len(missing)} original instruction(s) are missing or out "
                f"of order (allowed {tolerance}); first missing: "
                + "; ".join(missing[:4]))
        if len(insns) <= len(original_insns):
            report.errors.append(
                f"{technique} did not insert any instruction; the technique "
                "was not applied")
    elif technique == "eq" and original_signatures:
        # Equal substitution changes mnemonics, so a plain text similarity is
        # not meaningful.  Control-flow instructions, however, must survive:
        # dropping a call, a branch or a return is never a valid substitution.
        def is_control_flow(signature: str) -> bool:
            mnemonic = signature.split(" ", 1)[0]
            return (mnemonic in _BRANCH_MNEMONICS
                    or mnemonic in ("ret", "retf", "iret", "iretd", "iretq"))

        from collections import Counter
        original_cf = Counter(sig for sig in original_signatures
                              if is_control_flow(sig))
        output_cf = Counter(sig for sig in output_signatures
                            if is_control_flow(sig))
        missing_cf = original_cf - output_cf
        if sum(missing_cf.values()) > 1:
            report.errors.append(
                "control-flow instructions disappeared during equal-code "
                "substitution: "
                + "; ".join(list(missing_cf.elements())[:4]))
        # Every allowed substitution maps one instruction to one or two
        # instructions; the output can never have fewer non-control
        # instructions than the input.
        original_non_cf = sum(1 for sig in original_signatures
                              if not is_control_flow(sig))
        output_non_cf = sum(1 for sig in output_signatures
                            if not is_control_flow(sig))
        if output_non_cf < original_non_cf:
            report.errors.append(
                f"equal-code substitution removed {original_non_cf - output_non_cf} "
                "non-control instruction(s); transformations may only replace "
                "an instruction, not delete it")
        if original_signatures == output_signatures:
            report.warnings.append(
                "eq did not change any instruction; the technique may not "
                "have been applied")
    elif technique == "ibp" and original_signatures:
        from collections import Counter
        missing = Counter(original_signatures) - Counter(output_signatures)
        if sum(missing.values()):
            report.errors.append(
                f"{sum(missing.values())} original instruction(s) disappeared "
                "during block permutation")
        # IBP must actually reorder something.  If the original instruction
        # sequence is still a subsequence of the output, the model returned
        # the input order (possibly with a few extra bytes).
        if len(original_signatures) >= 4 and _is_subsequence(
                original_signatures, output_signatures):
            report.errors.append(
                "IBP did not permute blocks: the original instruction order "
                "is unchanged (the tool requires at least two non-entry "
                "blocks to be reordered)")
        original_jmps = sum(1 for sig in original_signatures
                            if sig.startswith("jmp "))
        output_jmps = sum(1 for sig in output_signatures
                          if sig.startswith("jmp "))
        if output_jmps <= original_jmps:
            report.warnings.append(
                "IBP output has no new unconditional jmp; check the "
                "fall-through block terminators")

    if min_similarity is not None and report.similarity < min_similarity:
        report.errors.append(
            f"structural similarity {report.similarity:.2f} is below "
            f"{min_similarity:.2f}: instructions were probably dropped or "
            "rewritten incorrectly")
    report.ok = not report.errors
    return report


def describe_difference(canonical: CanonicalPayload,
                        assembled: AssembledPayload) -> str:
    """A compact diff used as retry feedback for the model."""
    cs = _disassembler(canonical.arch)
    original = [_instruction_signature(insn)
                for insn in cs.disasm(canonical.code, 0)]
    output = [_instruction_signature(insn)
              for insn in cs.disasm(assembled.code, 0)]
    diff = list(difflib.unified_diff(original, output, fromfile="original",
                                     tofile="morphed", lineterm="", n=2))
    if len(diff) > 120:
        diff = diff[:120] + ["... diff truncated ..."]
    return "\n".join(diff)
