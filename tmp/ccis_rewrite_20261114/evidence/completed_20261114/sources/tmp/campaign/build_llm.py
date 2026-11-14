#!/usr/bin/env python3
"""LLM-morphing matrix: 102 payloads x 4 techniques x {0,2} shots, one output
per cell.

Every run is one DeepSeek generation (retries inside the engine up to 3).  The
output is validated statically by the engine; functional verification is done
afterwards by the external harness, not by the generator, so the pass rate is
not conditional on a built-in dialog check.

Resumable through ``llm_build.jsonl``.  A cost ceiling stops new tasks when the
recorded API cost reaches ``--max-cost``.
"""
from __future__ import annotations

import argparse
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
OUT = ROOT / "mutations_all" / "llm"
STATS = BASE / "llm_stats"
RUN = BASE / "run"
RESULTS = BASE / "llm_build.jsonl"
TECHS = ["eq", "nop", "bcf", "ibp"]
SHOTS = [0, 2]
WORKERS = 6
TIMEOUT = 3600
LOCK = threading.Lock()
STOP = threading.Event()
RETRIES = 3


def api_key() -> str:
    return (ROOT / "dsk.txt").read_text(encoding="utf-8").strip()


def prepare(index: int) -> Path:
    cwd = RUN / f"llm_w{index}"
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


def key_of(task: dict) -> str:
    return f"{task['arch']}/{task['payload']}/{task['tech']}/{task['shots']}"


def run_one(task: dict, cwd: Path) -> dict:
    arch, name, tech, shots = (task["arch"], task["payload"],
                              task["tech"], task["shots"])
    engine = ENGINE / ("pobf.py" if arch == "x64" else "pobf86.py")
    out = OUT / arch / f"{name}_llm_{tech}_s{shots}.bin"
    stats = STATS / arch / f"{name}_llm_{tech}_s{shots}.json"
    failed = STATS / arch / f"{name}_llm_{tech}_s{shots}.failed.asm"
    out.parent.mkdir(parents=True, exist_ok=True)
    stats.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8",
               ZONE_LLM_API_KEY=api_key())
    cmd = [
        sys.executable, str(engine), str(task["src"]),
        "--llm", f"-{tech}", "--llm-shots", str(shots),
        "--llm-retries", str(RETRIES), "--llm-max-tokens", "65536",
        "--llm-stats", str(stats), "--llm-failed-output", str(failed),
        "-o", str(out),
    ]
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, timeout=TIMEOUT,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - started, 1)
    text = raw.decode("utf-8", errors="replace") if raw else ""
    data = {}
    if stats.exists():
        try:
            data = json.loads(stats.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    ok = bool(out.exists() and out.stat().st_size and data.get("ok"))
    return {
        "arch": arch, "payload": name, "tech": tech, "shots": shots,
        "src": str(task["src"]), "out": str(out.relative_to(ROOT)),
        "status": "ok" if ok else "fail",
        "size": out.stat().st_size if out.exists() else 0,
        "sha256": __import__("hashlib").sha256(out.read_bytes()).hexdigest()
        if out.exists() else "",
        "elapsed_s": elapsed, "rc": rc, "timed_out": timed_out,
        "api_calls": data.get("api_calls"),
        "attempts": data.get("attempts"),
        "cost_usd": (data.get("cost_usd") or {}).get("total"),
        "tokens": (data.get("usage") or {}).get("total_tokens"),
        "similarity": next((a.get("similarity") for a in reversed(
            data.get("attempt_details", [])) if a.get("accepted")), None),
        "error": "" if ok else (data.get("error") or text[-1500:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cost", type=float, default=28.0)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--tech", action="append", default=None)
    parser.add_argument("--shots", type=int, action="append", default=None)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    global RETRIES
    RETRIES = args.retries
    techs = args.tech or TECHS
    shots_list = args.shots if args.shots is not None else SHOTS

    tasks = []
    for arch in ("x64", "x86"):
        for src in sorted((ROOT / "original_pl" / arch).glob("*.bin")):
            for tech in techs:
                for shots in shots_list:
                    tasks.append({"arch": arch, "payload": src.stem,
                                  "tech": tech, "shots": shots, "src": src})
    done = set()
    spent = 0.0
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            spent += row.get("cost_usd") or 0.0
            if row["status"] == "ok":
                done.add(key_of(row))
    pending = [task for task in tasks if key_of(task) not in done]
    print(f"[INFO] {len(pending)} pending of {len(tasks)}, already ${spent:.2f}",
          flush=True)

    cwds = [prepare(index) for index in range(args.workers)]
    schedule = [[] for _ in range(args.workers)]
    for position, task in enumerate(pending):
        schedule[position % args.workers].append(task)

    def guarded(task: dict, cwd: Path) -> dict:
        if STOP.is_set():
            return {**task, "status": "skipped", "size": 0, "sha256": "",
                    "elapsed_s": 0, "cost_usd": 0.0, "api_calls": 0,
                    "attempts": 0, "tokens": 0, "similarity": None,
                    "out": "", "src": str(task["src"]),
                    "error": "cost ceiling reached"}
        return run_one(task, cwd)

    started = time.time()
    counts = {"ok": 0, "fail": 0, "skipped": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for index, worker_tasks in enumerate(schedule):
            for task in worker_tasks:
                futures[pool.submit(guarded, task, cwds[index])] = task
        for position, future in enumerate(as_completed(futures), 1):
            record = future.result()
            counts[record["status"]] += 1
            spent += record.get("cost_usd") or 0.0
            with LOCK:
                with RESULTS.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            if spent >= args.max_cost and not STOP.is_set():
                STOP.set()
                print(f"[STOP] cost ceiling ${args.max_cost:.2f} reached",
                      flush=True)
            print(f"[{position}/{len(pending)}] {record['arch']} "
                  f"{record['payload']} {record['tech']} s{record['shots']} "
                  f"{record['status']} {record['size']}B "
                  f"${record.get('cost_usd') or 0:.4f} "
                  f"{record['elapsed_s']}s", flush=True)
    print(f"[DONE] {counts} spent=${spent:.4f} "
          f"in {(time.time() - started) / 3600:.2f} h", flush=True)
    return 0 if counts["fail"] == 0 and counts["skipped"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
