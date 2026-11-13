#!/usr/bin/env python3
"""Generate assembly-wrapping mutants for the x64 low-working-rate payload set.

Two configurations are produced for every payload:

    wrap       -xd -wrap
    wrap_full  -xd -wrap -eq -nop -bcf -ibp

The engine is taken from ``tmp/wrap_snapshot`` so that concurrent edits to the
live tree cannot change the experiment half way through.  Every run executes
with ``tmp/wrap_run`` as its working directory, which holds dict.txt,
instr_payload*.txt and the warm data_cache.json.

Outputs: mutations_wrap/x64/<payload>_<tech>_<i>.bin
Manifest: mutations_wrap/manifest.jsonl (resumable: existing files are kept)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "tmp" / "wrap_snapshot" / "pobf.py"
RUNDIR = ROOT / "tmp" / "wrap_run"
MANIFEST_LOCK = threading.Lock()

CONFIGS = {
    "wrap": ["-xd", "-wrap"],
    "wrap_full": ["-xd", "-wrap", "-eq", "-nop", "-bcf", "-ibp"],
}


def load_payloads(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data["payloads"] if row["arch"] == "x64"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="tmp/low_payloads.json")
    ap.add_argument("--outdir", default="mutations_wrap")
    ap.add_argument("--per-tech", type=int, default=10)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--tech", action="append", default=None)
    args = ap.parse_args()

    rows = load_payloads(ROOT / args.list)
    techs = args.tech or list(CONFIGS)
    outdir = ROOT / args.outdir
    manifest = outdir / "manifest.jsonl"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    tasks = []
    for row in rows:
        for tech in techs:
            for index in range(1, args.per_tech + 1):
                out = outdir / "x64" / f"{row['payload']}_{tech}_{index}.bin"
                tasks.append({
                    "payload": row["payload"],
                    "tech": tech,
                    "index": index,
                    "src": ROOT / "original_pl" / "x64" / f"{row['payload']}.bin",
                    "out": out,
                    "seed": 1000 * (1 + list(CONFIGS).index(tech)) + index,
                })

    def generate(task):
        out = task["out"]
        if out.exists() and out.stat().st_size > 0:
            return {**task, "status": "exists", "size": out.stat().st_size,
                    "elapsed": 0.0, "error": ""}
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(SNAP), str(task["src"]),
               *CONFIGS[task["tech"]], "-o", str(out)]
        run_env = dict(env)
        run_env["ZONE_WRAP_SEED"] = str(task["seed"])
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, cwd=RUNDIR, env=run_env, timeout=args.timeout,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            rc, raw, timed_out = proc.returncode, proc.stdout, False
        except subprocess.TimeoutExpired as exc:
            rc, raw, timed_out = -1, exc.stdout or b"", True
        elapsed = round(time.time() - t0, 2)
        ok = out.exists() and out.stat().st_size > 0
        error = ""
        if not ok:
            text = raw.decode("utf-8", errors="replace") if raw else ""
            error = text[-1500:]
            if out.exists():
                try:
                    out.unlink()
                except OSError:
                    pass
        return {**task, "status": "ok" if ok else "genfail",
                "size": out.stat().st_size if ok else 0,
                "rc": rc, "elapsed": elapsed, "timed_out": timed_out,
                "error": error}

    print(f"[INFO] {len(tasks)} tasks, {args.threads} threads", flush=True)
    counts = {"ok": 0, "exists": 0, "genfail": 0}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [pool.submit(generate, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            record = future.result()
            record["src"] = str(record["src"].relative_to(ROOT))
            record["out"] = str(record["out"].relative_to(ROOT))
            counts[record["status"]] += 1
            with MANIFEST_LOCK:
                with manifest.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            if record["status"] == "genfail":
                print(f"[GENFAIL] {record['payload']}/{record['tech']}"
                      f"/{record['index']}: "
                      f"{record['error'].strip().splitlines()[-1][:200]}",
                      flush=True)
            if done % 25 == 0 or done == len(tasks):
                elapsed = time.time() - t0
                print(f"[{done}/{len(tasks)}] {counts} "
                      f"{done / elapsed:.1f}/s", flush=True)
    print(f"[DONE] {counts} in {time.time() - t0:.1f}s", flush=True)
    return 0 if counts["genfail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
