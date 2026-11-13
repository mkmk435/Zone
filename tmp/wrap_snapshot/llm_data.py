"""LLM-based data classification, an alternative to the symbolic ``-xd``.

The model receives:

* a hex dump with offsets and ASCII,
* a linear disassembly (heuristic: strings may be decoded as instructions),
* candidate printable runs (also heuristic),

and returns JSON data ranges.  The tool then uses the existing xref scanner
and ``Zone.extract_data()`` machinery to move those ranges and rewrite every
reference.  The model only classifies; it never writes or relocates code.

This keeps the risky part deterministic: the model says *what* is data, the
existing engine decides *whether and how* it can be moved.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional, Sequence, Tuple

from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_MODE_64

import llm_technique as engine
from llm_stats import APICall, AttemptRecord, RunStats

MAX_PAYLOAD = 65536
MAX_INSTRUCTIONS = 6000
MAX_SECTIONS = 256


class DataError(engine.LLMError):
    """A classification answer could not be turned into a safe extraction."""


DATA_EXAMPLES = (r"""
EXAMPLE 1 (x86-64 string referenced by LEA):
hex:
00000000  48 8d 35 06 00 00 00 b8 01 00 00 00 c3 68 65 6c  |H.5..........hel|
00000010  6c 6f 00                                          |lo.|
disassembly:
00000000  48 8d 35 06 00 00 00   lea rsi, [rip + 6]
00000007  b8 01 00 00 00         mov eax, 1
0000000c  c3                     ret
0000000d  68 65 6c 6c 6f 00      push 0x6c6c6568   (string misdecoded as code)
output:
{"sections":[{"offset":13,"length":6,"kind":"ascii","text":"hello"}]}
""", r"""
EXAMPLE 2 (x86-64 table referenced by RIP-relative MOV):
hex:
00000000  8b 05 05 00 00 00 c3 90 90 90 90 01 00 00 00 02  |................|
00000010  00 00 00                                          |...|
disassembly:
00000000  8b 05 05 00 00 00      mov eax, dword ptr [rip + 5]
00000006  c3                     ret
00000007  90                     nop
00000008  90                     nop
00000009  90                     nop
0000000a  90                     nop
0000000b  01 00                  add dword ptr [rax], eax  (table misdecoded as code)
0000000d  00 00                  add byte ptr [rax], al
0000000f  02 00                  add al, byte ptr [rax]
00000011  00 00                  add byte ptr [rax], al
output:
{"sections":[{"offset":11,"length":8,"kind":"table"}]}
""")


def _mode(arch: str) -> int:
    if arch == "x64":
        return CS_MODE_64
    if arch == "x86":
        return CS_MODE_32
    raise engine.LLMConfigError(f"unsupported architecture: {arch}")


def _hexdump(raw: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(raw), width):
        chunk = raw[offset:offset + width]
        hex_part = " ".join(f"{byte:02x}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte < 127 else "."
                             for byte in chunk)
        lines.append(f"{offset:08x}  {hex_part:<{width * 3 - 1}}  |{ascii_part}|")
    return "\n".join(lines)


def _disassembly(raw: bytes, arch: str) -> str:
    cs = Cs(CS_ARCH_X86, _mode(arch))
    cs.skipdata = True
    lines = []
    cursor = 0
    count = 0
    for insn in cs.disasm(raw, 0):
        if insn.address > cursor:
            lines.append(f"{cursor:08x}  {raw[cursor:insn.address].hex(' '):<24} "
                         ".byte (gap)")
        lines.append(f"{insn.address:08x}  {insn.bytes.hex(' '):<24} "
                     f"{insn.mnemonic} {insn.op_str}".rstrip())
        cursor = insn.address + insn.size
        count += 1
        if count > MAX_INSTRUCTIONS:
            lines.append("... disassembly truncated; payload too large for "
                         "this mode ...")
            break
    if cursor < len(raw) and count <= MAX_INSTRUCTIONS:
        lines.append(f"{cursor:08x}  {raw[cursor:].hex(' '):<24} .byte (tail)")
    return "\n".join(lines)


def _printable_candidates(raw: bytes) -> str:
    lines = []
    for match in re.finditer(rb"[\x20-\x7e]{4,}", raw):
        text = match.group().decode("ascii")
        lines.append(f"offset {match.start()} length {len(text)} ascii "
                     f"{text!r}")
        if len(lines) >= 200:
            lines.append("... more printable runs omitted ...")
            break
    for match in re.finditer(rb"(?:[\x20-\x7e]\x00){4,}", raw):
        text = match.group().decode("utf-16le", "replace")
        lines.append(f"offset {match.start()} length {len(match.group())} "
                     f"utf16le {text!r}")
        if len(lines) >= 200:
            lines.append("... more printable runs omitted ...")
            break
    return "\n".join(lines) if lines else "(none)"


SYSTEM_PROMPT = """\
You are a senior reverse engineer. You classify data ranges inside raw x86 and
x86-64 payloads used in authorized security research. The caller will locate
the code references and move the ranges; you only decide which byte ranges are
data.

