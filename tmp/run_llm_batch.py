#!/usr/bin/env python3
"""Run the LLM-morphing matrix: 4 techniques x {0,2} shots x 3 mutations.

Every run is a separate DeepSeek call on the x64 MessageBox payload, verified by
executing the result and waiting for the dialog (--llm-verify messagebox).
The engine is pinned to tmp/wrap_snapshot so live edits cannot change the
experiment.  Results are resumable: a run with ok output and ok stats is kept.

Outputs: mutations_llm/x64/windows_x64_messagebox_llm_<tech>_s<shots>_<i>.bin
Stats:   tmp/llm_run/stats/<name>.json
Log:     tmp/llm_batch_results.jsonl
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

import argparse

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "tmp" / "wrap_snapshot" / "pobf.py"
PAYLOAD = ROOT / "original_pl" / "x64" / "windows_x64_messagebox.bin"
OUTDIR = ROOT / "mutations_llm" / "x64"
RUNDIR = ROOT / "tmp" / "llm_run"
STATS = RUNDIR / "stats"
FAILED = RUNDIR / "failed"
RESULTS = ROOT / "tmp" / "llm_batch_results.jsonl"

TECHS = ["eq", "nop", "bcf", "ibp"]
SHOTS = [0, 2]
MUTATIONS = 3
WORKERS = 3

LOCK = threading.Lock()


def prepare_worker(index: int) -> Path:
    cwd = RUNDIR / f"w{index}"
    cwd.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "instr_payload.txt", "instr_payload2.txt",
                 "data_cache.json"):
        target = cwd / name
        if not target.exists():
            shutil.copy2(ROOT / "tmp" / "wrap_run" / name, target)
    return cwd


def read_stats(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def run_one(task: dict, worker_cwd: Path) -> dict:
    name = task["name"]
    out = OUTDIR / f"{name}.bin"
    stats_path = STATS / f"{name}.json"
    failed_path = FAILED / f"{name}.asm"

    previous = read_stats(stats_path)
    if out.exists() and out.stat().st_size > 0 and previous and previous.get("ok"):
        return {**task, "status": "exists", "size": out.stat().st_size,
                "attempts": previous.get("attempts"),
                "cost_usd": (previous.get("cost_usd") or {}).get("total"),
                "elapsed": 0.0, "error": ""}

    for path in (out, stats_path, failed_path):
        if path.exists():
            path.unlink()

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        sys.executable, str(SNAP), str(PAYLOAD),
        "--llm", f"-{task['tech']}",
        "--llm-shots", str(task["shots"]),
        "--llm-verify", "messagebox",
        "--llm-retries", "3",
        "--llm-stats", str(stats_path),
        "--llm-failed-output", str(failed_path),
        "-o", str(out),
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=worker_cwd, env=env, timeout=3600,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - t0, 1)
    stats = read_stats(stats_path) or {}
    ok = (out.exists() and out.stat().st_size > 0 and stats.get("ok") is True)
    error = ""
    if not ok:
        text = raw.decode("utf-8", errors="replace") if raw else ""
        error = (stats.get("error") or text[-1200:])
    return {
        **task,
        "status": "ok" if ok else "fail",
        "size": out.stat().st_size if out.exists() else 0,
        "attempts": stats.get("attempts"),
        "api_calls": stats.get("api_calls"),
        "cost_usd": (stats.get("cost_usd") or {}).get("total"),
        "tokens": (stats.get("usage") or {}).get("total_tokens"),
        "similarity": next((a.get("similarity")
                            for a in reversed(stats.get("attempt_details", []))
                            if a.get("accepted")), None),
        "elapsed": elapsed,
        "timed_out": timed_out,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tech", action="append", default=None)
    parser.add_argument("--shots", type=int, action="append", default=None)
    parser.add_argument("--mutations", type=int, default=MUTATIONS)
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args()
    techs = args.tech or TECHS
    shots_list = args.shots if args.shots is not None else SHOTS
    workers = args.workers

    OUTDIR.mkdir(parents=True, exist_ok=True)
    STATS.mkdir(parents=True, exist_ok=True)
    FAILED.mkdir(parents=True, exist_ok=True)

    tasks = []
    for tech in techs:
        for shots in shots_list:
            for index in range(1, args.mutations + 1):
                tasks.append({
                    "name": f"windows_x64_messagebox_llm_{tech}_s{shots}_{index}",
                    "tech": tech, "shots": shots, "index": index,
                })

    # only one worker owns a given cwd at a time; simple round-robin list
    cwds = [prepare_worker(i) for i in range(workers)]
    schedule = [[] for _ in range(workers)]
    for position, task in enumerate(tasks):
        schedule[position % workers].append(task)

    print(f"[INFO] {len(tasks)} runs, {workers} workers", flush=True)
    counts = {"ok": 0, "exists": 0, "fail": 0}
    total_cost = 0.0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for worker, worker_tasks in enumerate(schedule):
            for task in worker_tasks:
                future = pool.submit(run_one, task, cwds[worker])
                futures[future] = task
        done = 0
        for future in as_completed(futures):
            record = future.result()
            done += 1
            counts[record["status"]] += 1
            total_cost += record.get("cost_usd") or 0.0
            with LOCK:
                with RESULTS.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            print(f"[{done}/{len(tasks)}] {record['name']} "
                  f"{record['status']} size={record['size']} "
                  f"attempts={record['attempts']} "
                  f"cost=${record.get('cost_usd') or 0:.4f} "
                  f"{record['elapsed']}s", flush=True)
    print(f"[DONE] {counts} cost=${total_cost:.4f} "
          f"in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
