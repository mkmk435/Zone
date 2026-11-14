#!/usr/bin/env python3
"""Re-run every wrap output that failed the first functional check.

The first sweep overlapped with an unrelated bind on port 1234 for a few
seconds, so failed rows are retested serially with a longer window and with no
other harness running.  Results go to ``wrap_retest.jsonl``.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import harness

SOURCE = BASE / "wrap_test.jsonl"
OUT = BASE / "wrap_retest.jsonl"


def main() -> int:
    rows = [json.loads(line) for line in
            SOURCE.read_text(encoding="utf-8").splitlines()]
    already = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            already.add((row["arch"], row["payload"], row["seed"]))
    failed = [row for row in rows if row["status"] == "FAIL"
              and (row["arch"], row["payload"], row["seed"]) not in already]
    print(f"[INFO] {len(failed)} failed rows to retest", flush=True)
    started = time.time()
    counts = {"OK": 0, "FAIL": 0}
    with OUT.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(failed, 1):
            time.sleep(0.7)                 # let the previous listener settle
            ok, detail, elapsed = harness.check(ROOT / row["path"], row["arch"],
                                                timeout=10.0)
            record = {**row, "status": "OK" if ok else "FAIL",
                      "detail": detail, "elapsed_s": elapsed,
                      "retest": True}
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            counts[record["status"]] += 1
            print(f"[{index}/{len(failed)}] {record['arch']} "
                  f"{record['payload']} s{record['seed']} {record['status']} "
                  f"{detail} {elapsed}s", flush=True)
    print(f"[DONE] {counts} in {(time.time() - started) / 60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
