#!/usr/bin/env python3
"""Regenerate mutations for selected payloads with -xd -ebi (+ technique flags)."""
import argparse, os, subprocess, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TECHS = [
    ("eq", ["-eq"]),
    ("bcf", ["-bcf"]),
    ("nop", ["-nop"]),
    ("ibp", ["-ibp"]),
    ("pii", ["-pii"]),
    ("eq_nop_pii", ["-eq", "-nop", "-pii"]),
    ("eq_nop_bcf", ["-eq", "-nop", "-bcf"]),
    ("eq_nop_ibp", ["-eq", "-nop", "-ibp"]),
    ("nop_eq", ["-nop", "-eq"]),
    ("nop_pii", ["-nop", "-pii"]),
    ("nop_bcf", ["-nop", "-bcf"]),
    ("nop_ibp", ["-nop", "-ibp"]),
    ("eq_pii", ["-eq", "-pii"]),
    ("eq_bcf", ["-eq", "-bcf"]),
    ("eq_ibp", ["-eq", "-ibp"]),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payloads", nargs="+", required=True)
    ap.add_argument("--arch", default="x64")
    ap.add_argument("--per-tech", type=int, default=10)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--outdir", default="mutations_fixed")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--capstone", choices=["local", "system"], default="local")
    args = ap.parse_args()

    root = Path.cwd()
    outdir = root / args.outdir / args.arch
    outdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if args.capstone == "local":
        env["PYTHONPATH"] = str(root / "tmp" / "capstone506")
    else:
        env.pop("PYTHONPATH", None)

    tasks = []
    for name in args.payloads:
        base = name.removesuffix(".bin")
        src = root / "original_pl" / args.arch / f"{base}.bin"
        if not src.exists():
            print(f"[MISSING] {src}")
            continue
        for label, flags in TECHS:
            for i in range(1, args.per_tech + 1):
                out = outdir / f"{base}_{label}_{i}.bin"
                if out.exists():
                    continue
                tasks.append((src, flags, out))

    print(f"[INFO] {len(tasks)} mutations to generate", flush=True)

    def run(task):
        src, flags, out = task
        cmd = [sys.executable, "pobf.py", str(src), "-xd", "-ebi", *flags, "-o", str(out)]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=root, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        dt = time.time() - t0
        exists = out.exists()
        err = p.stderr.decode(errors="replace")
        fatal = (not exists) or p.returncode != 0
        return (out, exists, dt, p.returncode, fatal, err[-300:])

    ok = 0
    bad = 0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futs = [pool.submit(run, t) for t in tasks]
        for n, f in enumerate(as_completed(futs), 1):
            out, exists, dt, rc, fatal, err = f.result()
            if exists and not fatal:
                ok += 1
            else:
                bad += 1
                print(f"[FAIL] {out.name} rc={rc} exists={exists} {dt:.1f}s\n{err}", flush=True)
            if n % 25 == 0:
                print(f"[PROGRESS] {n}/{len(tasks)} ok={ok} bad={bad}", flush=True)
    print(f"[DONE] ok={ok} bad={bad}", flush=True)

if __name__ == "__main__":
    main()
