#!/usr/bin/env python3
"""Aggregate native and LLM attempts into the case matrix and metrics.

Metrics, kept separate on purpose:
  * build_ok / attempts
  * match / build_ok        (correct executions over successful builds)
  * match / attempts        (correct executions over total attempts)
  * unique_outputs / produced
An output counts as produced when the build succeeded; identical SHA-256
outputs are not independent samples.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def load(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def metrics(rows: list) -> dict:
    attempts = len(rows)
    build = sum(1 for row in rows if row["build_ok"])
    exec_ok = sum(1 for row in rows if row.get("exec_ok"))
    match = sum(1 for row in rows if row.get("match"))
    hashes = {row["sha256"] for row in rows if row["build_ok"]}
    return {
        "attempts": attempts,
        "build_ok": build,
        "exec_ok": exec_ok,
        "match": match,
        "unique_outputs": len(hashes),
        "produced": build,
        "build_rate": build / attempts if attempts else 0.0,
        "match_over_build": match / build if build else 0.0,
        "match_over_attempts": match / attempts if attempts else 0.0,
        "unique_over_produced": len(hashes) / build if build else 0.0,
    }


def main() -> int:
    native = load(RESULTS / "native_attempts.jsonl")
    llm = load(RESULTS / "llm_attempts.jsonl")
    classifier = load(RESULTS / "llm_data_attempts.jsonl")
    wrap86 = [row for row in load(RESULTS / "native_wrap86.jsonl")
              if row["technique"] == "wrap"]
    cases = {(case["arch"], case["name"]): case for case in json.loads(
        (HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))}

    # native technique cells (baseline xd excluded)
    native_cells = defaultdict(list)
    for row in native:
        if row["technique"] == "xd":
            continue
        native_cells[(row["arch"], row["case"], row["technique"])].append(row)
    baseline = [row for row in native if row["technique"] == "xd"]

    matrix = []
    for (arch, case, technique), rows in sorted(native_cells.items()):
        item = metrics(rows)
        item.update({
            "arch": arch, "case": case, "technique": technique,
            "kind": cases[(arch, case)]["kind"],
            "requires_extract": cases[(arch, case)]["requires_extract"],
        })
        matrix.append(item)

    # LLM cells
    llm_cells = defaultdict(list)
    for row in llm:
        llm_cells[(row["case"], row["technique"], row["shots"])].append(row)
    llm_matrix = []
    for (case, technique, shots), rows in sorted(llm_cells.items()):
        item = metrics(rows)
        item.update({
            "case": case, "technique": technique, "shots": shots,
            "cost_usd": sum(row.get("cost_usd") or 0.0 for row in rows),
            "api_calls": sum(row.get("generation_calls", 0) for row in rows),
            "api_attempts": sum(row.get("attempts") or 0 for row in rows),
        })
        llm_matrix.append(item)

    # Write CSV
    fields = ["arch", "case", "kind", "technique", "requires_extract",
              "attempts", "build_ok", "build_rate", "exec_ok", "match",
              "match_over_build", "match_over_attempts", "unique_outputs",
              "produced", "unique_over_produced"]
    with (RESULTS / "case_matrix_native.csv").open("w", newline="",
                                                    encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(matrix)

    fields_llm = ["case", "technique", "shots", "attempts", "build_ok",
                  "build_rate", "match", "match_over_build",
                  "match_over_attempts", "unique_outputs", "produced",
                  "unique_over_produced", "api_calls", "api_attempts",
                  "cost_usd"]
    with (RESULTS / "case_matrix_llm.csv").open("w", newline="",
                                                encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields_llm,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(llm_matrix)

    # aggregate per technique
    per_technique = defaultdict(list)
    for item in matrix:
        per_technique[item["technique"]].append(item)
    technique_summary = {}
    for technique, items in per_technique.items():
        attempts = sum(item["attempts"] for item in items)
        build = sum(item["build_ok"] for item in items)
        match = sum(item["match"] for item in items)
        unique = sum(item["unique_outputs"] for item in items)
        produced = sum(item["produced"] for item in items)
        technique_summary[technique] = {
            "attempts": attempts, "build_ok": build, "match": match,
            "unique_outputs": unique, "produced": produced,
            "build_rate": build / attempts if attempts else 0.0,
            "match_over_build": match / build if build else 0.0,
            "match_over_attempts": match / attempts if attempts else 0.0,
            "unique_over_produced": unique / produced if produced else 0.0,
        }

    llm_summary = {
        "calls": len(llm),
        "build_ok": sum(1 for row in llm if row["build_ok"]),
        "match": sum(1 for row in llm if row["match"]),
        "unique_outputs": len({row["sha256"] for row in llm
                               if row["build_ok"]}),
        "cost_usd": sum(row.get("cost_usd") or 0.0 for row in llm),
        "errors": [{"case": row["case"], "technique": row["technique"],
                    "shots": row["shots"], "call": row["call"],
                    "error": (row.get("error") or "")[-400:]}
                   for row in llm if not row["match"]],
    }

    summary = {
        "native": {
            "attempts": len(native),
            "techniques": technique_summary,
            "baseline_xd": metrics(baseline),
        },
        "wrap_x86_block2": metrics(wrap86),
        "llm": llm_summary,
        "classifier": {
            "calls": len(classifier),
            "exact_classification": sum(
                1 for row in classifier if row["exact_classification"]),
            "build_ok": sum(1 for row in classifier if row["build_ok"]),
            "match": sum(1 for row in classifier if row["match"]),
            "cost_usd": sum(row["cost_usd"] for row in classifier),
        },
        "matrix_native": matrix,
        "matrix_llm": llm_matrix,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2),
                                          encoding="utf-8")

    print("native per technique")
    for technique in sorted(technique_summary):
        item = technique_summary[technique]
        print(f"  {technique:6s} attempts={item['attempts']:3d} "
              f"build={item['build_ok']:3d} ({item['build_rate']*100:5.1f}%) "
              f"match/build={item['match_over_build']*100:5.1f}% "
              f"match/att={item['match_over_attempts']*100:5.1f}% "
              f"unique={item['unique_outputs']}/{item['produced']}")
    print(f"llm calls={llm_summary['calls']} build={llm_summary['build_ok']} "
          f"match={llm_summary['match']} "
          f"unique={llm_summary['unique_outputs']} "
          f"cost=${llm_summary['cost_usd']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
