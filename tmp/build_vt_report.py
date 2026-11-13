#!/usr/bin/env python3
"""Summarise tmp/vt_results.jsonl joined with vt_manifest.json."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    manifest = json.loads((ROOT / "vt_manifest.json").read_text(encoding="utf-8"))
    latest = {}
    path = ROOT / "tmp" / "vt_results.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        latest[record["sha256"]] = record

    groups = defaultdict(lambda: {"files": 0, "completed": 0, "detected": 0,
                                  "malicious": 0, "total": 0, "max": 0,
                                  "pending": 0})
    seen = set()
    for entry in manifest:
        if entry["sha256"] in seen:
            continue
        seen.add(entry["sha256"])
        group = groups[entry["technique"]]
        group["files"] += 1
        record = latest.get(entry["sha256"], {})
        if record.get("status") == "completed":
            group["completed"] += 1
            malicious = record.get("malicious", 0)
            group["malicious"] += malicious
            group["total"] += record.get("total", 0)
            group["detected"] += malicious > 0
            group["max"] = max(group["max"], malicious)
        else:
            group["pending"] += 1

    lines = ["# VirusTotal", "",
             "| Tecnica | File | Completati | Rilevati (>0) | Detection rate | "
             "Malicious medi | Max |", "|---|---:|---:|---:|---:|---:|---:|"]
    total_files = total_completed = total_detected = 0
    for technique in sorted(groups):
        group = groups[technique]
        rate = (group["detected"] / group["completed"] * 100
                if group["completed"] else 0.0)
        mean = (group["malicious"] / group["completed"]
                if group["completed"] else 0.0)
        lines.append(f"| `{technique}` | {group['files']} | "
                     f"{group['completed']} | {group['detected']} | "
                     f"{rate:.1f}% | {mean:.2f} | {group['max']} |")
        total_files += group["files"]
        total_completed += group["completed"]
        total_detected += group["detected"]
    overall = (total_detected / total_completed * 100
               if total_completed else 0.0)
    lines += ["", f"Totale: {total_completed}/{total_files} completati, "
                  f"{total_detected} rilevati ({overall:.1f}%).", ""]
    (ROOT / "VT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
