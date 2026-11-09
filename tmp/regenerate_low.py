#!/usr/bin/env python3
"""Regenerate low-working-rate payloads with -xd -ebi (fallback -xd).

For every selected payload and every one of the 15 technique configurations,
produce 10 independent mutants.  Resumable: existing non-empty outputs are
skipped.  A JSONL manifest records exactly which flags produced each file.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, "tmp")
import work_rate_data as W

ROOT = Path.cwd()
LOCAL_CAPSTONE = ROOT / "tmp" / "capstone506"
MANIFEST_LOCK = threading.Lock()


def load_low(path):
    data = json.load(open(path, encoding="utf-8"))
    return data["payloads"]


def build_tasks(rows, outdir, per_tech, payload_filter, tech_filter, arch_filter):
    tasks = []
    for r in rows:
        arch, base = r["arch"], r["payload"]
        if arch_filter and arch != arch_filter:
            continue
        if payload_filter and base not in payload_filter:
            continue
        src = ROOT / "original_pl" / arch / f"{base}.bin"
        if not src.exists():
            print(f"[MISSING] {src}")
            continue
        for tech in W.ALL_TECHS:
            if tech_filter and tech not in tech_filter:
                continue
            for i in range(1, per_tech + 1):
                out = ROOT / outdir / arch / f"{base}_{tech}_{i}.bin"
                tasks.append({
                    "arch": arch, "payload": base, "tech": tech, "index": i,
                    "src": src, "out": out,
                })
    return tasks


def run_cmd(cmd, env, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd, cwd=ROOT, env=env, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        return p.returncode, p.stdout, time.time() - t0, False
    except subprocess.TimeoutExpired as e:
        out = e.stdout or b""
        return -1, out, time.time() - t0, True


def generate(task, env, timeout):
    out = task["out"]
    if out.exists() and out.stat().st_size > 0:
        return {**{k: task[k] for k in ("arch", "payload", "tech", "index")},
                "status": "exists", "output": str(out.relative_to(ROOT)),
                "flags": None, "rc": 0, "size": out.stat().st_size,
                "elapsed": 0.0, "error": ""}

    arch = task["arch"]
    tool = "pobf.py" if arch == "x64" else "pobf86.py"
    primary = W.flags_for(task["tech"])
    if task["tech"] == "xd_ebi":
        flag_sets = [(primary, "xd_ebi"), (["-xd"], "xd")]
    elif task["tech"] == "xd":
        flag_sets = [(primary, "xd")]
    else:
        flag_sets = [(primary, "xd_ebi"), (["-xd"] + W.TECH_FLAGS[task["tech"]], "xd")]
    last = None
    for flags, label in flag_sets:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            try:
                out.unlink()
            except OSError:
                pass
        cmd = [sys.executable, tool, str(task["src"])] + flags + ["-o", str(out)]
        rc, raw, dt, timed_out = run_cmd(cmd, env, timeout)
        ok = out.exists() and out.stat().st_size > 0
        if ok:
            return {**{k: task[k] for k in ("arch", "payload", "tech", "index")},
                    "status": "ok", "output": str(out.relative_to(ROOT)),
                    "flags": label, "rc": rc, "size": out.stat().st_size,
                    "elapsed": round(dt, 2), "error": ""}
        err = raw.decode("utf-8", errors="replace")[-2000:] if raw else ""
        last = {"status": "genfail", "output": str(out.relative_to(ROOT)),
                "flags": label, "rc": rc, "size": 0,
                "elapsed": round(dt, 2), "error": err,
                "timed_out": timed_out}
    return {**{k: task[k] for k in ("arch", "payload", "tech", "index")}, **last}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="tmp/low_payloads.json")
    ap.add_argument("--outdir", default="mutations_new_xd_ebi")
    ap.add_argument("--per-tech", type=int, default=10)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--payload", action="append", default=None,
                    help="only this payload (repeatable)")
    ap.add_argument("--tech", action="append", default=None,
                    help="only this technique (repeatable)")
    ap.add_argument("--arch", choices=["x64", "x86", "both"], default="both")
    args = ap.parse_args()

    rows = load_low(args.list)
    arch_filter = None if args.arch == "both" else args.arch
    tasks = build_tasks(rows, args.outdir, args.per_tech,
                        set(args.payload) if args.payload else None,
                        set(args.tech) if args.tech else None,
                        arch_filter)
    manifest = ROOT / args.outdir / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(LOCAL_CAPSTONE)
    print(f"[INFO] {len(tasks)} tasks, {args.threads} threads, "
          f"out={args.outdir}", flush=True)

    counts = {"ok": 0, "exists": 0, "genfail": 0}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futs = [pool.submit(generate, t, env, args.timeout) for t in tasks]
        for n, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
            with MANIFEST_LOCK:
                with manifest.open("a", encoding="utf-8") as mf:
                    mf.write(json.dumps(rec) + "\n")
            if rec["status"] == "genfail":
                print(f"[GENFAIL] {rec['arch']}/{rec['payload']}_"
                      f"{rec['tech']}_{rec['index']} rc={rec['rc']} "
                      f"{rec['error'][-300:]}", flush=True)
            if n % 100 == 0 or n == len(tasks):
                el = time.time() - t0
                print(f"[{n}/{len(tasks)}] ok={counts['ok']} "
                      f"exists={counts['exists']} fail={counts['genfail']} "
                      f"{n/el:.1f}/s ETA {(len(tasks)-n)/(n/el)/60:.1f} min",
                      flush=True)
    print(f"[DONE] {counts} in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
