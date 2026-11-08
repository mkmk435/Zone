"""Explore a raw x86/x64 payload with angr and report unobserved addresses.

The output is observational: an address not reached by this run is not proved
unreachable. The raw-payload environment, solver, CFG recovery, and limits all
affect coverage.

Example:
    python symbolic_payload_coverage.py new_payload.bin --arch x64
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import tempfile
import threading
import time
from collections import deque
from pathlib import Path
from types import SimpleNamespace


def integer(value: str) -> int:
    return int(value, 0)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path, help="Raw payload file")
    parser.add_argument("--arch", choices=("x86", "x64"), required=True)
    parser.add_argument("--entry-offset", type=integer, default=0,
                        help="Entry offset in the file (default: 0)")
    parser.add_argument("--base-address", type=integer, default=0x400000,
                        help="Virtual load address (default: 0x400000)")
    parser.add_argument("--max-steps", type=int, default=10000,
                        help="Maximum state/block steps; 0 disables (default: 10000)")
    parser.add_argument("--timeout", type=float, default=120,
                        help="Symbolic exploration timeout in seconds; 0 disables (default: 120)")
    parser.add_argument("--solver-timeout-ms", type=int, default=5000,
                        help="Timeout for each solver query; 0 disables (default: 5000 ms)")
    parser.add_argument("--progress-interval", type=float, default=5,
                        help="Print progress every N seconds; 0 disables (default: 5)")
    parser.add_argument("--max-queued-states", type=int, default=10000,
                        help="Stop if the pending frontier exceeds this size; 0 disables")
    parser.add_argument("--scan-all", action="store_true",
                        help="Let CFGFast scan the whole blob for code candidates; may classify data as code")
    parser.add_argument("--oppologist", action="store_true",
                        help="Try Unicorn for unsupported instructions; concretizes symbolic values")
    parser.add_argument("--output", type=Path,
                        help="JSON report (default: <payload stem>_symbolic_coverage.json)")
    args = parser.parse_args()
    if args.entry_offset < 0 or args.base_address < 0:
        parser.error("entry offset and base address must be nonnegative")
    if (args.max_steps < 0 or args.timeout < 0 or args.max_queued_states < 0
            or args.solver_timeout_ms < 0 or args.progress_interval < 0):
        parser.error("limits must be nonnegative; use 0 to disable")
    return args


def ranges_not_in_cfg(base: int, size: int, nodes: list[object]) -> list[dict]:
    """Byte ranges outside all recovered CFG blocks; they may be code or data."""
    in_cfg = bytearray(size)
    for node in nodes:
        start = max(0, node.addr - base)
        end = min(size, node.addr + node.size - base)
        if start < end:
            in_cfg[start:end] = b"\x01" * (end - start)
    ranges = []
    cursor = 0
    while cursor < size:
        if in_cfg[cursor]:
            cursor += 1
            continue
        end = cursor + 1
        while end < size and not in_cfg[end]:
            end += 1
        ranges.append({"offset_start": cursor, "offset_end_exclusive": end,
                       "address_start": hex(base + cursor),
                       "address_end_exclusive": hex(base + end)})
        cursor = end
    return ranges


def static_candidates(project, base: int, size: int, scan_all: bool,
                      function_starts: set[int] | None = None):
    cfg = project.analyses.CFGFast(
        start_at_entry=True,
        force_complete_scan=scan_all,
        force_smart_scan=False,
        function_prologues=False,
        symbols=False,
        normalize=True,
        data_references=True,
        function_starts=sorted(function_starts) if function_starts else None,
    )
    nodes = [
        node for node in cfg.graph.nodes
        if isinstance(getattr(node, "addr", None), int)
        and isinstance(getattr(node, "size", None), int)
        and node.size > 0 and base <= node.addr < base + size
    ]
    addresses = {
        addr for node in nodes for addr in node.instruction_addrs
        if base <= addr < base + size
    }
    code_spans = [(node.addr, node.addr + node.size) for node in nodes]
    inferred_data = [
        (addr, addr + item.size, str(getattr(item, "sort", "unknown")))
        for addr, item in cfg.model.memory_data.items()
        if isinstance(addr, int) and isinstance(getattr(item, "size", None), int)
        and item.size > 0 and addr < base + size and addr + item.size > base
    ]
    return addresses, ranges_not_in_cfg(base, size, nodes), len(nodes), code_spans, inferred_data


def identify_data(raw: bytes, base: int, arch: str, observed: set[int],
                  candidates: set[int],
                  code_spans: list[tuple[int, int]],
                  inferred_data: list[tuple[int, int, str]]):
    """Find data candidates without calling unvisited code proven unreachable."""
    import capstone

    size = len(raw)
    code = bytearray(size)
    executed = bytearray(size)
    cfg_data = bytearray(size)
    call_pop_gaps: set[tuple[int, int]] = set()

    def mark(mask: bytearray, start: int, end: int):
        lo, hi = max(0, start - base), min(size, end - base)
        if lo < hi:
            mask[lo:hi] = b"\x01" * (hi - lo)

    for start, end in code_spans:
        mark(code, start, end)
    for start, end, _ in inferred_data:
        mark(cfg_data, start, end)

    decoder = capstone.Cs(capstone.CS_ARCH_X86,
                          capstone.CS_MODE_64 if arch == "x64" else capstone.CS_MODE_32)
    decoder.detail = True
    for address in observed:
        offset = address - base
        instruction = next(decoder.disasm(raw[offset:offset + 15], address, count=1), None)
        if instruction is not None and instruction.address == address:
            mark(executed, address, address + instruction.size)
        else:
            mark(executed, address, address + 1)

    # A forward call to a pop instruction can skip inline data, but a normal
    # callee can also return to ordinary code in the gap. Only use this pattern
    # to corroborate a string that occupies the *entire* gap.
    for address in candidates | observed:
        offset = address - base
        instruction = next(decoder.disasm(raw[offset:offset + 15], address, count=1), None)
        if (instruction is None or instruction.mnemonic != "call"
                or not instruction.operands
                or instruction.operands[0].type != capstone.x86_const.X86_OP_IMM):
            continue
        gap_start = address + instruction.size
        target = instruction.operands[0].imm
        if not gap_start < target <= base + size:
            continue
        target_offset = target - base
        if target_offset >= size:
            continue
        target_instruction = next(decoder.disasm(
            raw[target_offset:target_offset + 15], target, count=1), None)
        if target_instruction is None or target_instruction.mnemonic != "pop":
            continue
        if not any(executed[gap_start - base:target_offset]):
            call_pop_gaps.add((gap_start - base, target_offset))

    strings = []
    string_bytes = bytearray(size)
    patterns = (
        ("ascii", re.compile(rb"[\x20-\x7e]{4,}\x00")),
        ("utf16le", re.compile(rb"(?:[\x20-\x7e]\x00){4,}\x00\x00")),
    )
    for encoding, pattern in patterns:
        for match in pattern.finditer(raw):
            start, end = match.span()
            if any(executed[start:end]) or any(string_bytes[start:end]):
                continue
            cfg_overlap = any(code[start:end])
            if cfg_overlap and (start, end) not in call_pop_gaps:
                continue
            chunk = raw[start:end]
            text = (chunk[:-1].decode("ascii") if encoding == "ascii"
                    else chunk[:-2].decode("utf-16le"))
            strings.append({
                "kind": encoding,
                "offset_start": start,
                "offset_end_exclusive": end,
                "address_start": hex(base + start),
                "size": end - start,
                "text": text,
                "hex": chunk.hex(" "),
                "cfg_code_overlap": cfg_overlap,
            })
            string_bytes[start:end] = b"\x01" * (end - start)

    raw_candidates = []
    offset = 0
    while offset < size:
        if executed[offset] or string_bytes[offset] or (code[offset] and not cfg_data[offset]):
            offset += 1
            continue
        kind = "cfg_data" if cfg_data[offset] else "outside_cfg"
        end = offset + 1
        while (end < size and not executed[end] and not string_bytes[end]
               and (not code[end] or cfg_data[end])
               and ("cfg_data" if cfg_data[end] else "outside_cfg") == kind):
            end += 1
        chunk = raw[offset:end]
        raw_candidates.append({
            "kind": kind,
            "offset_start": offset,
            "offset_end_exclusive": end,
            "address_start": hex(base + offset),
            "size": end - offset,
            "hex": chunk.hex(" "),
            "ascii_preview": "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk[:64]),
        })
        offset = end
    strings.sort(key=lambda item: item["offset_start"])
    return strings, raw_candidates, sum(executed)


def _print_payload_details(raw: bytes, path: Path | None, arch: str,
                           base: int, entry_offset: int) -> None:
    source = str(path.resolve()) if path is not None else "<in-memory bytes>"
    print(f"Payload: {source} ({len(raw)} B)", flush=True)
    print(f"SHA-256: {hashlib.sha256(raw).hexdigest()}", flush=True)
    print(f"Architecture: {arch}; base: {hex(base)}; "
          f"entry: {hex(base + entry_offset)}", flush=True)


def _print_exploration_status(run: dict) -> None:
    print(f"Stopped: {run['stop_reason']} after {run['steps']} steps "
          f"in {run['elapsed_seconds']:.3f}s "
          f"({run['pending_states']} states pending, "
          f"{run['deadended_states']} deadended, "
          f"{run['unconstrained_states']} unconstrained, {len(run['errors'])} errors)")
    for error in run["errors"][:5]:
        print(f"  Exploration error at {error['address']}: {error['error']!r}")
    if len(run["errors"]) > 5:
        print(f"  ... {len(run['errors']) - 5} additional exploration errors")


def find_data_sections(payload: bytes | bytearray | memoryview | str | Path,
                       arch: str, *, base_address: int = 0x400000,
                       entry_offset: int = 0, scan_all: bool = False,
                       max_steps: int = 10000, timeout: float = 120,
                       solver_timeout_ms: int = 5000,
                       max_queued_states: int = 10000,
                       oppologist: bool = False,
                       print_strings: bool = True,
                       return_strings: bool = False
                       ) -> list[dict] | tuple[list[dict], list[dict]]:
    """Return heuristic data ranges as dictionaries with address and length.

    Payload may be raw bytes or a path to a raw x86/x64 payload. Each result
    has integer address, offset, and length fields, plus kind (ascii, utf16le,
    cfg_data, or outside_cfg). These are candidates, not proven data: bounded
    exploration can miss code paths, and CFG recovery can mistake code for
    data. Found strings are printed with their start address, file offset,
    byte length (including the NUL terminator), encoding, and text.
    Input identity and exploration stop diagnostics are also printed. Pass
    print_strings=False to suppress all this output. The function does not
    modify the payload.

    With return_strings=True, return (sections, string_candidates) instead.
    The second list contains the full string records used by the CLI report:
    kind, offset_start, offset_end_exclusive, address_start (hex), size, text,
    hex, and cfg_code_overlap. String sizes include the NUL terminator.
    This option is independent of print_strings.
    """
    if arch not in ("x86", "x64"):
        raise ValueError("arch must be 'x86' or 'x64'")
    if base_address < 0 or entry_offset < 0:
        raise ValueError("base_address and entry_offset must be nonnegative")
    if any(value < 0 for value in (max_steps, timeout, solver_timeout_ms,
                                    max_queued_states)):
        raise ValueError("analysis limits must be nonnegative")

    if isinstance(payload, (str, Path)):
        payload_path = Path(payload)
        raw = payload_path.read_bytes()
    elif isinstance(payload, (bytes, bytearray, memoryview)):
        raw = bytes(payload)
        payload_path = None
    else:
        raise TypeError("payload must be raw bytes or a filesystem path")
    if not raw or entry_offset >= len(raw):
        raise ValueError("entry_offset must be inside a nonempty payload")

    try:
        import angr
    except ImportError as exc:
        raise ImportError("angr is required: python -m pip install angr") from exc

    options = SimpleNamespace(
        entry_offset=entry_offset, scan_all=scan_all, max_steps=max_steps,
        timeout=timeout, solver_timeout_ms=solver_timeout_ms,
        max_queued_states=max_queued_states, oppologist=oppologist,
        progress_interval=0,
    )

    # CFGFast's data-reference heuristic treats small constants inside the
    # payload as absolute pointers. When the blob is mapped at 0, offsets such
    # as the 0x4a displacement in `movzx rcx, [rdx+0x4a]` look like valid
    # addresses: code bytes get marked as data, the block is truncated, and the
    # remaining code is later classified as data. Analyze at a nonzero base and
    # translate the reported addresses back to the caller's address space.
    analysis_base = base_address if base_address >= 0x10000 else 0x400000
    shift = base_address - analysis_base

    def analyze(path: Path) -> list[dict] | tuple[list[dict], list[dict]]:
        if print_strings:
            _print_payload_details(raw, payload_path, arch, base_address, entry_offset)
        logging.getLogger("angr").setLevel(logging.ERROR)
        project = angr.Project(
            str(path),
            main_opts={"backend": "blob", "arch": "x86" if arch == "x86" else "amd64",
                       "base_addr": analysis_base,
                       "entry_point": analysis_base + entry_offset},
            auto_load_libs=False,
        )
        candidates, unclassified, _, code_spans, inferred_data = static_candidates(
            project, analysis_base, len(raw), scan_all)
        run = explore(project, analysis_base, len(raw), options, angr)
        observed = run["observed"]
        block_entries = run["block_entries"]

        # Recover code reached through indirect transfers before classifying
        # bytes outside the first CFG pass as possible data.
        cfg_seeds = set()
        for item in unclassified:
            start = int(item["address_start"], 16)
            end = int(item["address_end_exclusive"], 16)
            entries = [address for address in block_entries if start <= address < end]
            if entries:
                cfg_seeds.add(min(entries))
        if cfg_seeds:
            candidates, _, _, code_spans, inferred_data = static_candidates(
                project, analysis_base, len(raw), scan_all, cfg_seeds)

        strings, raw_candidates, _ = identify_data(
            raw, analysis_base, arch, observed, candidates, code_spans, inferred_data)
        if shift:
            for item in strings + raw_candidates:
                item["address_start"] = hex(int(item["address_start"], 16) + shift)
            for error in run["errors"]:
                error["address"] = hex(int(error["address"], 16) + shift)
        if print_strings:
            print(f"String candidates: {len(strings)} "
                  "(length in bytes, including the NUL terminator)")
            for item in strings:
                print(f"  {item['address_start']} "
                      f"(+0x{item['offset_start']:x}, {item['size']} B) "
                      f"{item['kind']}: {item['text']!r}")
            _print_exploration_status(run)
            if (run["stop_reason"] != "frontier_exhausted"
                    or run["unconstrained_states"] or run["errors"]):
                print("Data candidates are provisional: symbolic exploration "
                      "has unresolved paths.")
        sections = [
            {"address": base_address + item["offset_start"],
             "offset": item["offset_start"], "length": item["size"],
             "kind": item["kind"]}
            for item in sorted(strings + raw_candidates,
                               key=lambda candidate: candidate["offset_start"])
        ]
        return (sections, strings) if return_strings else sections

    if payload_path is not None:
        return analyze(payload_path)
    with tempfile.TemporaryDirectory(prefix="symbolic_payload_coverage_") as temp_dir:
        path = Path(temp_dir) / "payload.bin"
        path.write_bytes(raw)
        return analyze(path)


def explore(project, base: int, size: int, args, angr):
    observed: set[int] = set()
    external: set[int] = set()
    block_entries: set[int] = set()

    def on_instruction(state):
        address = state.scratch.ins_addr
        if not isinstance(address, int):
            return
        if base <= address < base + size:
            observed.add(address)
        else:
            external.add(address)

    initial = project.factory.blank_state(
        addr=base + args.entry_offset,
        add_options={angr.options.SYMBOL_FILL_UNCONSTRAINED_MEMORY,
                     angr.options.SYMBOL_FILL_UNCONSTRAINED_REGISTERS},
    )
    initial.inspect.b("instruction", when=angr.BP_BEFORE, action=on_instruction)
    simgr = project.factory.simgr(initial, save_unconstrained=True)
    if args.oppologist:
        simgr.use_technique(angr.exploration_techniques.Oppologist())
    pending = deque(simgr.active)
    simgr.stashes["active"] = []
    started = time.monotonic()
    steps = deadended = unconstrained = 0
    errors: list[dict] = []
    stop_reason = "frontier_exhausted"
    current_address = None
    stop_progress = threading.Event()

    def show_progress():
        while not stop_progress.wait(args.progress_interval):
            address = hex(current_address) if current_address is not None else "between steps"
            print(f"[angr] {time.monotonic() - started:.1f}s, {steps} steps, "
                  f"{len(pending)} pending, current {address}, "
                  f"{len(observed)} instructions observed", flush=True)

    progress_thread = None
    if args.progress_interval:
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()

    try:
        while pending:
            elapsed = time.monotonic() - started
            if args.max_steps and steps >= args.max_steps:
                stop_reason = "max_steps"
                break
            if args.timeout and elapsed >= args.timeout:
                stop_reason = "timeout"
                break
            if args.max_queued_states and len(pending) > args.max_queued_states:
                stop_reason = "max_queued_states"
                break

            state = pending.popleft()
            current_address = state.addr
            if base <= current_address < base + size:
                block_entries.add(current_address)
            # angr 9.x exposes claripy's per-query timeout through this solver.
            # Clamp it to the remaining exploration budget so one query cannot
            # consume the full default claripy timeout (five minutes).
            remaining_ms = max(1, int((args.timeout - elapsed) * 1000)) if args.timeout else 0
            query_limit_ms = args.solver_timeout_ms
            if remaining_ms:
                query_limit_ms = min(query_limit_ms, remaining_ms) if query_limit_ms else remaining_ms
            if query_limit_ms:
                state.solver._solver.timeout = query_limit_ms

            simgr.stashes["active"] = [state]
            simgr.step()
            steps += 1
            pending.extend(simgr.active)
            deadended += len(simgr.deadended)
            unconstrained += len(simgr.unconstrained)
            for record in simgr.errored:
                errors.append({"address": hex(record.state.addr),
                               "error": str(record.error)})
            # Retain the frontier, but discard terminal states to bound memory use.
            simgr.stashes["active"] = []
            simgr.stashes["deadended"].clear()
            simgr.stashes["unconstrained"].clear()
            simgr.errored.clear()
            current_address = None
    finally:
        stop_progress.set()
        if progress_thread is not None:
            progress_thread.join(timeout=1)

    return {
        "observed": observed,
        "external": external,
        "block_entries": block_entries,
        "steps": steps,
        "pending_states": len(pending),
        "deadended_states": deadended,
        "unconstrained_states": unconstrained,
        "errors": errors,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> None:
    args = arguments()
    if not args.payload.is_file():
        raise SystemExit(f"Payload not found: {args.payload}")
    raw = args.payload.read_bytes()
    size = len(raw)
    if size == 0:
        raise SystemExit("Payload is empty")
    if args.entry_offset >= size:
        raise SystemExit("--entry-offset must be inside the payload")

    print("[angr] Loading angr and the payload...", flush=True)
    try:
        import angr
    except ImportError as exc:
        raise SystemExit("angr is required: python -m pip install angr") from exc

    logging.getLogger("angr").setLevel(logging.ERROR)
    base = args.base_address
    if base < 0x10000:
        print("[angr] warning: base addresses below 0x10000 are ambiguous for a raw "
              "payload; CFGFast can treat small constants as data pointers. "
              "find_data_sections() rebases internally; this CLI does not.",
              flush=True)
    _print_payload_details(raw, args.payload, args.arch, base, args.entry_offset)
    project = angr.Project(
        str(args.payload),
        main_opts={"backend": "blob", "arch": "x86" if args.arch == "x86" else "amd64",
                   "base_addr": base, "entry_point": base + args.entry_offset},
        auto_load_libs=False,
    )

    cfg_error = None
    print("[angr] Recovering static CFG candidates...", flush=True)
    try:
        candidates, unclassified, cfg_blocks, code_spans, inferred_data = static_candidates(
            project, base, size, args.scan_all)
    except Exception as exc:  # The symbolic run is useful even if CFG recovery fails.
        candidates, unclassified, cfg_blocks, code_spans, inferred_data = set(), [], 0, [], []
        cfg_error = f"{type(exc).__name__}: {exc}"

    initial_cfg_blocks = cfg_blocks
    print(f"[angr] CFG: {cfg_blocks} blocks, {len(candidates)} instruction candidates. "
          "Starting symbolic exploration...", flush=True)
    run = explore(project, base, size, args, angr)
    observed = run.pop("observed")
    external = run.pop("external")
    block_entries = run.pop("block_entries")

    # Indirect calls can enter code that CFGFast misses on its first pass.
    # Seed one observed entry per previously uncovered range and recover the
    # graph again; on the sample this finds the resolver at offset 0x0d.
    cfg_seeds = set()
    for item in unclassified:
        start = int(item["address_start"], 16)
        end = int(item["address_end_exclusive"], 16)
        entries = [address for address in block_entries if start <= address < end]
        if entries:
            cfg_seeds.add(min(entries))
    if cfg_error and not cfg_seeds:
        cfg_seeds = block_entries.copy()
    if cfg_seeds:
        print(f"[angr] Expanding CFG from {len(cfg_seeds)} observed code entries...", flush=True)
        try:
            candidates, unclassified, cfg_blocks, code_spans, inferred_data = static_candidates(
                project, base, size, args.scan_all, cfg_seeds)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            cfg_error = f"{cfg_error}; enriched CFG: {message}" if cfg_error else message

    strings, raw_candidates, executed_bytes = identify_data(
        raw, base, args.arch, observed, candidates, code_spans, inferred_data)
    data_candidates = sorted(strings + raw_candidates, key=lambda item: item["offset_start"])
    string_ranges = [(base + item["offset_start"], base + item["offset_end_exclusive"])
                     for item in strings]
    rejected_cfg_addresses = sorted(
        address for address in candidates - observed
        if any(start <= address < end for start, end in string_ranges)
    )
    candidates.difference_update(rejected_cfg_addresses)
    plausible_blocks = [
        (start, end) for start, end in code_spans
        if not any(lo <= start < hi for lo, hi in string_ranges)
    ]
    covered_blocks = sum(
        any(start <= address < end for address in observed)
        for start, end in plausible_blocks
    )
    unobserved_blocks = [
        hex(start) for start, end in plausible_blocks
        if not any(start <= address < end for address in observed)
    ]
    not_observed = sorted(candidates - observed)
    unresolved_paths = (run["pending_states"] + run["unconstrained_states"]
                        + len(run["errors"]))
    report = {
        "payload": str(args.payload.resolve()),
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "architecture": args.arch,
        "base_address": hex(base),
        "entry_address": hex(base + args.entry_offset),
        "size_bytes": size,
        "meaning": "not_observed means not reached during this bounded analysis, not proven unreachable; data_candidates are heuristic",
        "model": "raw blob; uninitialized memory and registers are symbolic; external OS environment is not initialized",
        "coverage_status": ("all_cfg_blocks_observed" if run["stop_reason"] == "frontier_exhausted"
                            and unresolved_paths == 0 and cfg_error is None
                            and covered_blocks == len(plausible_blocks) else "incomplete"),
        "unresolved_paths": unresolved_paths,
        "limits": {"max_steps": args.max_steps, "timeout_seconds": args.timeout,
                   "max_queued_states": args.max_queued_states,
                   "solver_timeout_ms": args.solver_timeout_ms},
        "scan_all": args.scan_all,
        "oppologist": args.oppologist,
        "cfg_blocks": cfg_blocks,
        "cfg_plausible_code_blocks": len(plausible_blocks),
        "cfg_observed_code_blocks": covered_blocks,
        "cfg_unobserved_code_block_addresses": unobserved_blocks,
        "cfg_initial_blocks": initial_cfg_blocks,
        "cfg_seeded_entry_addresses": [hex(address) for address in sorted(cfg_seeds)],
        "cfg_error": cfg_error,
        "cfg_candidate_instruction_count": len(candidates),
        "observed_instruction_byte_count": executed_bytes,
        "observed_instruction_addresses": [hex(addr) for addr in sorted(observed)],
        "not_observed_instruction_addresses": [hex(addr) for addr in not_observed],
        "candidate_instructions": [
            {"address": hex(addr), "offset": addr - base,
             "status": "observed" if addr in observed else "not_observed",
             "in_cfg": addr in candidates}
            for addr in sorted(candidates | observed)
        ],
        "outside_cfg_byte_ranges": unclassified,
        "data_candidates": data_candidates,
        "string_candidates": strings,
        "raw_data_candidates": raw_candidates,
        "cfg_instruction_candidates_rejected_as_strings": [hex(address)
                                                          for address in rejected_cfg_addresses],
        "observed_addresses_outside_payload": [hex(addr) for addr in sorted(external)],
        **run,
    }
    output = args.output or Path.cwd() / f"{args.payload.stem}_symbolic_coverage.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Observed {len(observed)} payload instructions; "
          f"{len(not_observed)} CFG candidates not observed")
    print(f"CFG code blocks observed: {covered_blocks}/{len(plausible_blocks)}")
    print(f"Data candidates: {len(strings)} strings, {len(raw_candidates)} raw ranges")
    for item in data_candidates:
        location = f"{item['address_start']} (+0x{item['offset_start']:x}, {item['size']} B)"
        if item["kind"] in ("ascii", "utf16le"):
            print(f"  {location} {item['kind']}: {item['text']!r} | {item['hex']}" +
                  (" [CFG overlap]" if item["cfg_code_overlap"] else ""))
        else:
            print(f"  {location} {item['kind']}: {item['hex']}")
    _print_exploration_status(run)
    if report["coverage_status"] == "incomplete":
        print("Data candidates are provisional: CFG coverage or symbolic paths remain incomplete.")
    if cfg_error:
        print(f"CFG recovery failed: {cfg_error}")
    print(f"Report: {output.resolve()}")


if __name__ == "__main__":
    main()
