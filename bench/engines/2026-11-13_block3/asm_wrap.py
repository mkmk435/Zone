"""Assembly wrapping for Zone (x86-64 and x86).

The technique hides real instructions inside the immediate operand of a
benign ``mov reg, imm``.  The CPU is redirected to the first byte of the
immediate, while a linear/recursive disassembler keeps decoding the ``mov``
and never sees the hidden code.

Layout produced by this module (x86-64)::

    entry:  push reg                     ; save the scratch register
            lea  reg, [rip + disp]       ; address of the first immediate
            xchg reg, [rsp]              ; put it on the stack, restore reg
            ret                          ; jump there, no flag is touched

    +0x00:  mov regA, imm64              ; container, static view: benign
                   ^ entry (+2)          ; runtime: up to 6 bytes of real code
    +0x0a:  mov regB, imm64              ; next container
                   ^ entry (+2)
    ...

Each 8-byte immediate holds ``<up to 6 bytes of code> + EB <dist> + <junk>``.
The short jump skips the junk and the *opcode* of the next container, landing
exactly on its immediate, so execution chains through the payload while every
byte stays covered by a legal instruction in the static view.

x86 (32-bit) works the same way, with two differences forced by the ISA:

* the largest immediate available is 32 bits, so a container is
  ``mov r32, imm32`` (5 bytes) and only **4 bytes** of code fit;
* the two-byte glue cannot live inside the immediate without eating half of
  the payload, so it is placed right after it::

      B8 <4 bytes of code> EB 01        ; mov eax, imm32 ; jmp +1
      B9 <4 bytes of code> EB 01        ; entry is at the immediate

  Unused immediate bytes are padded with harmless instructions because, unlike
  the 64-bit layout, they are executed.

The 32-bit entry stub has no RIP-relative addressing: it computes the target
with the classic ``call/pop`` getpc plus a base-relative ``lea``, then jumps
through the stack without touching the flags::

    push reg            ; save
    call $+5            ; push the address of "pop"
    pop  reg            ; reg = address of "pop"
    lea  reg, [reg + d] ; target
    xchg reg, [esp]     ; stack slot -> target, reg -> original
    ret                 ; jump, stack restored

Instructions that do not fit (larger than the container capacity) or that must
keep a byte-exact local layout (the ``-ebi`` trampolines, ``loop``/``jcxz``)
are copied verbatim into "raw" blocks; control flow through them is still
glued with the same short jumps.

The module is deliberately independent from ``pobf.py``/``pobf86.py``: it
takes a list of :class:`WrapItem` and returns the rewritten bytes.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_MODE_64
from capstone import x86_const
from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KS_MODE_64


IMM64_SIZE = 8
GLUE_SIZE = 2
MASK32 = 0xFFFFFFFF

# `mov r64, imm64` opcodes: B8+rd with REX.W (and REX.B for r8-r15).
_MOV_IMM64 = {
    "rax": b"\x48\xb8", "rcx": b"\x48\xb9", "rdx": b"\x48\xba",
    "rbx": b"\x48\xbb", "rsp": b"\x48\xbc", "rbp": b"\x48\xbd",
    "rsi": b"\x48\xbe", "rdi": b"\x48\xbf",
    "r8": b"\x49\xb8", "r9": b"\x49\xb9", "r10": b"\x49\xba",
    "r11": b"\x49\xbb", "r12": b"\x49\xbc", "r13": b"\x49\xbd",
    "r14": b"\x49\xbe", "r15": b"\x49\xbf",
}

# `mov r32, imm32` opcodes: B8+rd, one byte.
_MOV_IMM32 = {
    "eax": b"\xb8", "ecx": b"\xb9", "edx": b"\xba", "ebx": b"\xbb",
    "esp": b"\xbc", "ebp": b"\xbd", "esi": b"\xbe", "edi": b"\xbf",
}

LOOP_FAMILY = {"loop", "loope", "loopne", "jcxz", "jecxz", "jrcxz"}

# Fillers. In 64-bit containers they are never executed (the glue jump skips
# them); in 32-bit containers the bytes before the glue are executed, so the
# 32-bit pool is restricted to flag-safe, side-effect-free instructions.
JUNK64 = {
    1: [b"\x90"],
    2: [b"\x66\x90", b"\x48\x90"],
    3: [b"\x0f\x1f\x00", b"\x48\x89\xc0", b"\x48\x89\xc9"],
    4: [b"\x0f\x1f\x40\x00", b"\x48\x8d\x24\x24", b"\x48\x8d\x40\x00"],
    5: [b"\x0f\x1f\x44\x00\x00", b"\x48\x8d\x64\x24\x00"],
    6: [b"\x66\x0f\x1f\x44\x00\x00"],
}

JUNK32 = {
    1: [b"\x90"],
    2: [b"\x66\x90", b"\x89\xc0", b"\x8b\xc0"],
    3: [b"\x0f\x1f\x00", b"\x8d\x40\x00", b"\x89\xc9"],
    4: [b"\x0f\x1f\x40\x00", b"\x8d\x64\x24\x00"],
}


class WrapError(RuntimeError):
    """Raised when the payload cannot be wrapped safely."""


@dataclass(frozen=True)
class _Arch:
    bits: int
    regs: tuple
    opcodes: dict
    opcode_len: int
    imm_size: int
    glue_inside_imm: bool
    junk: dict
    capacity_choices: tuple

    @property
    def capacity(self) -> int:
        return self.imm_size - (GLUE_SIZE if self.glue_inside_imm else 0)

    @property
    def container_size(self) -> int:
        return (self.opcode_len + self.imm_size
                + (0 if self.glue_inside_imm else GLUE_SIZE))


ARCH_64 = _Arch(
    bits=64,
    # rsp/rbp are never wrapper registers: the opcode is never executed by
    # design, but a layout bug that let execution fall into `mov rsp, imm64`
    # would destroy the stack frame.
    regs=tuple(reg for reg in _MOV_IMM64 if reg not in ("rsp", "rbp")),
    opcodes=_MOV_IMM64, opcode_len=2, imm_size=IMM64_SIZE,
    glue_inside_imm=True, junk=JUNK64,
    capacity_choices=(6, 6, 6, 5, 4, 3),
)

ARCH_32 = _Arch(
    bits=32,
    regs=("eax", "ecx", "edx", "ebx", "esi", "edi"),
    opcodes=_MOV_IMM32, opcode_len=1, imm_size=4,
    glue_inside_imm=False, junk=JUNK32,
    capacity_choices=(4, 4, 4, 3, 2),
)

USABLE = ARCH_64.capacity          # kept for callers that import it


@dataclass
class WrapItem:
    """One instruction of the final linear stream.

    ``key``        caller identifier, returned through ``new_address``.
    ``addr``       address in the current (pre-wrap) layout.
    ``data``       instruction bytes; branch encodings may be normalised here.
    ``forced_raw`` keep the bytes verbatim in a raw block (-ebi trampoline).
    ``data_fixup`` the instruction gets its displacement rewritten later by
                   Zone's finalize_data_refs(); do not touch it here.
    """

    key: object
    addr: int
    data: bytes
    forced_raw: bool = False
    data_fixup: bool = False


@dataclass
class _Reloc:
    kind: str          # "rel32" | "disp32" | "rel8"
    offset: int        # field offset inside the instruction
    target: int        # absolute target in the pre-wrap layout
    size: int = 4


@dataclass
class _Block:
    kind: str                                # container | ghost | raw | junk
    items: List[WrapItem] = field(default_factory=list)
    opcode: bytes = b""
    junk: bytes = b""
    start: int = 0
    size: int = 0
    entry: int = 0
    glue_offset: int = 0
    distance: int = 0
    used: int = 0
    capacity: int = 6


class AssemblyWrapping:
    """Chunk, wrap and relocate an x86-64 or x86 instruction stream."""

    def __init__(self, seed: Optional[int] = None,
                 ghost_probability: float = 0.20,
                 junk_probability: float = 0.15,
                 verify: bool = True,
                 bits: int = 64):
        if bits not in (32, 64):
            raise WrapError(f"unsupported bitness: {bits}")
        self.bits = bits
        self.arch = ARCH_64 if bits == 64 else ARCH_32

        self.rng = random.Random(seed)
        self.ghost_probability = ghost_probability
        self.junk_probability = junk_probability
        self.verify = verify

        mode = CS_MODE_64 if bits == 64 else CS_MODE_32
        self.cs = Cs(CS_ARCH_X86, mode)
        self.cs.detail = True
        self.ks = Ks(KS_ARCH_X86, KS_MODE_64 if bits == 64 else KS_MODE_32)

        self.items: List[WrapItem] = []
        self.blocks: List[_Block] = []
        self.relocs: Dict[object, List[_Reloc]] = {}
        self.new_address: Dict[object, int] = {}
        self.targets: Dict[object, int] = {}
        self.warnings: List[str] = []
        self.code_length = 0

        self.stats = {"containers": 0, "ghosts": 0, "raw_items": 0,
                      "wrapped_items": 0, "junk_blocks": 0}

        self._insn: Dict[object, object] = {}
        self._by_addr: Dict[int, WrapItem] = {}
        self._end = 0

        self._build_entry()

    # ------------------------------------------------------------------ #
    # entry stub
    # ------------------------------------------------------------------ #
    def _build_entry(self) -> None:
        """Build the position-independent entry stub.

        The target address of the stub is computed at runtime; the only
        register touched is a scratch one, restored through the stack, and no
        flag is modified (push/call/pop/lea/xchg/ret are all flag-safe).
        """
        self.entry_register = self.rng.choice(self.arch.regs)
        reg = self.entry_register

        if self.bits == 64:
            text = (f"push {reg}\n"
                    f"lea {reg}, [rip + 0]\n"
                    f"xchg {reg}, [rsp]\n"
                    "ret")
            encoding, _ = self.ks.asm(text, 0)
            entry = bytes(encoding)
            insns = list(self.cs.disasm(entry, 0))
            lea = next((i for i in insns if i.mnemonic == "lea"), None)
            if lea is None or len(insns) != 4:
                raise WrapError("cannot build the 64-bit entry stub")
            self.entry_base = lea.address + lea.size
        else:
            # keystone optimises `call $+5; pop reg` away when assembled as a
            # single string, so the stub is assembled piece by piece.
            push, _ = self.ks.asm(f"push {reg}", 0)
            call_next = b"\xE8\x00\x00\x00\x00"
            pop, _ = self.ks.asm(f"pop {reg}", 0)
            # a non-zero displacement forces the 6-byte `lea reg, [reg+disp32]`
            lea, _ = self.ks.asm(f"lea {reg}, [{reg} + 0x11223344]", 0)
            xchg, _ = self.ks.asm(f"xchg {reg}, [esp]", 0)
            ret, _ = self.ks.asm("ret", 0)
            entry = bytes(push) + call_next + bytes(pop) + bytes(lea) \
                + bytes(xchg) + bytes(ret)
            insns = list(self.cs.disasm(entry, 0))
            lea_insn = next((i for i in insns if i.mnemonic == "lea"), None)
            pop_insn = next((i for i in insns if i.mnemonic == "pop"), None)
            if lea_insn is None or pop_insn is None or len(insns) != 6:
                raise WrapError("cannot build the 32-bit entry stub")
            lea = lea_insn
            # `call $+5` pushes the address of the following `pop`, and the
            # lea is base-relative on that value.
            self.entry_base = pop_insn.address

        self.entry = entry
        self.entry_lea_offset = lea.address
        self.entry_lea_size = lea.size
        self.entry_lea_disp_offset = lea.disp_offset

    # ------------------------------------------------------------------ #
    # plan
    # ------------------------------------------------------------------ #
    def plan(self, items: List[WrapItem]) -> int:
        """Normalise, chunk and place the payload. Returns the code length."""
        if not items:
            raise WrapError("nothing to wrap")
        self.items = list(items)
        starts = [item.addr for item in self.items]
        if starts != sorted(starts):
            for index in range(1, len(starts)):
                if starts[index] < starts[index - 1]:
                    bad = self.items[index]
                    raise WrapError(
                        f"items are not sorted by address: instruction "
                        f"{index} is at {bad.addr:#x} after "
                        f"{starts[index - 1]:#x} (stale layout from the "
                        "morphing pass)")
            raise WrapError("items are not sorted by address")
        for prev, cur in zip(self.items, self.items[1:]):
            if prev.addr + len(prev.data) != cur.addr:
                raise WrapError(
                    f"gap in the instruction stream between {prev.addr:#x} "
                    f"and {cur.addr:#x}")
        self._by_addr = {item.addr: item for item in self.items}

        self._normalise_branches()
        self._scan_relocations()
        self._compute_raw_ranges()
        self._build_blocks()
        self._assign_addresses()
        return self.code_length

    def _disasm_one(self, data: bytes, address: int):
        return next(self.cs.disasm(bytes(data), address, count=1), None)

    def _normalise_branches(self) -> None:
        """Promote short branches to their near forms.

        Fixing the encoding up front means instruction sizes never change, so
        the layout is computed once and every displacement is patched at the
        end.  A branch that kept its ``rel8`` form could otherwise flip size
        between iterations and make the layout oscillate.
        """
        for item in self.items:
            insn = self._disasm_one(item.data, item.addr)
            if insn is None or insn.size != len(item.data):
                raise WrapError(
                    f"cannot decode the instruction at {item.addr:#x} "
                    f"({item.data.hex()}); inline data must be extracted "
                    "before wrapping")
            self._insn[item.key] = insn

            if not self._has_immediate_branch(insn):
                continue

            target = insn.operands[0].imm
            self.targets[item.key] = target
            code = bytes(item.data)
            # the opcode sits right before the encoded target; segment and
            # operand-size prefixes (65/66/67) may precede it, and a 66 prefix
            # also turns rel32 into rel16, so the whole instruction is rebuilt
            # in its canonical near form instead of editing the field in place
            opcode_index = max(insn.imm_offset - 1, 0)
            opcode = code[opcode_index]

            if opcode in (0xE0, 0xE1, 0xE2, 0xE3):
                # loop/jcxz/jrcxz: no near form exists, keep the rel8 field
                continue

            canonical = (len(code) == 5 and code[0] in (0xE9, 0xE8)) \
                or (len(code) == 6 and code[0] == 0x0F
                    and 0x80 <= code[1] <= 0x8F)
            if not canonical:
                if opcode == 0xE9:
                    item.data = b"\xE9" + b"\x00\x00\x00\x00"
                elif opcode == 0xE8:
                    item.data = b"\xE8" + b"\x00\x00\x00\x00"
                elif opcode == 0xEB:
                    item.data = b"\xE9" + b"\x00\x00\x00\x00"
                elif 0x70 <= opcode <= 0x7F:
                    item.data = (b"\x0F" + bytes([opcode + 0x10])
                                 + b"\x00\x00\x00\x00")
                elif (0x80 <= opcode <= 0x8F and opcode_index > 0
                      and code[opcode_index - 1] == 0x0F):
                    # near jcc, possibly with an operand-size prefix
                    item.data = (b"\x0F" + bytes([opcode])
                                 + b"\x00\x00\x00\x00")
                else:
                    raise WrapError(
                        f"unsupported branch encoding at {item.addr:#x}: "
                        f"{insn.mnemonic} {insn.op_str} ({code.hex()})")
                self._insn[item.key] = self._disasm_one(item.data, item.addr)

    @staticmethod
    def _has_immediate_branch(insn) -> bool:
        if not insn.operands:
            return False
        if insn.operands[0].type != x86_const.X86_OP_IMM:
            return False
        try:
            is_branch = (insn.group(x86_const.X86_GRP_JUMP)
                         or insn.group(x86_const.X86_GRP_CALL)
                         or insn.mnemonic in LOOP_FAMILY)
        except Exception:
            return False
        return bool(is_branch)

    def _scan_relocations(self) -> None:
        """Record every field that must be rewritten after the move."""
        for item in self.items:
            if item.data_fixup:
                # Zone's finalize_data_refs() rewrites this instruction
                # entirely (getpc call/jmp, lea, absolute reference): touching
                # its operands here would undo that rewrite.
                continue

            insn = self._insn[item.key]
            relocs: List[_Reloc] = []

            if self._has_immediate_branch(insn):
                target = self.targets.get(item.key, insn.operands[0].imm)
                # the width of the encoded field: 1 byte for rel8 branches
                # (including prefixed ones), 4 for the near forms
                field = insn.size - insn.imm_offset
                if field == 1:
                    # loop/jcxz/jrcxz: the only branches that keep rel8
                    relocs.append(_Reloc("rel8", insn.imm_offset, target, 1))
                else:
                    relocs.append(_Reloc("rel32", insn.imm_offset, target, 4))

            if self.bits == 64:
                for operand in insn.operands:
                    if (operand.type == x86_const.X86_OP_MEM
                            and operand.mem.base == x86_const.X86_REG_RIP):
                        target = (item.addr + insn.size + operand.mem.disp) \
                            & ((1 << 64) - 1)
                        relocs.append(
                            _Reloc("disp32", insn.disp_offset, target, 4))
                        break

            if relocs:
                self.relocs[item.key] = relocs

    # ------------------------------------------------------------------ #
    # layout
    # ------------------------------------------------------------------ #
    def _compute_raw_ranges(self) -> None:
        """Keep every rel8 branch contiguous with its target.

        ``loop``/``jcxz``/``jrcxz`` cannot be promoted to a near form, so the
        whole range between the branch and its target is copied verbatim: the
        byte distance is then identical to the original one and the branch
        keeps working whatever the wrapper does around it.
        """
        self.raw_mask = [False] * len(self.items)
        index_by_key = {item.key: index
                        for index, item in enumerate(self.items)}
        for key, relocs in self.relocs.items():
            for reloc in relocs:
                if reloc.kind != "rel8":
                    continue
                start = index_by_key[key]
                end = self._owner_index(reloc.target)
                if end is None:
                    raise WrapError(
                        f"rel8 branch at {self.items[start].addr:#x} targets "
                        f"{reloc.target:#x}, which is outside the payload")
                for index in range(min(start, end), max(start, end) + 1):
                    self.raw_mask[index] = True

    def _owner_index(self, address: int) -> Optional[int]:
        """Index of the item that contains `address`, if any."""
        item = self._by_addr.get(address)
        if item is not None:
            for index, candidate in enumerate(self.items):
                if candidate is item:
                    return index
            return None
        starts = self._starts()
        index = bisect_right(starts, address) - 1
        if index >= 0 and address < self.items[index].addr + len(
                self.items[index].data):
            return index
        return None

    def _build_blocks(self) -> None:
        blocks: List[_Block] = []
        current: Optional[_Block] = None
        raw_run = False

        for index, item in enumerate(self.items):
            needs_raw = (item.forced_raw
                         or len(item.data) > self.arch.capacity
                         or self.raw_mask[index])
            if needs_raw:
                consecutive = (current is not None and raw_run
                               and current.kind == "raw"
                               and current.items[-1].addr
                               + len(current.items[-1].data) == item.addr)
                if consecutive:
                    current.items.append(item)
                    current.size += len(item.data)
                else:
                    current = _Block("raw", [item],
                                     size=len(item.data) + GLUE_SIZE)
                    blocks.append(current)
                raw_run = True
                continue

            raw_run = False
            if (current is not None and current.kind == "container"
                    and current.used + len(item.data) <= current.capacity):
                current.items.append(item)
                current.used += len(item.data)
                continue

            capacity = self._pick_capacity(len(item.data))
            current = _Block(
                "container", [item],
                opcode=self.arch.opcodes[self.rng.choice(self.arch.regs)],
                size=self.arch.container_size, used=len(item.data),
                capacity=capacity)
            blocks.append(current)

        # Decoys between blocks: a ghost container (a wrapper whose immediate
        # is just a jump, so it never executes anything) or plain junk bytes
        # that the previous glue jump skips over.
        decorated: List[_Block] = []
        for index, block in enumerate(blocks):
            if index > 0 and self.rng.random() < (
                    self.ghost_probability + self.junk_probability):
                if self.rng.random() < 0.6:
                    decorated.append(_Block(
                        "ghost",
                        opcode=self.arch.opcodes[
                            self.rng.choice(self.arch.regs)],
                        size=self.arch.container_size))
                else:
                    size = self.rng.randint(1, 5)
                    decorated.append(_Block("junk", size=size,
                                            junk=self._junk(size)))
            decorated.append(block)

        self.blocks = decorated
        for block in self.blocks:
            if block.kind == "container":
                self.stats["containers"] += 1
                self.stats["wrapped_items"] += len(block.items)
            elif block.kind == "ghost":
                self.stats["ghosts"] += 1
            elif block.kind == "raw":
                self.stats["raw_items"] += len(block.items)
            else:
                self.stats["junk_blocks"] += 1

    def _pick_capacity(self, first_size: int) -> int:
        capacity = self.rng.choice(self.arch.capacity_choices)
        return max(capacity, first_size)

    def _assign_addresses(self) -> None:
        arch = self.arch
        position = len(self.entry)
        for block in self.blocks:
            block.start = position
            position += block.size
        self.code_length = position

        entries = [block.start + (arch.opcode_len
                                  if block.kind in ("container", "ghost")
                                  else 0)
                   for block in self.blocks]
        for index, block in enumerate(self.blocks):
            block.entry = entries[index]
            if block.kind == "container":
                block.glue_offset = (
                    arch.opcode_len + block.used if arch.glue_inside_imm
                    else arch.opcode_len + arch.imm_size)
            elif block.kind == "ghost":
                block.glue_offset = arch.opcode_len
            elif block.kind == "raw":
                block.glue_offset = block.size - GLUE_SIZE
            else:
                block.glue_offset = -1

            following = index + 1
            while (following < len(self.blocks)
                   and self.blocks[following].kind == "junk"):
                following += 1
            block.next_entry = (entries[following]
                                if following < len(self.blocks)
                                else self.code_length)

            if block.glue_offset >= 0:
                glue_addr = block.start + block.glue_offset
                block.distance = block.next_entry - (glue_addr + GLUE_SIZE)
                if not -128 <= block.distance <= 127:
                    raise WrapError(
                        f"glue jump out of range: {block.distance}")

        for block in self.blocks:
            if block.kind == "container":
                offset = block.start + arch.opcode_len
                for item in block.items:
                    self.new_address[item.key] = offset
                    offset += len(item.data)
            elif block.kind == "raw":
                offset = block.start
                for item in block.items:
                    self.new_address[item.key] = offset
                    offset += len(item.data)

        self._end = self.items[-1].addr + len(self.items[-1].data)

    # ------------------------------------------------------------------ #
    # render
    # ------------------------------------------------------------------ #
    def render(self, get_bytes) -> bytes:
        """Emit the wrapped payload.

        ``get_bytes(key)`` must return the final bytes of an item (after any
        later fixup), with the size planned here.
        """
        arch = self.arch
        buffer = bytearray(self.code_length)

        # entry stub: patch the displacement of the lea
        buffer[0:len(self.entry)] = self.entry
        first_entry = self.blocks[0].entry if self.blocks else self.code_length
        displacement = first_entry - self.entry_base
        field = self.entry_lea_offset + self.entry_lea_disp_offset
        buffer[field:field + 4] = (displacement & MASK32).to_bytes(4, "little")

        for block in self.blocks:
            if block.kind == "container":
                self._render_container(buffer, block, get_bytes)
            elif block.kind == "ghost":
                buffer[block.start:block.start + arch.opcode_len] = block.opcode
                glue = block.start + arch.opcode_len
                buffer[glue] = 0xEB
                buffer[glue + 1] = block.distance & 0xFF
                fill = glue + GLUE_SIZE
                buffer[fill:block.start + block.size] = self._junk(
                    block.start + block.size - fill)
            elif block.kind == "raw":
                self._render_raw(buffer, block, get_bytes)
            elif block.kind == "junk":
                buffer[block.start:block.start + block.size] = block.junk

        self._patch_relocations(buffer)
        if self.verify:
            self._verify(buffer, get_bytes)
        return bytes(buffer)

    def _render_container(self, buffer: bytearray, block: _Block,
                          get_bytes) -> None:
        arch = self.arch
        buffer[block.start:block.start + arch.opcode_len] = block.opcode
        position = block.start + arch.opcode_len
        for item in block.items:
            data = bytes(get_bytes(item.key))
            if len(data) != len(item.data):
                raise WrapError(
                    f"size changed while wrapping the instruction at "
                    f"{item.addr:#x}: {len(item.data)} -> {len(data)}")
            buffer[position:position + len(data)] = data
            position += len(data)

        if arch.glue_inside_imm:
            glue = block.start + block.glue_offset
        else:
            # the bytes between the code and the glue are executed, so they
            # must be harmless instructions (they also hide the chunk size)
            padding = (block.start + arch.opcode_len + arch.imm_size
                       - position)
            if padding:
                buffer[position:position + padding] = self._exec_padding(
                    padding)
            glue = block.start + block.glue_offset

        buffer[glue] = 0xEB
        buffer[glue + 1] = block.distance & 0xFF
        fill = glue + GLUE_SIZE
        buffer[fill:block.start + block.size] = self._junk(
            block.start + block.size - fill)

    def _render_raw(self, buffer: bytearray, block: _Block, get_bytes) -> None:
        position = block.start
        for item in block.items:
            data = bytes(get_bytes(item.key))
            if len(data) != len(item.data):
                raise WrapError(
                    f"size changed while wrapping the instruction at "
                    f"{item.addr:#x}")
            buffer[position:position + len(data)] = data
            position += len(data)
        glue = block.start + block.glue_offset
        buffer[glue] = 0xEB
        buffer[glue + 1] = block.distance & 0xFF

    def _patch_relocations(self, buffer: bytearray) -> None:
        for item in self.items:
            base = self.new_address[item.key]
            instruction_end = base + len(item.data)
            for reloc in self.relocs.get(item.key, []):
                target = self._remap(reloc.target)
                relative = target - instruction_end
                field = base + reloc.offset
                if reloc.kind in ("rel32", "disp32"):
                    buffer[field:field + 4] = (relative & MASK32).to_bytes(
                        4, "little")
                elif reloc.kind == "rel8":
                    if not -128 <= relative <= 127:
                        raise WrapError(
                            f"short branch at {item.addr:#x} moved out of "
                            f"range ({relative})")
                    buffer[field] = relative & 0xFF

    def _remap(self, target: int) -> int:
        """Translate a pre-wrap address into the wrapped layout."""
        item = self._by_addr.get(target)
        if item is not None:
            return self.new_address[item.key]

        starts = self._starts()
        index = bisect_right(starts, target) - 1
        if index >= 0:
            owner = self.items[index]
            if target < owner.addr + len(owner.data):
                return (self.new_address[owner.key]
                        + (target - owner.addr))

        if target == self._end:
            return self.code_length
        return target

    def _starts(self) -> List[int]:
        if not hasattr(self, "_start_cache"):
            self._start_cache = [item.addr for item in self.items]
        return self._start_cache

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _junk(self, size: int) -> bytes:
        out = b""
        while len(out) < size:
            remaining = size - len(out)
            usage = min(remaining, self.rng.choice([1, 2, 3, 4, 5]))
            while usage not in self.arch.junk:
                usage -= 1
            out += self.rng.choice(self.arch.junk[usage])
        return out

    def _exec_padding(self, size: int) -> bytes:
        """Exactly `size` bytes of harmless, executable instructions."""
        out = b""
        while len(out) < size:
            remaining = size - len(out)
            usage = min(remaining, self.rng.choice([1, 2, 3, 4]))
            while usage not in self.arch.junk:
                usage -= 1
            out += self.rng.choice(self.arch.junk[usage])
        return out

    def _verify(self, buffer: bytes, get_bytes) -> None:
        """Decode every hidden instruction in place and check the relocation."""
        for item in self.items:
            base = self.new_address[item.key]
            raw = bytes(buffer[base:base + len(item.data)])
            got = self._disasm_one(raw, base)
            expected = self._insn[item.key]
            if item.data_fixup:
                # the data layer rewrites this instruction (a getpc call
                # becomes a jmp to the appended stub): only the size is
                # guaranteed, the mnemonic is expected to change
                if got is None or got.size != len(item.data):
                    raise WrapError(
                        f"data-fixup instruction at {base:#x} does not "
                        "decode to its planned size")
                continue
            if got is None or got.mnemonic != expected.mnemonic:
                raise WrapError(
                    f"verification failed at {base:#x}: expected "
                    f"{expected.mnemonic}, got "
                    f"{got.mnemonic if got else 'nothing'}")
            for reloc in self.relocs.get(item.key, []):
                target = self._remap(reloc.target)
                if reloc.kind in ("rel32", "rel8"):
                    if got.operands[0].imm != target:
                        raise WrapError(
                            f"branch target mismatch at {base:#x} "
                            f"(source {item.addr:#x}, {got.mnemonic} "
                            f"{got.op_str}, bytes {raw.hex()}): "
                            f"{got.operands[0].imm:#x} != {target:#x} "
                            f"(planned target {reloc.target:#x})")
                elif reloc.kind == "disp32":
                    operand = next(
                        (op for op in got.operands
                         if op.type == x86_const.X86_OP_MEM
                         and op.mem.base == x86_const.X86_REG_RIP), None)
                    if operand is None:
                        raise WrapError(
                            f"RIP operand disappeared at {base:#x}")
                    actual = base + got.size + operand.mem.disp
                    if actual != target:
                        raise WrapError(
                            f"RIP target mismatch at {base:#x}: "
                            f"{actual:#x} != {target:#x}")

    def source_length(self) -> int:
        return sum(len(item.data) for item in self.items)

    def describe(self) -> str:
        return (f"[wrap] {self.stats['wrapped_items']} instruction(s) hidden in "
                f"{self.stats['containers']} container(s), "
                f"{self.stats['raw_items']} raw, "
                f"{self.stats['ghosts']} ghost, "
                f"{self.stats['junk_blocks']} junk block(s): "
                f"{self.source_length()} -> {self.code_length} bytes")
