#!/usr/bin/env python3
"""Compare LLM data classification and the symbolic extractor against the same
ground truth, on classifier-only fixtures.

The model receives only the payload (hex dump + disassembly + printable runs);
neither the ground truth nor the symbolic answer is in the prompt.  The two
methods are evaluated independently against the expected ranges; their mutual
agreement is recorded separately.

Per case:
  * symbolic: one `-xd` run, ranges parsed from the extractor log;
  * LLM: three `--llm-data` calls (max 3, retries included at --llm-retries 1).
"""
from __future__ import annotations

import argparse
import hashlib
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

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness" / "bin"
LOCK = threading.Lock()
SECTION_RE = re.compile(r"^\s+0x([0-9a-f]+) \((\d+) B")


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
    return (True, bytes(int(value, 16) for value in text.split(","))) \
        if text else (False, None)


def prepare_dir(directory: Path, engine: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("dict.txt", "blocks.txt", "jump_table.txt"):
        shutil.copy2(engine / name, directory / name)
    for name in ("instr_payload.txt", "instr_payload2.txt"):
        (directory / name).write_text("", encoding="utf-8")
    (directory / "data_cache.json").write_text("{}", encoding="utf-8")


def parse_symbolic_sections(text: str) -> list:
    """Parse the 'Data sections:' block: the analyser's classification."""
    ranges = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("Data sections:"):
            collecting = True
            continue
        if collecting:
            match = SECTION_RE.match(line)
            if match:
                ranges.append({"offset": int(match.group(1), 16),
                               "length": int(match.group(2))})
            elif line.strip() and not line.startswith(" "):
                break
    return ranges


def parse_response_sections(path: Path) -> tuple[list, str]:
    """Best-effort parse of the raw model response (JSON)."""
    if not path.exists():
        return [], ""
    text = path.read_text(encoding="utf-8", errors="replace")
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return [], text[-300:]
    try:
        data = json.loads(text[start:end + 1])
    except ValueError as error:
        return [], f"invalid JSON: {error}"
    return data.get("sections") or [], ""


def parse_sections(text: str) -> list:
    ranges = []
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            ranges.append({"offset": int(match.group(1), 16),
                           "length": int(match.group(2))})
    return ranges


def evaluate(predicted: list, truth: list, size: int) -> dict:
    pred = {(int(item["offset"]), int(item["length"])) for item in predicted}
    true = {(item["offset"], item["length"]) for item in truth}

    def covered_by(intervals, start, length):
        return any(start >= a and start + length <= a + b
                   for a, b in intervals)

    missed = [item for item in true if item not in pred]
    extra = [item for item in pred if item not in true]
    truth_union = set()
    for offset, length in true:
        truth_union.update(range(offset, offset + length))
    extra_bytes = sum(length for _, length in extra)
    code_fp = 0
    for offset, length in extra:
        code_fp += sum(1 for byte in range(offset, offset + length)
                       if byte not in truth_union)
    data_covered = 0
    for offset, length in true:
        for position in range(offset, offset + length):
            if any(a <= position < a + b for a, b in pred):
                data_covered += 1
    return {
        "exact": pred == true,
        "predicted": sorted(pred),
        "truth": sorted(true),
        "missed_ranges": sorted(missed),
        "extra_ranges": sorted(extra),
        "missed_bytes": sum(length for _, length in missed),
        "extra_bytes": extra_bytes,
        "code_false_positive_bytes": code_fp,
        "data_covered_bytes": data_covered,
        "data_total_bytes": sum(length for _, length in true),
        "coverage": (data_covered / sum(length for _, length in true)
                     if true else 1.0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--calls", type=int, default=3)
    parser.add_argument("--out", default="bench/results/classifier_compare.jsonl")
    args = parser.parse_args()

    engine = ROOT / args.engine
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("[ERROR] DEEPSEEK_API_KEY is not set")
        return 2
    cases = json.loads((HERE / "fixtures" / "classifier_cases.json").read_text(
        encoding="utf-8"))
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
            existing.add((record["arch"], record["case"], record["method"],
                          record["call"]))

    tasks = []
    for case in cases:
        if (case["arch"], case["name"], "symbolic", 0) not in existing:
            tasks.append({"case": case, "method": "symbolic", "call": 0})
        for call in range(1, args.calls + 1):
            if (case["arch"], case["name"], "llm", call) not in existing:
                tasks.append({"case": case, "method": "llm", "call": call})
    print(f"[INFO] {len(tasks)} classifier runs", flush=True)
    if not tasks:
        return 0

    worker_dirs: dict[int, Path] = {}

    def worker_dir() -> Path:
        ident = threading.get_ident()
        with LOCK:
            if ident not in worker_dirs:
                index = len(worker_dirs)
                directory = run_dir / f"cls_w{index}"
                prepare_dir(directory, engine)
                worker_dirs[ident] = directory
        return worker_dirs[ident]

    def execute(task: dict) -> dict:
        case = task["case"]
        arch, name = case["arch"], case["name"]
        method, call = task["method"], task["call"]
        tool = "pobf.py" if arch == "x64" else "pobf86.py"
        stem = f"{arch}_{name}_{method}_{call}"
        output = run_dir / "cls_outputs" / f"{stem}.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        data_path = run_dir / "cls_data" / f"{stem}.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        response_path = run_dir / "cls_responses" / f"{stem}.json"
        response_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path = run_dir / "cls_stats" / f"{stem}.json"
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        log = ROOT / "bench" / "logs" / "classifier" / f"{stem}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        for path in (output, data_path, response_path, stats_path):
            if path.exists():
                path.unlink()

        env = dict(os.environ, PYTHONIOENCODING="utf-8",
                   DEEPSEEK_API_KEY=key)
        if method == "symbolic":
            command = [sys.executable, str(engine / tool),
                       str(ROOT / case["file"]), "-xd", "-o", str(output)]
        else:
            command = [sys.executable, str(engine / tool),
                       str(ROOT / case["file"]), "--llm-data",
                       "--llm-data-json", str(data_path),
                       "--llm-dump-response", str(response_path),
                       "--llm-stats", str(stats_path),
                       "--llm-retries", "1", "-o", str(output)]
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
        text = raw.decode("utf-8", "replace")

        if method == "symbolic":
            predicted = parse_symbolic_sections(text)
            classification_source = "symbolic_data_sections"
            cost = 0.0
            stats = {}
        else:
            stats = {}
            if stats_path.exists():
                try:
                    stats = json.loads(stats_path.read_text(encoding="utf-8"))
                except ValueError:
                    stats = {}
            predicted = []
            classification_source = "none"
            if data_path.exists():
                try:
                    data = json.loads(data_path.read_text(encoding="utf-8"))
                except ValueError:
                    data = {}
                predicted = data.get("sections") or []
                classification_source = "accepted_sections"
            elif response_path.exists():
                predicted, _ = parse_response_sections(response_path)
                classification_source = "raw_response"
            cost = (stats.get("cost_usd") or {}).get("total") or 0.0

        build_ok = output.exists() and output.stat().st_size > 0
        exec_ok = match = False
        if build_ok and method == "symbolic":
            build_ok = rc == 0
        if build_ok:
            exec_ok, buffer = run_payload(
                arch, output, run_dir / "cls_outputs" / f"{stem}.txt")
            match = exec_ok and buffer == expected_buffer(case)
        result_eval = evaluate(predicted, case["data_ranges"], case["size"])
        return {
            "arch": arch, "case": name, "method": method, "call": call,
            "engine": args.engine,
            "predicted": predicted, "evaluation": result_eval,
            "classification_source": classification_source,
            "build_ok": build_ok, "exec_ok": exec_ok, "match": match,
            "cost_usd": cost, "elapsed": elapsed, "timed_out": timed_out,
            "attempts": stats.get("attempts", 0),
            "log": str(log.relative_to(ROOT)),
            "sha256": sha256(output) if output.exists() else None,
            "error": "" if build_ok else (stats.get("error")
                                          or text[-500:]),
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
                  f"{record['case']}/{record['method']}/{record['call']} "
                  f"exact={record['evaluation']['exact']} "
                  f"build={record['build_ok']} match={record['match']} "
                  f"${record['cost_usd']:.4f}", flush=True)
    print(f"[DONE] runs={len(tasks)} correct_exec={ok} "
          f"cost=${total_cost:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
