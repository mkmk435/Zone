#!/usr/bin/env python3
"""Single LLM pilot on network payloads (x64/x86) to validate the pipeline."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "bench" / "engines" / "2026-11-13_block3"
BASE = Path(__file__).resolve().parent
RUN = BASE / "run"
OUT = BASE / "llm_pilot"
API_KEY = (ROOT / "dsk.txt").read_text(encoding="utf-8").strip()


def worker(name: str) -> Path:
    cwd = RUN / f"pilot_{name}"
    cwd.mkdir(parents=True, exist_ok=True)
    for item in ("dict.txt", "instr_payload.txt", "instr_payload2.txt",
                 "blocks.txt", "jump_table.txt"):
        target = cwd / item
        if not target.exists():
            shutil.copy2(ROOT / item, target)
    cache = RUN / "data_cache.json"
    if cache.exists():
        shutil.copy2(cache, cwd / "data_cache.json")
    return cwd


def run(arch: str, payload: str, tech: str, shots: int) -> dict:
    src = ROOT / "original_pl" / arch / f"{payload}.bin"
    out = OUT / arch / f"{payload}_llm_{tech}_s{shots}.bin"
    stats = OUT / arch / f"{payload}_llm_{tech}_s{shots}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    engine = ENGINE / ("pobf.py" if arch == "x64" else "pobf86.py")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", ZONE_LLM_API_KEY=API_KEY)
    cmd = [sys.executable, str(engine), str(src), "--llm", f"-{tech}",
           "--llm-shots", str(shots), "--llm-retries", "3",
           "--llm-max-tokens", "65536", "--llm-stats", str(stats),
           "-o", str(out)]
    started = time.time()
    proc = subprocess.run(cmd, cwd=worker(f"{arch}_{payload}_{tech}_{shots}"),
                          env=env, timeout=3600,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    elapsed = round(time.time() - started, 1)
    text = proc.stdout.decode("utf-8", errors="replace")
    data = {}
    if stats.exists():
        data = json.loads(stats.read_text(encoding="utf-8"))
    return {
        "arch": arch, "payload": payload, "tech": tech, "shots": shots,
        "out": str(out), "status": "ok" if out.exists() and data.get("ok") else "fail",
        "elapsed_s": elapsed, "size": out.stat().st_size if out.exists() else 0,
        "api_calls": data.get("api_calls"),
        "attempts": data.get("attempts"),
        "cost_usd": (data.get("cost_usd") or {}).get("total"),
        "tokens": (data.get("usage") or {}).get("total_tokens"),
        "similarity": next((a.get("similarity") for a in reversed(
            data.get("attempt_details", [])) if a.get("accepted")), None),
        "error": "" if data.get("ok") else (data.get("error") or text[-1200:]),
    }


if __name__ == "__main__":
    results = []
    for arch, payload in (("x64", "windows_x64_custom_reverse_http"),
                          ("x86", "windows_custom_reverse_http")):
        results.append(run(arch, payload, "eq", 0))
    for row in results:
        print(json.dumps(row, indent=2))
    (BASE / "llm_pilot.json").write_text(json.dumps(results, indent=2),
                                         encoding="utf-8")
