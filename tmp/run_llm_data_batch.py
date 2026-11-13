#!/usr/bin/env python3
"""Working-rate matrix for LLM data classification (--llm-data).

Cases:
  * x64 MessageBox: classification only (3) and classification + -eq (3)
  * x86 MessageBox: classification only (3)
  * x64 custom_reverse_http: classification only (3)
  * x86 custom_reverse_http: classification only (3)

Each run is independent and resumable.  Outputs go to
mutations_llm_data/<arch>/<name>.bin, the classifier JSON and stats to
tmp/lldata_run/.
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

ROOT = Path(__file__).resolve().parent.parent
RUNDIR = ROOT / "tmp" / "lldata_run"
OUTDIR = ROOT / "mutations_llm_data"
RESULTS = ROOT / "tmp" / "llm_data_results.jsonl"
LOCK = threading.Lock()

CASES = [
    # name, arch, tool, payload, extra flags, verify
    ("windows_x64_messagebox_lldata", "x64", "pobf.py",
     "original_pl/x64/windows_x64_messagebox.bin", [], "messagebox"),
    ("windows_x64_messagebox_lldata_eq", "x64", "pobf.py",
     "original_pl/x64/windows_x64_messagebox.bin", ["-eq"], "messagebox"),
    ("windows_messagebox_lldata", "x86", "pobf86.py",
     "original_pl/x86/windows_messagebox.bin", [], "messagebox"),
    ("windows_x64_custom_reverse_http_lldata", "x64", "pobf.py",
     "original_pl/x64/windows_x64_custom_reverse_http.bin", [], "static"),
    ("windows_custom_reverse_http_lldata", "x86", "pobf86.py",
     "original_pl/x86/windows_custom_reverse_http.bin", [], "static"),
]


def prepare_worker(index: int) -> Path:
    cwd = RUNDIR / f"w{index}"
    cwd.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "instr_payload.txt", "instr_payload2.txt",
                 "data_cache.json"):
        target = cwd / name
        if not target.exists():
            shutil.copy2(ROOT / "tmp" / "wrap_run" / name, target)
    return cwd


def run_one(task: dict, cwd: Path) -> dict:
    name = task["name"]
    out = OUTDIR / task["arch"] / f"{name}.bin"
    stats_path = RUNDIR / "stats" / f"{name}.json"
    data_path = RUNDIR / "data" / f"{name}.json"
    failed_path = RUNDIR / "failed" / f"{name}.asm"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and out.stat().st_size > 0 and stats_path.exists():
        previous = json.loads(stats_path.read_text(encoding="utf-8"))
        if previous.get("ok"):
            return {**task, "status": "exists", "size": out.stat().st_size,
                    "cost_usd": (previous.get("cost_usd") or {}).get("total"),
                    "sections": None, "data_bytes": None,
                    "elapsed": 0.0, "error": ""}

    for path in (out, stats_path, data_path, failed_path):
        if path.exists():
            path.unlink()

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        sys.executable, str(ROOT / task["tool"]), str(ROOT / task["payload"]),
        "--llm-data",
        "--llm-data-json", str(data_path),
        "--llm-stats", str(stats_path),
        "--llm-failed-output", str(failed_path),
        *task["extra"],
        "-o", str(out),
    ]
    if task["verify"] == "messagebox":
        cmd += ["--llm-verify", "messagebox"]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, timeout=3600,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - t0, 1)
    stats = {}
    try:
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    ok = out.exists() and out.stat().st_size > 0 and stats.get("ok") is True
    error = ""
    if not ok:
        text = raw.decode("utf-8", errors="replace") if raw else ""
        error = stats.get("error") or text[-1200:]
    data_summary = None
    try:
        data_summary = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    sections = (data_summary or {}).get("sections") or []
    return {
        **task,
        "status": "ok" if ok else "fail",
        "size": out.stat().st_size if out.exists() else 0,
        "attempts": stats.get("attempts"),
        "cost_usd": (stats.get("cost_usd") or {}).get("total"),
        "sections": len(sections),
        "data_bytes": sum(int(s.get("length", 0)) for s in sections),
        "elapsed": elapsed,
        "timed_out": timed_out,
        "error": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--index", type=int, default=None)
    args = parser.parse_args()

    for sub in ("stats", "data", "failed"):
        (RUNDIR / sub).mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)

    tasks = []
    for case in CASES:
        name, arch, tool, payload, extra, verify = case
        if args.case and name not in args.case:
            continue
        indices = [args.index] if args.index else range(1, args.runs + 1)
        for index in indices:
            tasks.append({
                "name": f"{name}_{index}", "arch": arch, "tool": tool,
                "payload": payload, "extra": extra, "verify": verify,
                "index": index,
            })

    workers = min(args.workers, max(1, len(tasks)))
    cwds = [prepare_worker(i) for i in range(workers)]
    schedule = [[] for _ in range(workers)]
    for position, task in enumerate(tasks):
        schedule[position % workers].append(task)

    print(f"[INFO] {len(tasks)} runs, {workers} workers", flush=True)
    counts = {"ok": 0, "exists": 0, "fail": 0}
    total_cost = 0.0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, task, cwds[worker])
                   for worker, worker_tasks in enumerate(schedule)
                   for task in worker_tasks]
        for done, future in enumerate(as_completed(futures), 1):
            record = future.result()
            counts[record["status"]] += 1
            total_cost += record.get("cost_usd") or 0.0
            with LOCK:
                with RESULTS.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            print(f"[{done}/{len(tasks)}] {record['name']} "
                  f"{record['status']} size={record['size']} "
                  f"sections={record['sections']} "
                  f"bytes={record['data_bytes']} "
                  f"cost=${record.get('cost_usd') or 0:.4f} "
                  f"{record['elapsed']}s", flush=True)
    print(f"[DONE] {counts} cost=${total_cost:.4f} "
          f"in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0 if counts["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
