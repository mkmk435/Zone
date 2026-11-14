#!/usr/bin/env python3
"""Consolidate the LLM-morphing matrix: build, functional, diversity, cost."""
from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]


def read(name: str):
    path = BASE / name
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def failure_class(error: str) -> str:
    text = error or ""
    if "truncated" in text or "finish_reason=length" in text:
        return "length"
    if "not fully disassembled" in text or "instruction boundary" in text:
        return "disassembly"
    if "IncompleteRead" in text or "timed out" in text or "HTTP" in text:
        return "network"
    if "did not produce a valid" in text or "rejected" in text:
        return "validation"
    if "data" in text and ("extract" in text or "xref" in text):
        return "data"
    return "other"


def main() -> int:
    builds = read("llm_build.jsonl")
    tests = {(row["arch"], row["payload"], row["tech"], row["shots"]): row
             for row in read("llm_test.jsonl")}
    planned = {}
    for arch, count in (("x64", 38), ("x86", 64)):
        for payload in sorted((ROOT / "original_pl" / arch).glob("*.bin")):
            for tech in ("eq", "nop", "bcf", "ibp"):
                for shots in (0, 2):
                    planned[(arch, payload.stem, tech, shots)] = True

    by_key = {}
    for item in builds:
        key = (item["arch"], item["payload"], item["tech"], item["shots"])
        previous = by_key.get(key)
        if previous is None or (item["status"] == "ok" and previous["status"] != "ok"):
            by_key[key] = item
    cells = []
    for key in planned:
        row = by_key.get(key)
        if row is None:
            cells.append({"arch": key[0], "payload": key[1], "tech": key[2],
                          "shots": key[3], "status": "missing", "built": 0,
                          "worked": 0, "sha256": "", "cost_usd": 0.0,
                          "attempts": 0, "similarity": None, "elapsed_s": 0,
                          "error": ""})
            continue
        test = tests.get(key, {})
        cells.append({
            "arch": row["arch"], "payload": row["payload"], "tech": row["tech"],
            "shots": row["shots"], "status": row["status"],
            "built": 1 if row["status"] == "ok" else 0,
            "worked": 1 if test.get("status") == "OK" else 0,
            "sha256": row.get("sha256", ""),
            "cost_usd": row.get("cost_usd") or 0.0,
            "attempts": row.get("attempts") or 0,
            "similarity": row.get("similarity"),
            "elapsed_s": row.get("elapsed_s") or 0,
            "error": row.get("error", ""),
        })

    fields = ["arch", "payload", "tech", "shots", "status", "built", "worked",
              "sha256", "cost_usd", "attempts", "similarity", "elapsed_s",
              "error"]
    with (BASE / "llm_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(cells)

    print(f"{'arch':4s} {'tech':4s} {'shot':4s} {'planned':>7s} {'built':>5s} "
          f"{'work':>5s} {'W/B':>6s} {'unique':>7s} {'cost':>8s} {'avg':>7s}")
    for arch in ("x64", "x86"):
        for tech in ("eq", "nop", "bcf", "ibp"):
            for shots in (0, 2):
                group = [row for row in cells if row["arch"] == arch
                         and row["tech"] == tech and row["shots"] == shots]
                built = sum(row["built"] for row in group)
                worked = sum(row["worked"] for row in group)
                unique = len({row["sha256"] for row in group if row["sha256"]})
                cost = sum(row["cost_usd"] for row in group)
                print(f"{arch:4s} {tech:4s} {shots:4d} {len(group):7d} "
                      f"{built:5d} {worked:5d} "
                      f"{100 * worked / built if built else 0:5.1f}% "
                      f"{unique:7d} {cost:8.3f} "
                      f"{cost / len(group) if group else 0:7.4f}")
    complete = sum(1 for row in cells if row["status"] in ("ok", "fail"))
    built = sum(row["built"] for row in cells)
    worked = sum(row["worked"] for row in cells)
    cost = sum(row["cost_usd"] for row in cells)
    causes = Counter(failure_class(row["error"]) for row in cells
                     if row["status"] == "fail")
    print(f"[TOTAL] cells={len(cells)} attempted={complete} built={built} "
          f"worked={worked} cost=${cost:.4f} "
          f"avg=${cost / complete if complete else 0:.4f}")
    print(f"[FAIL] {dict(causes)}")
    print(f"[INFO] write llm_summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
