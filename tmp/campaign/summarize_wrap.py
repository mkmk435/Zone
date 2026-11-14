#!/usr/bin/env python3
"""Consolidate the wrapping campaign: build, functional and diversity counts."""
from __future__ import annotations

import csv
import json
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


def main() -> int:
    builds = read("wrap_build.jsonl")
    tests = read("wrap_test.jsonl")
    retests = read("wrap_retest.jsonl")
    final = {}
    for row in tests:
        final[(row["arch"], row["payload"], row["seed"])] = row
    for row in retests:
        final[(row["arch"], row["payload"], row["seed"])] = row

    per_payload = defaultdict(lambda: {"planned": 0, "built": 0, "worked": 0,
                                       "sha": []})
    per_arch = defaultdict(lambda: {"planned": 0, "built": 0, "worked": 0})
    failures = []
    for row in builds:
        key = (row["arch"], row["payload"])
        item = per_payload[key]
        item["planned"] += 1
        per_arch[row["arch"]]["planned"] += 1
        if row["status"] != "ok":
            failures.append({"arch": row["arch"], "payload": row["payload"],
                             "seed": row["seed"],
                             "kind": "build",
                             "error": (row.get("error") or "").strip().splitlines()[-1][:220]})
            continue
        item["built"] += 1
        item["sha"].append(row["sha256"])
        per_arch[row["arch"]]["built"] += 1
        test = final.get((row["arch"], row["payload"], row["seed"]))
        if test and test["status"] == "OK":
            item["worked"] += 1
            per_arch[row["arch"]]["worked"] += 1
        elif test:
            failures.append({"arch": row["arch"], "payload": row["payload"],
                             "seed": row["seed"], "kind": "functional",
                             "error": test.get("detail", "")})

    print("arch  planned built built% worked W/B%  W/N%  unique")
    for arch in ("x64", "x86"):
        stats = per_arch[arch]
        shas = [sha for row in builds if row["arch"] == arch and row["status"] == "ok"
                for sha in [row["sha256"]]]
        unique = len(set(shas))
        print(f"{arch:4s} {stats['planned']:7d} {stats['built']:5d} "
              f"{100 * stats['built'] / stats['planned']:5.1f}% "
              f"{stats['worked']:6d} "
              f"{100 * stats['worked'] / max(stats['built'], 1):5.1f}% "
              f"{100 * stats['worked'] / stats['planned']:5.1f}% {unique}/{len(shas)}")
    total = {key: sum(per_arch[arch][key] for arch in ("x64", "x86"))
             for key in ("planned", "built", "worked")}
    print(f"tot  {total['planned']:7d} {total['built']:5d} "
          f"{100 * total['built'] / total['planned']:5.1f}% "
          f"{total['worked']:6d} "
          f"{100 * total['worked'] / max(total['built'], 1):5.1f}% "
          f"{100 * total['worked'] / total['planned']:5.1f}%")

    with (BASE / "wrap_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["arch", "payload", "planned", "built", "worked",
                         "unique_sha", "build_fail", "functional_fail",
                         "working_rate_built", "working_rate_planned"])
        for (arch, payload), item in sorted(per_payload.items()):
            writer.writerow([
                arch, payload, item["planned"], item["built"], item["worked"],
                len(set(item["sha"])), item["planned"] - item["built"],
                item["built"] - item["worked"],
                round(item["worked"] / item["built"], 3) if item["built"] else "",
                round(item["worked"] / item["planned"], 3),
            ])
    with (BASE / "wrap_failures.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["arch", "payload", "seed",
                                                    "kind", "error"])
        writer.writeheader()
        writer.writerows(failures)
    print(f"[INFO] failures: {Counter(item['kind'] for item in failures)}")
    print(f"[INFO] write wrap_summary.csv / wrap_failures.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
