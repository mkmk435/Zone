#!/usr/bin/env python3
"""Build the assembly-wrapping matrix: 102 payloads x 3 seeds, -xd -wrap only.

One technique per output (no combined techniques).  ``-xd`` is preprocessing,
not a morphing technique.  The seed fixes the layout, so three seeds give three
independent variants per payload.  Results are resumable through
``wrap_build.jsonl``.
"""
from __future__ import annotations

import hashlib
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
OUT = ROOT / "mutations_all" / "wrap"
RUN = BASE / "run"
RESULTS = BASE / "wrap_build.jsonl"
SEEDS = [101, 102, 103]
WORKERS = 4
TIMEOUT = 1200
LOCK = threading.Lock()


def prepare(index: int) -> Path:
    cwd = RUN / f"wrap_w{index}"
    cwd.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "instr_payload.txt", "instr_payload2.txt",
                 "blocks.txt", "jump_table.txt"):
        target = cwd / name
        if not target.exists():
            shutil.copy2(ROOT / name, target)
    cache = RUN / "data_cache.json"
    if cache.exists():
        shutil.copy2(cache, cwd / "data_cache.json")
    return cwd


def task_key(task: dict) -> str:
    return f"{task['arch']}/{task['payload']}/s{task['seed']}"


def run_one(task: dict, cwd: Path) -> dict:
    arch, name, seed = task["arch"], task["payload"], task["seed"]
    engine = ENGINE / ("pobf.py" if arch == "x64" else "pobf86.py")
    out = OUT / arch / f"{name}_wrap_s{seed}.bin"
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", ZONE_WRAP_SEED=str(seed))
    started = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(engine), str(task["src"]),
             "-xd", "-wrap", "-o", str(out)],
            cwd=cwd, env=env, timeout=TIMEOUT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - started, 2)
    ok = out.exists() and out.stat().st_size > 0
    text = raw.decode("utf-8", errors="replace") if raw else ""
    digest = hashlib.sha256(out.read_bytes()).hexdigest() if ok else ""
    wrap_line = next((line for line in reversed(text.splitlines())
                      if line.startswith("[wrap]")), "")
    return {
        "arch": arch, "payload": name, "seed": seed,
        "src": str(task["src"]),
        "out": str(out.relative_to(ROOT)),
        "status": "ok" if ok else "genfail",
        "size": out.stat().st_size if ok else 0,
        "sha256": digest,
        "elapsed_s": elapsed, "rc": rc, "timed_out": timed_out,
        "wrap_line": wrap_line,
        "error": "" if ok else text[-1800:],
    }


def main() -> int:
    tasks = []
    for arch in ("x64", "x86"):
        for src in sorted((ROOT / "original_pl" / arch).glob("*.bin")):
            for seed in SEEDS:
                tasks.append({"arch": arch, "payload": src.stem, "seed": seed,
                              "src": src})
    done = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["status"] == "ok":
                done.add(task_key(row))
    pending = [task for task in tasks if task_key(task) not in done]
    print(f"[INFO] {len(pending)} pending of {len(tasks)}", flush=True)
    cwds = [prepare(index) for index in range(WORKERS)]
    schedule = [[] for _ in range(WORKERS)]
    for position, task in enumerate(pending):
        schedule[position % WORKERS].append(task)
    started = time.time()
    counts = {"ok": 0, "genfail": 0}
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
            mark = "OK" if record["status"] == "ok" else "GENFAIL"
            print(f"[{position}/{len(pending)}] {record['arch']} "
                  f"{record['payload']} s{record['seed']} {mark} "
                  f"{record['size']}B {record['elapsed_s']}s", flush=True)
    print(f"[DONE] {counts} in {(time.time() - started) / 60:.1f} min", flush=True)
    return 0 if counts["genfail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
