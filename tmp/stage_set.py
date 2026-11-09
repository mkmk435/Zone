"""Stage a payload set (from low_payloads.json) into <out>/x64 and <out>/x86."""
import argparse
import json
import os
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="tmp/low_payloads.json")
    ap.add_argument("--out", default="tmp/original_low_set")
    ap.add_argument("--source", default="original_pl")
    args = ap.parse_args()

    data = json.load(open(args.list, encoding="utf-8"))
    n = 0
    for r in data["payloads"]:
        arch, name = r["arch"], r["payload"]
        src = Path(args.source) / arch / f"{name}.bin"
        if not src.exists():
            print(f"[MISSING] {src}")
            continue
        dst = Path(args.out) / arch
        dst.mkdir(parents=True, exist_ok=True)
        target = dst / src.name
        if target.exists():
            continue
        try:
            os.link(src, target)
        except OSError:
            shutil.copy2(src, target)
        n += 1
    print(f"staged {n} files into {args.out}")


if __name__ == "__main__":
    main()
