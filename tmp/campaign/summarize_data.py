#!/usr/bin/env python3
"""Compare symbolic/heuristic -xd with LLM --llm-data on data-bearing payloads."""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]


def read(name: str):
    path = BASE / name
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _final_hash(arch: str, payload: str, llm: bool = False) -> str:
    if llm:
        path = ROOT / "mutations_all" / "lldata" / arch / f"{payload}_lldata.bin"
    else:
        path = BASE / "prewarm" / arch / f"{payload}.bin"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def main() -> int:
    symbolic = {row["payload"]: row for row in read("symbolic_test.jsonl")}
    llm_tests = {row["payload"]: row for row in read("lldata_test.jsonl")}
    builds = {row["payload"]: row for row in read("llm_data_build.jsonl")}
    symbolic_builds = {row["payload"]: row for row in read("symbolic_build.jsonl")}
    prewarm = {row["payload"]: row for row in read("prewarm_xd.jsonl")}

    rows = []
    for payload, build in sorted(builds.items()):
        arch = build["arch"]
        sym = prewarm.get(payload, {})
        sym_sections = []
        for line in sym.get("data_lines", []):
            if line.startswith("[extract] data 0x"):
                # [extract] data 0xff -> 0x14b (17 B)
                src = int(line.split("0x")[1].split()[0], 16)
                length = int(line.rsplit("(", 1)[1].split(" B")[0])
                sym_sections.append((src, length))
        llm_ranges = []
        for item in build.get("llm_ranges", []):
            offset = item.get("offset")
            length = item.get("length")
            if offset is not None and length is not None:
                llm_ranges.append((int(offset), int(length)))
        sym_set = sorted(sym_sections)
        llm_set = sorted(llm_ranges)
        rows.append({
            "arch": arch,
            "payload": payload,
            "symbolic_built": 1 if payload in symbolic_builds else 0,
            "symbolic_working": 1 if symbolic.get(payload, {}).get("status") == "OK" else 0,
            "symbolic_sections": len(sym_sections),
            "symbolic_bytes": sum(length for _, length in sym_sections),
            "symbolic_time_s": sym.get("elapsed_s", ""),
            "llm_built": 1 if build.get("status") == "ok" else 0,
            "llm_working": 1 if llm_tests.get(payload, {}).get("status") == "OK" else 0,
            "llm_sections": len(llm_ranges),
            "llm_bytes": sum(length for _, length in llm_ranges),
            "llm_time_s": build.get("elapsed_s", ""),
            "llm_cost_usd": build.get("cost_usd") or 0,
            "llm_attempts": build.get("attempts", ""),
            "llm_tokens": build.get("tokens", ""),
            "exact_sections": 1 if sym_set and sym_set == llm_set else 0,
            "final_identical": int(_final_hash(arch, payload) == _final_hash(arch, payload, llm=True)),
            "same_byte_count": 1 if sum(x[1] for x in sym_set) == sum(x[1] for x in llm_set) else 0,
            "symbolic_set": str(sym_set),
            "llm_set": str(llm_set),
        })

    fields = list(rows[0].keys())
    with (BASE / "data_compare.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    def pct(values):
        return f"{sum(values)}/{len(values)} ({100 * sum(values) / len(values):.1f}%)"

    print(f"payloads: {len(rows)}")
    print(f"symbolic built: {pct([r['symbolic_built'] for r in rows])}")
    print(f"symbolic working: {pct([r['symbolic_working'] for r in rows])}")
    print(f"LLM built: {pct([r['llm_built'] for r in rows])}")
    print(f"LLM working: {pct([r['llm_working'] for r in rows])}")
    print(f"exact section agreement: {pct([r['exact_sections'] for r in rows])}")
    print(f"same byte count (raw ranges): {pct([r['same_byte_count'] for r in rows])}")
    print(f"final output identical: {pct([r['final_identical'] for r in rows])}")
    print(f"symbolic time median: {statistics.median(r['symbolic_time_s'] for r in rows):.1f}s")
    print(f"LLM time median: {statistics.median(r['llm_time_s'] for r in rows):.1f}s")
    print(f"LLM cost total: ${sum(r['llm_cost_usd'] for r in rows):.4f} "
          f"(median ${statistics.median(r['llm_cost_usd'] for r in rows):.4f})")
    print("[INFO] write data_compare.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
