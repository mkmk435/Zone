#!/usr/bin/env python3
"""Native transformation matrix on the benign corpus.

One technique per build (extraction `-xd` is preprocessing for cases that
declare inline data).  Three independent runs per cell.  Every attempt records
the command, seed (wrap only), output hash, build result, execution result and
the log path.  Results are appended to a JSONL file and the run is resumable.

Usage:
    python bench/run_native.py --engine bench/engines/2026-11-13_block1
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
TECHNIQUES = ["eq", "nop", "bcf", "ibp", "wrap"]
LOCK = threading.Lock()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases() -> list:
    return json.loads((HERE / "fixtures" / "cases.json").read_text(
        encoding="utf-8"))


def prepare_dir(directory: Path, engine: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "blocks.txt", "jump_table.txt"):
        shutil.copy2(engine / name, directory / name)
    for name in ("instr_payload.txt", "instr_payload2.txt"):
        (directory / name).write_text("", encoding="utf-8")


def expected_buffer(case: dict) -> bytearray:
    buffer = bytearray(b"\xCC" * 256)
    for entry in case["expect"]:
        data = bytes.fromhex(entry["bytes"])
        buffer[entry["offset"]:entry["offset"] + len(data)] = data
    return buffer


def run_payload(arch: str, payload: Path, output: Path) -> tuple[bool, bytes | None]:
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


def run_command(command: list[str], cwd: Path, env: dict, timeout: int):
    started = time.time()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, timeout=timeout,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        return result.returncode, result.stdout, time.time() - started, False
    except subprocess.TimeoutExpired as error:
        return -1, error.stdout or b"", time.time() - started, True


def prewarm(engine: Path, cases: list, run_dir: Path) -> dict:
    """Run -xd once per data case, keep the baseline and a warm cache."""
    directory = run_dir / "prewarm"
    prepare_dir(directory, engine)
    cache = directory / "data_cache.json"
    cache.write_text("{}", encoding="utf-8")
    baselines = {}
    for case in cases:
        if not case["requires_extract"]:
            continue
        arch, name = case["arch"], case["name"]
        output = run_dir / "baseline" / f"{arch}_{name}_xd.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        python = "pobf.py" if arch == "x64" else "pobf86.py"
        command = [sys.executable, str(engine / python),
                   str(ROOT / case["file"]), "-xd", "-o", str(output)]
        log = run_dir.parent / "logs" / "native" / f"{arch}_{name}_xd.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        rc, raw, elapsed, timed_out = run_command(command, directory, env, 300)
        log.write_bytes(raw)
        ok = output.exists() and output.stat().st_size > 0
        exec_ok, buffer = (False, None)
        match = False
        if ok:
            exec_ok, buffer = run_payload(
                arch, output, run_dir / "baseline" / f"{arch}_{name}_xd.txt")
            match = exec_ok and buffer == expected_buffer(case)
        print(f"[prewarm] {arch}/{name} -xd: build={ok} exec={exec_ok} "
              f"match={match}", flush=True)
        baselines[(arch, name)] = {
            "arch": arch, "case": name, "technique": "xd", "run": 0,
            "flags": ["-xd"], "rc": rc, "build_ok": ok,
            "size": output.stat().st_size if ok else 0,
            "sha256": sha256(output) if ok else None,
            "exec_ok": exec_ok, "match": match,
            "elapsed": round(elapsed, 2), "log": str(log.relative_to(ROOT)),
            "error": ("" if ok else raw.decode("utf-8", "replace")[-800:]),
        }
    return baselines, cache


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--threads", type=int, default=3)
    parser.add_argument("--arch", choices=["x64", "x86", "both"], default="both")
    parser.add_argument("--tech", action="append", default=None)
    parser.add_argument("--out", default="bench/results/native_attempts.jsonl")
    parser.add_argument("--allow-x86-wrap", action="store_true",
                        help="test -wrap on x86 (needs a frozen engine that "
                             "implements it)")
    args = parser.parse_args()

    engine = (ROOT / args.engine)
    if not (engine / "pobf.py").exists():
        print(f"[ERROR] engine not found: {engine}")
        return 2
    cases = [case for case in load_cases()
             if args.arch == "both" or case["arch"] == args.arch]
    techniques = args.tech or TECHNIQUES

    run_dir = ROOT / "bench" / "run"
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    baselines, cache = prewarm(engine, cases, run_dir)

    existing = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            existing.add((record["arch"], record["case"], record["technique"],
                          record["run"]))

    tasks = []
    for case in cases:
        arch, name = case["arch"], case["name"]
        for technique in techniques:
            if technique == "wrap" and arch == "x86" \
                    and not args.allow_x86_wrap:
                continue        # block 1 excluded in-progress x86 wrapping
            for index in range(1, args.runs + 1):
                key = (arch, name, technique, index)
                if key in existing:
                    continue
                flags = [f"-{technique}"]
                if case["requires_extract"]:
                    flags = ["-xd", f"-{technique}"]
                tasks.append({
                    "arch": arch, "case": name, "technique": technique,
                    "run": index, "flags": flags,
                    "seed": (1000 * techniques.index(technique) + index)
                    if technique == "wrap" else None,
                    "case_data": case,
                })
    print(f"[INFO] {len(tasks)} native attempts, {args.threads} workers",
          flush=True)

    worker_dirs: dict[int, Path] = {}

    def worker_dir() -> Path:
        ident = threading.get_ident()
        with LOCK:
            if ident not in worker_dirs:
                index = len(worker_dirs)
                directory = run_dir / f"native_w{index}"
                prepare_dir(directory, engine)
                shutil.copy2(cache, directory / "data_cache.json")
                worker_dirs[ident] = directory
        return worker_dirs[ident]

    def execute(task) -> dict:
        arch, name, technique = task["arch"], task["case"], task["technique"]
        case = task["case_data"]
        output = run_dir / "outputs" / f"{arch}_{name}_{technique}_{task['run']}.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        log = ROOT / "bench" / "logs" / "native" / (
            f"{arch}_{name}_{technique}_{task['run']}.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        if task["seed"] is not None:
            env["ZONE_WRAP_SEED"] = str(task["seed"])
        python = "pobf.py" if arch == "x64" else "pobf86.py"
        command = [sys.executable, str(engine / python),
                   str(ROOT / case["file"]), *task["flags"], "-o", str(output)]
        rc, raw, elapsed, timed_out = run_command(
            command, worker_dir(), env, 300)
        log.write_bytes(raw)
        build_ok = output.exists() and output.stat().st_size > 0
        exec_ok = False
        match = False
        detail = ""
        if build_ok:
            exec_ok, buffer = run_payload(
                arch, output, run_dir / "outputs" / (
                    f"{arch}_{name}_{technique}_{task['run']}.txt"))
            if exec_ok and buffer is not None:
                match = buffer == expected_buffer(case)
                if not match:
                    detail = "result buffer mismatch"
            else:
                detail = "payload crashed or produced no output"
        else:
            detail = raw.decode("utf-8", "replace")[-800:]
        return {
            "arch": arch, "case": name, "technique": technique,
            "run": task["run"], "seed": task["seed"],
            "flags": task["flags"], "rc": rc, "build_ok": build_ok,
            "size": output.stat().st_size if build_ok else 0,
            "sha256": sha256(output) if build_ok else None,
            "exec_ok": exec_ok, "match": match,
            "elapsed": round(elapsed, 2), "timed_out": timed_out,
            "log": str(log.relative_to(ROOT)), "error": detail,
        }

    successes = 0
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [pool.submit(execute, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            record = future.result()
            if record["build_ok"] and record["match"]:
                successes += 1
            with LOCK:
                with out_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            if done % 10 == 0 or done == len(tasks):
                print(f"[{done}/{len(tasks)}] ok={successes}", flush=True)

    if baselines:
        with out_path.open("a", encoding="utf-8") as handle:
            for record in baselines.values():
                key = (record["arch"], record["case"], "xd", 0)
                if key in existing:
                    continue
                handle.write(json.dumps(record) + "\n")
    print(f"[DONE] newly attempted={len(tasks)} ok={successes}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
