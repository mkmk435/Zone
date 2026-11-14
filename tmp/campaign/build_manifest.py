#!/usr/bin/env python3
"""Build the VirusTotal manifest from the campaign build records.

Only successfully built files are listed.  Entries keep the experimental
membership (group, payload, technique, seed/shots) even when the SHA-256 is
shared; ``tmp/vt_submit.py`` deduplicates uploads by hash while the report can
still attribute one scan to several conditions.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent


def read(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    entries = []
    for row in read(BASE / "wrap_build.jsonl"):
        if row.get("status") != "ok":
            continue
        entries.append({
            "path": row["out"],
            "sha256": row["sha256"],
            "group": "wrap",
            "technique": "wrap",
            "arch": row["arch"],
            "payload": row["payload"],
            "seed": row["seed"],
            "size": row["size"],
        })
    for row in read(BASE / "wrap_xu_build.jsonl"):
        if row.get("status") != "ok":
            continue
        entries.append({
            "path": row["out"],
            "sha256": row["sha256"],
            "group": "wrap_xu",
            "technique": "wrap_xu",
            "arch": row["arch"],
            "payload": row["payload"],
            "seed": row["seed"],
            "size": row["size"],
        })
    for row in read(BASE / "llm_build.jsonl"):
        if row.get("status") != "ok":
            continue
        entries.append({
            "path": row["out"],
            "sha256": row["sha256"],
            "group": "llm",
            "technique": f"llm_{row['tech']}_s{row['shots']}",
            "arch": row["arch"],
            "payload": row["payload"],
            "tech": row["tech"],
            "shots": row["shots"],
            "size": row["size"],
        })
    for row in read(BASE / "llm_data_build.jsonl"):
        if row.get("status") != "ok":
            continue
        entries.append({
            "path": row["out"],
            "sha256": row["sha256"],
            "group": "lldata",
            "technique": "lldata",
            "arch": row["arch"],
            "payload": row["payload"],
            "size": row["size"],
        })
    unique = {}
    for entry in entries:
        unique.setdefault(entry["sha256"], entry)
    out_json = ROOT / "vt_manifest_campaign.json"
    out_json.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    out_csv = ROOT / "vt_manifest_campaign.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256", "group",
                                                    "technique", "arch",
                                                    "payload", "size"])
        writer.writeheader()
        for entry in entries:
            writer.writerow({key: entry.get(key, "") for key in
                             writer.fieldnames})
    groups = Counter(entry["group"] for entry in entries)
    shared = sum(1 for count in Counter(entry["sha256"] for entry in entries).values()
                 if count > 1)
    print(f"[INFO] {len(entries)} files, {len(unique)} unique SHA-256")
    print(f"[INFO] groups: {dict(groups)}")
    print(f"[INFO] hashes shared by >1 condition: {shared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
