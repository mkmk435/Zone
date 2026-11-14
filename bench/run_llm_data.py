#!/usr/bin/env python3
"""LLM data-classifier verification on fixtures with known code/data layout.

RUN ONLY after an explicit confirmation that the other session has finished.
The verified engine is the one passed with --engine (freeze it first with
bench/freeze_engine.py).

For every data-bearing fixture: 3 calls of --llm-data (retries included),
then compare the classified ranges with the ground-truth ranges recorded in
bench/fixtures/cases.json, and execute the extracted payload.
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
CALLS = 3
LOCK = threading.Lock()


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


def prepare_dir(directory: Path, engine: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "blocks.txt", "jump_table.txt"):
        shutil.copy2(engine / name, directory / name)
    for name in ("instr_payload.txt", "instr_payload2.txt"):
        (directory / name).write_text("", encoding="utf-8")
    (directory / "data_cache.json").write_text("{}", encoding="utf-8")


def compare(sections: list, truth: list) -> dict:
    def key(section):
        return (int(section.get("offset", -1)), int(section.get("length", -1)))

    predicted = {key(section) for section in sections}
    expected = {(entry["offset"], entry["length"]) for entry in truth}
    exact = predicted == expected
    covered = sum(entry["length"] for entry in truth
                  if (entry["offset"], entry["length"]) in predicted)
    total = sum(entry["length"] for entry in truth)
    return {
        "exact_match": exact,
        "expected": sorted(expected),
        "predicted": sorted(predicted),
        "covered_data_bytes": covered,
        "total_data_bytes": total,
        "coverage": covered / total if total else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--out", default="bench/results/llm_data_attempts.jsonl")
    args = parser.parse_args()

    engine = ROOT / args.engine
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("[ERROR] DEEPSEEK_API_KEY is not set")
        return 2
    cases = [case for case in json.loads(
        (HERE / "fixtures" / "cases.json").read_text(encoding="utf-8"))
        if case["requires_extract"]]
    if not cases:
        print("[ERROR] no data-bearing fixture")
        return 2

    run_dir = ROOT / "bench" / "run"
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            existing.add((record["arch"], record["case"], record["call"]))

    tasks = [{"case": case, "call": call}
             for case in cases for call in range(1, CALLS + 1)
             if (case["arch"], case["name"], call) not in existing]
    print(f"[INFO] {len(tasks)} classifier calls", flush=True)
    if not tasks:
        return 0

    worker_dirs: dict[int, Path] = {}

    def worker_dir() -> Path:
        ident = threading.get_ident()
        with LOCK:
            if ident not in worker_dirs:
                index = len(worker_dirs)
                directory = run_dir / f"lldata_w{index}"
                prepare_dir(directory, engine)
                worker_dirs[ident] = directory
        return worker_dirs[ident]

    def execute(task: dict) -> dict:
        case = task["case"]
        arch, name, call = case["arch"], case["name"], task["call"]
        stem = f"{arch}_{name}_call{call}"
        output = run_dir / "lldata_outputs" / f"{stem}.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        stats_path = run_dir / "lldata_stats" / f"{stem}.json"
        data_path = run_dir / "lldata_stats" / f"{stem}.data.json"
        failed_path = run_dir / "lldata_failed" / f"{stem}.asm"
        for directory in (stats_path.parent, failed_path.parent):
            directory.mkdir(parents=True, exist_ok=True)
        log = ROOT / "bench" / "logs" / "lldata" / f"{stem}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        for path in (output, stats_path, data_path, failed_path):
            if path.exists():
                path.unlink()

        tool = "pobf.py" if arch == "x64" else "pobf86.py"
        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   DEEPSEEK_API_KEY=key)
        command = [
            sys.executable, str(engine / tool), str(ROOT / case["file"]),
            "--llm-data",
            "--llm-data-json", str(data_path),
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
        data = {}
        if data_path.exists():
            try:
                data = json.loads(data_path.read_text(encoding="utf-8"))
            except ValueError:
                data = {}
        build_ok = (output.exists() and output.stat().st_size > 0
                    and stats.get("ok") is True)
        exec_ok = match = False
        detail = ""
        if build_ok:
            exec_ok, buffer = run_payload(
                arch, output, run_dir / "lldata_outputs" / f"{stem}.txt")
            if exec_ok and buffer is not None:
                match = buffer == expected_buffer(case)
                detail = "" if match else "result buffer mismatch"
            else:
                detail = "payload crashed or produced no output"
        else:
            detail = (stats.get("error")
                      or raw.decode("utf-8", "replace")[-800:])
        comparison = compare(data.get("sections") or [], case["data_ranges"])
        return {
            "arch": arch, "case": name, "call": call, "rc": rc,
            "build_ok": build_ok,
            "size": output.stat().st_size if output.exists() else 0,
            "sha256": sha256(output) if output.exists() else None,
            "exec_ok": exec_ok, "match": match,
            "exact_classification": comparison["exact_match"],
            "classification": comparison,
            "attempts": stats.get("attempts", 0),
            "tokens": (stats.get("usage") or {}).get("total_tokens"),
            "cost_usd": (stats.get("cost_usd") or {}).get("total") or 0.0,
            "elapsed": elapsed, "timed_out": timed_out,
            "log": str(log.relative_to(ROOT)),
            "error": detail,
        }

    ok = 0
    total_cost = 0.0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [pool.submit(execute, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            record = future.result()
            ok += record["match"]
            total_cost += record["cost_usd"]
            with LOCK:
                with out_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            print(f"[{done}/{len(tasks)}] {record['arch']}/"
                  f"{record['case']}/call{record['call']} "
                  f"build={record['build_ok']} exact="
                  f"{record['exact_classification']} match={record['match']} "
                  f"${record['cost_usd']:.4f}", flush=True)
    print(f"[DONE] calls={len(tasks)} matches={ok} "
          f"cost=${total_cost:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
