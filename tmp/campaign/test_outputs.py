#!/usr/bin/env python3
"""Execute every built mutant and record its functional observable.

Reads a build JSONL (``--build``) and runs the harness on each ``ok`` row.
Resumable through the output JSONL.  Network tests are serialized because every
payload uses the same local port 1234.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import harness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    build = BASE / args.build
    out = BASE / args.out
    rows = [json.loads(line) for line in
            build.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done.add((row["arch"], row["payload"], row.get("label", ""),
                      row.get("seed", ""), row.get("tech", ""), row.get("shots", "")))
    started = time.time()
    tested = 0
    with out.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(rows, 1):
            if row.get("status") != "ok":
                continue
            key = (row["arch"], row["payload"], args.label,
                   row.get("seed", ""), row.get("tech", ""), row.get("shots", ""))
            if key in done:
                continue
            path = ROOT / row["out"]
            ok, detail, elapsed = harness.check(path, row["arch"])
            record = {
                "label": args.label,
                "arch": row["arch"],
                "payload": row["payload"],
                "seed": row.get("seed", ""),
                "tech": row.get("tech", ""),
                "shots": row.get("shots", ""),
                "path": row["out"],
                "sha256": row.get("sha256", ""),
                "size": row.get("size", 0),
                "status": "OK" if ok else "FAIL",
                "detail": detail,
                "elapsed_s": elapsed,
            }
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            done.add(key)
            tested += 1
            print(f"[{index}/{len(rows)}] {record['arch']} {record['payload']} "
                  f"{args.label} {record['status']} {detail} {elapsed}s",
                  flush=True)
    ok_count = sum(1 for row in done if True)
    total = len(done)
    passed = 0
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["status"] == "OK":
                passed += 1
    print(f"[DONE] {passed}/{total} OK, {tested} new in "
          f"{(time.time() - started) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
