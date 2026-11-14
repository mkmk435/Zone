#!/usr/bin/env python3
"""LLM morphing matrix on the benign corpus.

Design fixed before running:
  * one technique per run (eq, nop, bcf, ibp);
  * 0-shot vs 2-shot on the same cases;
  * at most 3 generation calls per cell (case x technique x shot), retries
    included: --llm-retries 1, and exactly 3 separate invocations;
  * failures, rejected outputs, duplicates and costs are recorded; a failed
    call is not replaced with an easier case.

Usage:
    python bench/run_llm.py --engine bench/engines/2026-11-13_block1
"""
from __future__ import annotations

import argparse
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

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness" / "bin"
CASES = ["arith", "branch", "call", "getpc"]
TECHNIQUES = ["eq", "nop", "bcf", "ibp"]
SHOTS = [0, 2]
CALLS = 3
LOCK = threading.Lock()
STOP = threading.Event()
SPENT = {"value": 0.0}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_buffer(case: dict) -> bytearray:
    buffer = bytearray(b"\xCC" * 256)
    for entry in case["expect"]:
        data = bytes.fromhex(entry["bytes"])
        buffer[entry["offset"]:entry["offset"] + len(data)] = data
    return buffer


def run_payload(arch: str, payload: Path, output: Path):
    runner = HARNESS / f"runner_{arch}.exe"
    try:
        result = subprocess.run([str(runner), str(payload), str(output)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=30)
    except subprocess.TimeoutExpired:
        return False, None
    if result.returncode != 0 or not output.exists():
        return False, None
    text = output.read_text().strip()
    if not text:
        return False, None
    return True, bytes(int(value, 16) for value in text.split(","))


def prepare_dir(directory: Path, engine: Path, cache: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "blocks.txt", "jump_table.txt"):
        shutil.copy2(engine / name, directory / name)
    for name in ("instr_payload.txt", "instr_payload2.txt"):
        (directory / name).write_text("", encoding="utf-8")
    if cache.exists():
        shutil.copy2(cache, directory / "data_cache.json")
    else:
        (directory / "data_cache.json").write_text("{}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--arch", choices=["x64", "x86"], default="x64")
    parser.add_argument("--threads", type=int, default=3)
    parser.add_argument("--out", default=None)
    parser.add_argument("--cells", default=None,
                        help="optional JSON list of [case, technique, shots]")
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--tech", action="append", default=None)
    parser.add_argument("--shots", type=int, action="append", default=None)
    parser.add_argument("--calls", type=int, default=CALLS)
    parser.add_argument("--max-cost", type=float, default=1.0,
                        help="stop issuing calls once the recorded cost "
                             "exceeds this value")
    args = parser.parse_args()

    engine = ROOT / args.engine
    arch = args.arch
    tool = "pobf.py" if arch == "x64" else "pobf86.py"
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("[ERROR] DEEPSEEK_API_KEY is not set")
        return 2
    cases = {case["name"]: case for case in json.loads(
        (HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))
        if case["arch"] == arch}

    run_dir = ROOT / "bench" / "run"
    out_path = ROOT / (args.out or f"bench/results/llm_attempts_{arch}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cache = run_dir / ("prewarm" if arch == "x64" else "prewarm_x86") / \
        "data_cache.json"

    cells = [(name, technique, shots)
             for name in (args.case or list(cases))
             for technique in (args.tech or TECHNIQUES)
             for shots in (args.shots if args.shots is not None else SHOTS)]
    existing = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            existing.add((record["case"], record["technique"],
                          record["shots"], record["call"]))

    tasks = []
    for case, technique, shots in cells:
        for call in range(1, args.calls + 1):
            if (case, technique, shots, call) in existing:
                continue
            tasks.append({"case": case, "technique": technique,
                          "shots": shots, "call": call})
    print(f"[INFO] {len(tasks)} LLM calls, {args.threads} workers",
          flush=True)
    if not tasks:
        return 0

    worker_dirs: dict[int, Path] = {}

    def worker_dir() -> Path:
        ident = threading.get_ident()
        with LOCK:
            if ident not in worker_dirs:
                index = len(worker_dirs)
                directory = run_dir / f"llm_w{index}"
                prepare_dir(directory, engine, cache)
                worker_dirs[ident] = directory
        return worker_dirs[ident]

    def execute(task: dict) -> dict:
        case_name = task["case"]
        technique = task["technique"]
        shots = task["shots"]
        call = task["call"]
        if STOP.is_set():
            return {
                "arch": arch, "case": case_name, "technique": technique,
                "shots": shots, "call": call, "rc": None, "build_ok": False,
                "size": 0, "sha256": None, "exec_ok": False, "match": False,
                "generation_calls": 0, "attempts": 0, "tokens": 0,
                "cost_usd": 0.0, "elapsed": 0.0, "timed_out": False,
                "log": None, "stats": None, "failed_output": None,
                "budget_skipped": True, "error": "budget exhausted",
            }
        case = cases[case_name]
        stem = f"{arch}_{case_name}_{technique}_s{shots}_{call}"
        output = run_dir / "llm_outputs" / f"{stem}.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        stats_path = run_dir / "llm_stats" / f"{stem}.json"
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        failed_path = run_dir / "llm_failed" / f"{stem}.asm"
        failed_path.parent.mkdir(parents=True, exist_ok=True)
        log = ROOT / "bench" / "logs" / "llm" / f"{stem}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        for path in (output, stats_path, failed_path):
            if path.exists():
                path.unlink()

        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   DEEPSEEK_API_KEY=key)
        command = [
            sys.executable, str(engine / tool),
            str(ROOT / case["file"]),
            "--llm", f"-{technique}",
            "--llm-shots", str(shots),
            "--llm-retries", "1",
            "--llm-stats", str(stats_path),
            "--llm-failed-output", str(failed_path),
            "-o", str(output),
        ]
        started = time.time()
        try:
            result = subprocess.run(command, cwd=worker_dir(), env=env,
                                    timeout=900, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            rc, raw, timed_out = result.returncode, result.stdout, False
        except subprocess.TimeoutExpired as error:
            rc, raw, timed_out = -1, error.stdout or b"", True
        elapsed = round(time.time() - started, 1)
        log.write_bytes(raw)

        stats = {}
        if stats_path.exists():
            try:
                stats = json.loads(stats_path.read_text(encoding="utf-8"))
            except ValueError:
                stats = {}
        build_ok = (output.exists() and output.stat().st_size > 0
                    and stats.get("ok") is True)
        exec_ok = False
        match = False
        detail = ""
        if build_ok:
            exec_ok, buffer = run_payload(
                arch, output, run_dir / "llm_outputs" / f"{stem}.txt")
            if exec_ok and buffer is not None:
                match = buffer == expected_buffer(case)
                if not match:
                    detail = "result buffer mismatch"
            else:
                detail = "payload crashed or produced no output"
        else:
            detail = (stats.get("error")
                      or raw.decode("utf-8", "replace")[-800:])

        attempts = stats.get("attempts", 0) or 0
        usage = stats.get("usage") or {}
        cost = (stats.get("cost_usd") or {}).get("total") or 0.0
        with LOCK:
            SPENT["value"] += cost
            if SPENT["value"] > args.max_cost:
                STOP.set()
        return {
            "arch": arch, "case": case_name, "technique": technique,
            "shots": shots, "call": call, "rc": rc, "build_ok": build_ok,
            "size": output.stat().st_size if output.exists() else 0,
            "sha256": sha256(output) if output.exists() else None,
            "exec_ok": exec_ok, "match": match,
            "generation_calls": 1, "attempts": attempts,
            "tokens": usage.get("total_tokens"),
            "cost_usd": cost,
            "elapsed": elapsed, "timed_out": timed_out,
            "log": str(log.relative_to(ROOT)),
            "stats": str(stats_path.relative_to(ROOT))
            if stats_path.exists() else None,
            "failed_output": str(failed_path.relative_to(ROOT))
            if failed_path.exists() else None,
            "error": detail,
        }

    ok = 0
    total_cost = 0.0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [pool.submit(execute, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            record = future.result()
            ok += record["match"]
            total_cost += record["cost_usd"] or 0.0
            with LOCK:
                with out_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            print(f"[{done}/{len(tasks)}] {record['case']}/"
                  f"{record['technique']}/s{record['shots']}/{record['call']} "
                  f"build={record['build_ok']} match={record['match']} "
                  f"${record['cost_usd']:.4f}", flush=True)
    print(f"[DONE] calls={len(tasks)} matches={ok} "
          f"cost=${total_cost:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
