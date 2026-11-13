#!/usr/bin/env python3
"""Build the VirusTotal submission manifest for the new experiments.

Sources:
  mutations_wrap/x64/*.bin          (native -wrap, two configurations)
  mutations_llm/x64/*.bin           (LLM morphing, 4 techniques x 0/2 shots)
  mutations_llm_data/{x64,x86}/*.bin (LLM data classification)

Outputs vt_manifest.csv / vt_manifest.json with sha256, technique, payload and
the local working-rate verdict.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = {}


def load_report(path: Path) -> None:
    if not path.exists():
        return
    for row in csv.reader(path.open(encoding="utf-8", errors="replace")):
        if len(row) >= 3:
            RESULTS[row[0].split("/")[-1]] = (row[2], row[3] if len(row) > 3 else "")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(name: str):
    stem = name[:-4]
    for tech in ("wrap_full", "wrap"):
        marker = f"_{tech}_"
        if marker in stem:
            return stem.split(marker)[0], tech
    match = re.match(r"(.+)_llm_([a-z]+)_s([02])_(\d+)$", stem)
    if match:
        return match.group(1), f"llm_{match.group(2)}_s{match.group(3)}"
    match = re.match(r"(.+)_lldata(_eq)?_(\d+)$", stem)
    if match:
        return match.group(1), "lldata_eq" if match.group(2) else "lldata"
    return stem, "unknown"


def main() -> int:
    for report in ("tmp/wrap_report.csv", "tmp/llm_morph_report.csv",
                   "tmp/llm_data_report.csv"):
        load_report(ROOT / report)

    entries = []
    for folder, arch in (("mutations_wrap/x64", "x64"),
                         ("mutations_llm/x64", "x64"),
                         ("mutations_llm_data/x64", "x64"),
                         ("mutations_llm_data/x86", "x86")):
        directory = ROOT / folder
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.bin")):
            payload, technique = classify(path.name)
            status, detail = RESULTS.get(path.name, ("", ""))
            entries.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "size": path.stat().st_size,
                "arch": arch,
                "technique": technique,
                "payload": payload,
                "working": status,
                "detail": detail,
            })

    (ROOT / "vt_manifest.json").write_text(
        json.dumps(entries, indent=2), encoding="utf-8")
    with (ROOT / "vt_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)

    unique = len({entry["sha256"] for entry in entries})
    print(f"{len(entries)} files, {unique} unique sha256")
    by_tech = {}
    for entry in entries:
        key = (entry["technique"], entry["working"])
        by_tech[key] = by_tech.get(key, 0) + 1
    for key in sorted(by_tech):
        print(f"  {key[0]:16s} {key[1]:5s} {by_tech[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
