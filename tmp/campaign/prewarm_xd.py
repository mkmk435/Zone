#!/usr/bin/env python3
"""Prewarm the symbolic data cache for every original payload.

Runs `-xd` once per payload with four isolated worker directories, keeps the
per-worker data caches, and merges them at the end.  The output of every run is
kept in ``tmp/campaign/prewarm``.  Resumable through ``prewarm_xd.jsonl``.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "bench" / "engines" / "2026-11-13_block3"
BASE = Path(__file__).resolve().parent
OUT = BASE / "prewarm"
RUN = BASE / "run"
RESULTS = BASE / "prewarm_xd.jsonl"
WORKERS = 4
TIMEOUT = 900
LOCK = threading.Lock()


def prepare(index: int) -> Path:
    cwd = RUN / f"w{index}"
    cwd.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "instr_payload.txt", "instr_payload2.txt",
                 "blocks.txt", "jump_table.txt"):
        target = cwd / name
        if not target.exists():
            shutil.copy2(ROOT / name, target)
    if not (cwd / "data_cache.json").exists():
        (cwd / "data_cache.json").write_text("{}\n", encoding="utf-8")
    return cwd


def run_one(task: dict, cwd: Path) -> dict:
    arch, name, src = task["arch"], task["payload"], task["src"]
    engine = ENGINE / ("pobf.py" if arch == "x64" else "pobf86.py")
    out = OUT / arch / f"{name}.bin"
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    started = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(engine), str(src), "-xd", "-o", str(out)],
            cwd=cwd, env=env, timeout=TIMEOUT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - started, 2)
    text = raw.decode("utf-8", errors="replace") if raw else ""
    ok = out.exists() and out.stat().st_size > 0
    return {
        "arch": arch, "payload": name, "src": str(src),
        "status": "ok" if ok else "fail",
        "size": out.stat().st_size if ok else 0,
        "elapsed_s": elapsed, "rc": rc, "timed_out": timed_out,
        "data_lines": [line for line in text.splitlines()
                       if line.startswith("[extract] data") or
                       line.startswith("[extract] ref") or
                       line.startswith("[extract] no ")],
        "error": "" if ok else text[-1500:],
    }


def main() -> int:
    tasks = []
    for arch in ("x64", "x86"):
        for src in sorted((ROOT / "original_pl" / arch).glob("*.bin")):
            tasks.append({"arch": arch, "payload": src.stem, "src": src})
    done = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done.add((row["arch"], row["payload"]))
    pending = [task for task in tasks if (task["arch"], task["payload"]) not in done]
    print(f"[INFO] {len(pending)} pending of {len(tasks)}", flush=True)
    cwds = [prepare(index) for index in range(WORKERS)]
    schedule = [[] for _ in range(WORKERS)]
    for position, task in enumerate(pending):
        schedule[position % WORKERS].append(task)
    started = time.time()
    counts = {"ok": 0, "fail": 0}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {}
        for index, worker_tasks in enumerate(schedule):
            for task in worker_tasks:
                futures[pool.submit(run_one, task, cwds[index])] = task
        for position, future in enumerate(as_completed(futures), 1):
            record = future.result()
            counts[record["status"]] += 1
            with LOCK:
                with RESULTS.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            print(f"[{position}/{len(pending)}] {record['arch']} "
                  f"{record['payload']} {record['status']} "
                  f"{record['size']}B {record['elapsed_s']}s", flush=True)
    print(f"[DONE] {counts} in {(time.time() - started) / 60:.1f} min", flush=True)

    merged = {}
    for cwd in cwds:
        cache = cwd / "data_cache.json"
        if cache.exists():
            try:
                merged.update(json.loads(cache.read_text(encoding="utf-8")))
            except ValueError:
                pass
    target = RUN / "data_cache.json"
    target.write_text(json.dumps(merged, indent=1), encoding="utf-8")
    print(f"[CACHE] {len(merged)} entries -> {target}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