Return exactly one JSON object and nothing else. Do not return assembly.
"""


def build_data_prompt(raw: bytes, arch: str, shots: int = 1) -> str:
    if len(raw) > MAX_PAYLOAD:
        raise engine.LLMConfigError(
            f"payload is {len(raw)} bytes; LLM data classification is limited "
            f"to {MAX_PAYLOAD} bytes — use the symbolic -xd instead")
    arch_name = "x86-64 (64-bit)" if arch == "x64" else "x86 (32-bit)"
    examples = DATA_EXAMPLES[:max(0, shots)]
    lines = [
        f"ARCHITECTURE: {arch_name}",
        f"PAYLOAD SIZE: {len(raw)} bytes",
        "",
        "TASK",
        "Identify every DATA range in the payload: strings, UTF-16 strings,",
        "lookup tables, jump tables, embedded structures, and inline getpc",
        "data. Do not include executable code. If the payload is all code,",
        "return an empty sections list.",
        "",
        "RULES",
        "* Offsets and lengths are byte offsets from the start of the payload.",
        "* A section must be non-overlapping with the others.",
        "* A C string includes its NUL terminator.",
        "* A table includes complete entries; do not cut an entry in half.",
        "* The linear disassembly is heuristic. Strings and tables are often",
        "  decoded as instructions; use the hex/ASCII view to overrule it.",
        "* A section without any code reference will be dropped by the tool.",
        "* If you are unsure, omit the range rather than classifying code.",
        "",
        "OUTPUT (JSON only)",
        '{"sections":[{"offset":13,"length":6,"kind":"ascii","text":"hello"}]}',
        "kind is one of: ascii, utf16le, table, struct, blob, unknown.",
        "",
    ]
    if examples:
        lines.append(f"WORKED EXAMPLE{'S' if len(examples) > 1 else ''} "
                     "(illustrative; do not copy the example offsets):")
        for index, example in enumerate(examples, 1):
            lines.append(f"--- example {index} ---")
            lines.append(example.strip())
            lines.append("")
    else:
        lines.append("No worked example is provided.")
        lines.append("")
    lines.extend([
        "HEX DUMP",
        _hexdump(raw),
        "",
        "LINEAR DISASSEMBLY (heuristic)",
        _disassembly(raw, arch),
        "",
        "CANDIDATE PRINTABLE RUNS (heuristic)",
        _printable_candidates(raw),
        "",
        "Return the JSON object now. No prose, no markdown except an optional",
        "```json fence.",
    ])
    return "\n".join(lines)


def build_data_messages(raw: bytes, arch: str, shots: int = 1) -> List[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_data_prompt(raw, arch, shots=shots)},
    ]


def _as_int(value) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not an offset")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text, 10)
    raise ValueError(f"not an integer: {value!r}")


def _extract_json(text: str) -> dict:
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text,
                        flags=re.IGNORECASE | re.DOTALL)
    candidates = fenced + [text]
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start < 0 or end <= start:
                continue
            try:
                value = json.loads(candidate[start:end + 1])
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict):
            if "sections" in value or "data" in value or "ranges" in value:
                return value
        elif isinstance(value, list):
            return {"sections": value}
    raise DataError("the model response does not contain a valid JSON "
                    "classification object")


def parse_sections(text: str, total: int) -> List[dict]:
    payload = _extract_json(text)
    raw_sections = (payload.get("sections")
                    or payload.get("data")
                    or payload.get("ranges")
                    or [])
    if not isinstance(raw_sections, list):
        raise DataError("'sections' must be a list")
    if len(raw_sections) > MAX_SECTIONS:
        raise DataError(f"too many sections ({len(raw_sections)} > "
                        f"{MAX_SECTIONS})")
    sections = []
    for index, entry in enumerate(raw_sections):
        if not isinstance(entry, dict):
            raise DataError(f"section {index} is not an object")
        offset_value = entry.get("offset", entry.get("address",
                                                      entry.get("start")))
        length_value = entry.get("length", entry.get("size",
                                                     entry.get("len")))
        if offset_value is None:
            raise DataError(f"section {index} has no offset")
        try:
            offset = _as_int(offset_value)
            if length_value is None and entry.get("end") is not None:
                length = _as_int(entry["end"]) - offset
            else:
                length = _as_int(length_value)
        except (TypeError, ValueError) as error:
            raise DataError(f"section {index} has invalid offset/length: "
                            f"{error}") from error
        if offset < 0 or length <= 0 or offset + length > total:
            raise DataError(
                f"section {index} is out of range: offset={offset}, "
                f"length={length}, payload={total}")
        kind = str(entry.get("kind") or "unknown").lower()
        text_value = entry.get("text")
        sections.append({
            "offset": offset,
            "length": length,
            "kind": kind,
            "text": text_value if isinstance(text_value, str) else None,
        })
    sections.sort(key=lambda item: item["offset"])
    for previous, current in zip(sections, sections[1:]):
        if previous["offset"] + previous["length"] > current["offset"]:
            raise DataError(
                f"overlapping sections: {previous['offset']}+"
                f"{previous['length']} and {current['offset']}+"
                f"{current['length']}")
    return sections


@dataclass
class DataResult:
    zone: object
    sections: List[dict]
    dropped: List[dict]
    xrefs: List[tuple]
    stats: RunStats
    raw_json: str

    @property
    def data_bytes(self) -> int:
        if self.zone is not None and getattr(self.zone, "final_data_blob", None):
            return len(self.zone.final_data_blob)
        return sum(section["length"] for section in self.sections)

    def to_dict(self) -> dict:
        return {
            "sections": [
                {
                    "offset": section["offset"],
                    "length": section["length"],
                    "kind": section.get("kind", "unknown"),
                    "text": section.get("text"),
                }
                for section in self.sections
            ],
            "dropped_no_reference": [
                {
                    "offset": section["offset"],
                    "length": section["length"],
                    "kind": section.get("kind", "unknown"),
                }
                for section in self.dropped
            ],
            "xrefs": [
                {"source": source, "target": target, "length": length}
                for source, target, length in self.xrefs
            ],
            "data_bytes": self.data_bytes,
            "stats": self.stats.to_dict(),
        }

    def write_json(self, path: str) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(self.to_dict(), handle, indent=2)
            handle.write("\n")


def _feedback(error: str, previous: str) -> str:
    clipped = previous.strip()
    if len(clipped) > 10000:
        clipped = clipped[:5000] + "\n... (truncated) ...\n" + clipped[-5000:]
    return "\n".join([
        "Your classification was rejected.",
        "",
        "REASON:",
        error,
        "",
        "PREVIOUS ANSWER:",
        "```json",
        clipped,
        "```",
        "",
        "Return the corrected JSON object only. Remember:",
        "* offsets/lengths are byte offsets from payload start;",
        "* ranges must be inside the payload and non-overlapping;",
        "* include NUL terminators for C strings and complete table entries;",
        "* do not classify executable code;",
        "* use the hex/ASCII view to overrule misleading disassembly;",
        "* a range without a code reference will be dropped;",
        "* if there is no data, return {\"sections\":[]}.",
    ])


def run_data(zone_factory: Callable[[], object], raw: bytes, arch: str,
             options: engine.LLMOptions,
             dump_prompt: Optional[str] = None,
             dump_response: Optional[str] = None) -> DataResult:
    """Classify data with the LLM and apply the extraction to a fresh Zone."""
    if options.retries < 1:
        raise engine.LLMConfigError("--llm-retries must be at least 1")
    if options.shots < 0 or options.shots > 5:
        raise engine.LLMConfigError("--llm-shots must be between 0 and 5")
    if len(raw) > MAX_PAYLOAD:
        raise engine.LLMConfigError(
            f"payload is {len(raw)} bytes; LLM data classification is limited "
            f"to {MAX_PAYLOAD} bytes — use the symbolic -xd instead")

    messages = build_data_messages(raw, arch, shots=options.shots)
    if dump_prompt:
        with open(dump_prompt, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n\n".join(
                f"### {message['role']}\n{message['content']}"
                for message in messages))

    client = None
    if not options.mock_response:
        client = engine.DeepSeekClient(options)

    stats = RunStats(model=options.model, technique="data", arch=arch)
    last_error = ""
    last_source = ""
    attempts = 0
    for attempt in range(1, options.retries + 1):
        attempts = attempt
        print(f"[llm-data] attempt {attempt}/{options.retries}: "
              f"{options.model}")
        attempt_started_at = datetime.now(timezone.utc)
        attempt_clock = time.perf_counter()
        api_clock = time.perf_counter()
        if options.mock_response:
            try:
                with open(options.mock_response, "r",
                          encoding="utf-8") as handle:
                    mock_text = handle.read()
            except OSError as error:
                raise engine.LLMConfigError(
                    f"cannot read --llm-mock-response: {error}") from error
            chunks = mock_text.split("\n---ATTEMPT---\n")
            response = chunks[min(attempt - 1, len(chunks) - 1)]
            api_seconds = 0.0
        else:
            calls_before = len(stats.api_calls)

            def record_call(call, _attempt=attempt):
                call.generation_attempt = _attempt
                stats.add_api_call(call)

            try:
                response, _usage = client.chat(messages, on_call=record_call)
            except engine.LLMTruncatedError as error:
                api_seconds = time.perf_counter() - api_clock
                stats.add_attempt(AttemptRecord(
                    attempt=attempt, started_at=attempt_started_at,
                    seconds=time.perf_counter() - attempt_clock,
                    api_seconds=api_seconds, response_chars=len(error.content),
                    accepted=False, error=str(error)))
                error.stats = stats
                last_error = str(error)
                last_source = error.content
                print(f"[llm-data] rejected: {last_error}")
                if attempt >= options.retries:
                    break
                if error.content.strip():
                    messages.append({"role": "assistant",
                                     "content": error.content})
                messages.append({
                    "role": "user",
                    "content": "Your JSON was truncated. Return only the "
                               "complete JSON object, without prose.",
                })
                continue
            except engine.LLMAPIError as error:
                api_seconds = time.perf_counter() - api_clock
                stats.add_attempt(AttemptRecord(
                    attempt=attempt, started_at=attempt_started_at,
                    seconds=time.perf_counter() - attempt_clock,
                    api_seconds=api_seconds, response_chars=0,
                    accepted=False, error=str(error)))
                stats.finish(False, str(error))
                error.stats = stats
                raise
            api_seconds = time.perf_counter() - api_clock
            att_usage = stats.usage_since(calls_before)
            att_cost = stats.cost_since(calls_before)
            cost_text = (f"${att_cost.total:.6f}" if att_cost is not None
                         else "n/a")
            print(f"[llm-data] attempt {attempt}: {att_usage.total:,} tokens "
                  f"({att_usage.prompt:,} in / "
                  f"{att_usage.completion:,} out), {api_seconds:.1f}s, "
                  f"{cost_text}")
        if dump_response:
            with open(dump_response, "w", encoding="utf-8",
                      newline="\n") as handle:
                handle.write(f"### attempt {attempt}\n{response}")

        try:
            sections = parse_sections(response, len(raw))
            if not sections:
                candidate = zone_factory()
                if candidate.sweep_coverage < len(raw):
                    raise DataError(
                        "you returned no sections, but the payload contains "
                        "bytes that the linear disassembler could not decode; "
                        "those bytes are probably data — classify them")
                stats.add_attempt(AttemptRecord(
                    attempt=attempt, started_at=attempt_started_at,
                    seconds=time.perf_counter() - attempt_clock,
                    api_seconds=api_seconds, response_chars=len(response),
                    accepted=True, code_bytes=len(raw), data_bytes=0,
                    instructions=len(candidate.instructions)))
                stats.finish(True)
                return DataResult(zone=candidate, sections=[], dropped=[],
                                  xrefs=[], stats=stats, raw_json=response)

            candidate = zone_factory()
            raw_sections = [{
                "address": section["offset"],
                "length": section["length"],
                "kind": section["kind"],
                "text": section.get("text"),
                "bytes": raw[section["offset"]:
                             section["offset"] + section["length"]],
            } for section in sections]
            xrefs = candidate.find_data_and_refs(sections=raw_sections)
            connected = []
            dropped = []
            for section in raw_sections:
                start = section["address"]
                end = start + section["length"]
                if any(start <= target < end for _source, target, _length
                       in xrefs):
                    connected.append(section)
                else:
                    dropped.append(section)
            if dropped:
                print(f"[llm-data] dropped {len(dropped)} section(s) with no "
                      "code reference")
            if not connected:
                raise DataError(
                    "none of the classified sections has a code reference; "
                    "check the offsets, or return an empty list if the payload "
                    "is all code")
            try:
                moved = candidate.extract_data(connected, xrefs,
                                               include_unknown=False)
                candidate.data_analysis_done = True
                candidate.finalize_data_refs()
            except Exception as error:
                raise DataError(f"the classified sections cannot be moved "
                                f"safely: {error}") from error
            if not moved:
                raise DataError(
                    "the classified sections could not be moved safely; their "
                    "references may be unsupported or they may overlap code")
            data_bytes = sum(len(section["bytes"]) for section in moved)
            stats.add_attempt(AttemptRecord(
                attempt=attempt, started_at=attempt_started_at,
                seconds=time.perf_counter() - attempt_clock,
                api_seconds=api_seconds, response_chars=len(response),
                accepted=True, code_bytes=candidate.final_code_len,
                data_bytes=data_bytes,
                instructions=len(candidate.instructions)))
            stats.finish(True)
            print(f"[llm-data] accepted {len(moved)} section(s), "
                  f"{data_bytes} data bytes")
            return DataResult(zone=candidate, sections=sections,
                              dropped=[{"offset": s["address"],
                                        "length": s["length"],
                                        "kind": s["kind"]}
                                       for s in dropped],
                              xrefs=list(xrefs), stats=stats,
                              raw_json=response)
        except DataError as error:
            last_error = str(error)
            last_source = response
            stats.add_attempt(AttemptRecord(
                attempt=attempt, started_at=attempt_started_at,
                seconds=time.perf_counter() - attempt_clock,
                api_seconds=api_seconds, response_chars=len(response),
                accepted=False, error=last_error))
            print(f"[llm-data] rejected: {last_error}")
            if attempt >= options.retries:
                break
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user",
                             "content": _feedback(last_error, response)})

    stats.finish(False, last_error)
    raise engine.LLMGenerationError(
        f"the model did not produce a usable data classification after "
        f"{attempts} attempt(s): {last_error}",
        attempts=attempts, last_source=last_source, last_error=last_error,
        stats=stats)
