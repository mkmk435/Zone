#!/usr/bin/env python3
"""Compare symbolic/heuristic data handling (-xd) with LLM data classification
(--llm-data) on the payloads where the symbolic layer finds movable data.

For each input:
  * symbolic arm: reuse the prewarm -xd output and its measured analysis time;
  * LLM arm: one --llm-data run, with classification JSON, time and cost.

Both arms are then executed through the functional harness.  Section agreement
is reported as exact interval-set equality between the LLM ranges that survived
the deterministic filters and the symbolic ranges.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
RUN = BASE / "run"
OUT = ROOT / "mutations_all" / "lldata"
STATS = BASE / "lldata_stats"
RESULTS = BASE / "llm_data_build.jsonl"
WORKERS = 2
TIMEOUT = 1800
LOCK = threading.Lock()

DATA_RE = re.compile(r"\[extract\] data 0x([0-9a-f]+) -> 0x([0-9a-f]+) \((\d+) B\)")


def api_key() -> str:
    return (ROOT / "dsk.txt").read_text(encoding="utf-8").strip()


def prepare(index: int) -> Path:
    cwd = RUN / f"data_w{index}"
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


def symbolic_rows():
    rows = []
    for line in (BASE / "prewarm_xd.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        sections = []
        for text in row["data_lines"]:
            match = DATA_RE.search(text)
            if match:
                sections.append({"src": int(match.group(1), 16),
                                 "dst": int(match.group(2), 16),
                                 "length": int(match.group(3))})
        if sections:
            rows.append({"arch": row["arch"], "payload": row["payload"],
                         "sections": sections,
                         "analysis_s": row["elapsed_s"],
                         "symbolic_out": f"tmp/campaign/prewarm/{row['arch']}/{row['payload']}.bin"})
    return rows


def run_one(task: dict, cwd: Path) -> dict:
    arch, name = task["arch"], task["payload"]
    engine = ENGINE / ("pobf.py" if arch == "x64" else "pobf86.py")
    src = ROOT / "original_pl" / arch / f"{name}.bin"
    out = OUT / arch / f"{name}_lldata.bin"
    stats = STATS / arch / f"{name}_lldata.json"
    classify = STATS / arch / f"{name}_lldata_ranges.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    stats.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8",
               ZONE_LLM_API_KEY=api_key())
    cmd = [sys.executable, str(engine), str(src), "--llm-data",
           "--llm-stats", str(stats), "--llm-data-json", str(classify),
           "-o", str(out)]
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, timeout=TIMEOUT,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc, raw, timed_out = proc.returncode, proc.stdout, False
    except subprocess.TimeoutExpired as exc:
        rc, raw, timed_out = -1, exc.stdout or b"", True
    elapsed = round(time.time() - started, 2)
    text = raw.decode("utf-8", errors="replace") if raw else ""
    data = {}
    if stats.exists():
        try:
            data = json.loads(stats.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    ranges = []
    if classify.exists():
        try:
            payload = json.loads(classify.read_text(encoding="utf-8"))
            ranges = payload.get("sections") or payload.get("ranges") or []
        except ValueError:
            ranges = []
    return {
        "arch": arch, "payload": name, "src": str(src.relative_to(ROOT)),
        "out": str(out.relative_to(ROOT)),
        "status": "ok" if out.exists() and out.stat().st_size else "fail",
        "size": out.stat().st_size if out.exists() else 0,
        "sha256": __import__("hashlib").sha256(out.read_bytes()).hexdigest()
        if out.exists() else "",
        "elapsed_s": elapsed, "timed_out": timed_out, "rc": rc,
        "api_calls": data.get("api_calls"), "attempts": data.get("attempts"),
        "cost_usd": (data.get("cost_usd") or {}).get("total"),
        "tokens": (data.get("usage") or {}).get("total_tokens"),
        "llm_ranges": ranges,
        "error": "" if out.exists() else text[-1500:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=WORKERS)
    args = parser.parse_args()
    tasks = symbolic_rows()
    done = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["status"] == "ok":
                done.add((row["arch"], row["payload"]))
    pending = [task for task in tasks if (task["arch"], task["payload"]) not in done]
    print(f"[INFO] {len(pending)} pending of {len(tasks)} data-bearing payloads",
          flush=True)
    cwds = [prepare(index) for index in range(args.workers)]
    schedule = [[] for _ in range(args.workers)]
    for position, task in enumerate(pending):
        schedule[position % args.workers].append(task)
    started = time.time()
    counts = {"ok": 0, "fail": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
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
                  f"{record['size']}B ${record.get('cost_usd') or 0:.4f} "
                  f"{record['elapsed_s']}s", flush=True)
    print(f"[DONE] {counts} in {(time.time() - started) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
