#!/usr/bin/env python3
"""Pre-warm data_cache.json for every selected payload (sequential).

`-fd` reuses a cache hit instantly; a miss runs symbolic exploration once.
Sequential execution avoids concurrent writers to data_cache.json.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
LOCAL_CAPSTONE = ROOT / "tmp" / "capstone506"


def cached_paths(cache_path):
    if not os.path.exists(cache_path):
        return set()
    try:
        data = json.load(open(cache_path, encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for v in data.get("payloads", {}).values():
        p = v.get("payload")
        if p:
            out.add(os.path.normcase(os.path.abspath(p)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="tmp/low_payloads.json")
    ap.add_argument("--cache", default="data_cache.json")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--logs", default="tmp/precache_logs")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = json.load(open(args.list, encoding="utf-8"))["payloads"]
    have = set() if args.force else cached_paths(args.cache)
    logs = Path(args.logs)
    logs.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(LOCAL_CAPSTONE)

    todo = []
    for r in rows:
        src = ROOT / "original_pl" / r["arch"] / f"{r['payload']}.bin"
        if os.path.normcase(str(src.resolve())) not in have:
            todo.append((r, src))
    print(f"[INFO] {len(rows)} payloads, {len(todo)} need analysis", flush=True)

    t0 = time.time()
    for n, (r, src) in enumerate(todo, 1):
        tool = "pobf.py" if r["arch"] == "x64" else "pobf86.py"
        log = logs / f"{r['arch']}_{r['payload']}.log"
        print(f"[{n}/{len(todo)}] {r['arch']}/{r['payload']}", flush=True)
        t = time.time()
        with open(log, "wb") as lf:
            p = subprocess.run(
                [sys.executable, tool, str(src), "-fd",
                 "--data-timeout", str(args.timeout)],
                cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT,
            )
        txt = log.read_text(errors="replace")
        sections = "Data sections:" in txt
        print(f"    rc={p.returncode} {time.time()-t:.1f}s "
              f"sections_printed={sections}", flush=True)
    print(f"[DONE] {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
