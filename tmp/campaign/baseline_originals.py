#!/usr/bin/env python3
"""Run the functional baseline on every original payload (x64 + x86)."""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness

OUT = Path(__file__).resolve().parent
FIELDS = ["arch", "payload", "kind", "status", "detail", "elapsed_s"]


def main() -> int:
    rows = []
    for arch in ("x64", "x86"):
        for path in sorted((ROOT / "original_pl" / arch).glob("*.bin")):
            rows.append({"arch": arch, "path": path})
    done = {}
    result_path = OUT / "baseline_originals.jsonl"
    if result_path.exists():
        for line in result_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done[(row["arch"], row["payload"])] = row
    started = time.time()
    with result_path.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(rows, 1):
            key = (row["arch"], row["path"].stem)
            if key in done:
                continue
            ok, detail, elapsed = harness.check(row["path"], row["arch"])
            record = {
                "arch": row["arch"],
                "payload": row["path"].stem,
                "kind": harness.kind_of(row["path"].stem),
                "status": "OK" if ok else "FAIL",
                "detail": detail,
                "elapsed_s": elapsed,
            }
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            done[key] = record
            print(f"[{index}/{len(rows)}] {record['arch']} {record['payload']} "
                  f"{record['status']} {detail} {elapsed}s", flush=True)
    ok = sum(1 for row in done.values() if row["status"] == "OK")
    print(f"[DONE] {ok}/{len(done)} OK in {time.time() - started:.1f}s")
    with (OUT / "baseline_originals.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in sorted(done.values(), key=lambda item: (item["arch"], item["payload"])):
            writer.writerow({key: row[key] for key in FIELDS})
    return 0


if __name__ == "__main__":
    sys.exit(main())
