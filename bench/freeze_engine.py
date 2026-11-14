#!/usr/bin/env python3
"""Freeze the current Zone engine into bench/engines/<label>/.

The live tree is being edited by another session, so this script copies (never
moves or edits) the engine files and records their SHA-256, size and mtime.
A frozen copy is what every benchmark block must run against.

Usage:
    python bench/freeze_engine.py --label 2026-11-13_block1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "pobf.py",
    "pobf86.py",
    "asm_wrap.py",
    "symbolic_payload_coverage.py",
    "zone_utils.py",
    "increase_text.py",
    "llm_payload.py",
    "llm_technique.py",
    "llm_stats.py",
    "llm_data.py",
    "dict.txt",
    "blocks.txt",
    "jump_table.txt",
    "ploader.exe",
    "ploader86.exe",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              check=False).stdout.strip()
    except OSError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    target = ROOT / "bench" / "engines" / args.label
    if target.exists() and not args.force:
        print(f"[ERROR] {target} exists; pass --force to replace")
        return 1
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    records = {}
    missing = []
    for name in FILES:
        source = ROOT / name
        if not source.exists():
            missing.append(name)
            continue
        destination = target / name
        shutil.copy2(source, destination)
        records[name] = {
            "sha256": sha256(destination),
            "size": destination.stat().st_size,
            "source_mtime": time.strftime(
                "%Y-%m-%dT%H:%M:%S",
                time.localtime(source.stat().st_mtime)),
        }

    metadata = {
        "label": args.label,
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "git_head": git_head(),
        "missing": missing,
        "files": records,
    }
    (target / "VERSION.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"frozen {len(records)} files in {target}")
    for name, record in records.items():
        print(f"  {name:32s} {record['size']:7d}  "
              f"{record['sha256'][:16]}")
    if missing:
        print(f"[WARN] missing: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
