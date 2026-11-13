#!/usr/bin/env python3
"""Focused working-rate study of -wrap on the x64 MessageBox payload.

Seven flag combinations x 5 seeds, each output executed through ploader.exe and
checked for the dialog.  Uses the pinned engine in tmp/wrap_snapshot.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import check_messagebox

SNAP = ROOT / "tmp" / "wrap_snapshot" / "pobf.py"
RUNDIR = ROOT / "tmp" / "wrap_run"
OUTDIR = ROOT / "tmp" / "wrap_combos"
PAYLOAD = ROOT / "original_pl" / "x64" / "windows_x64_messagebox.bin"
RUNS = 5

COMBOS = [
    ["-xd", "-wrap"],
    ["-xd", "-wrap", "-eq"],
    ["-xd", "-wrap", "-nop"],
    ["-xd", "-wrap", "-bcf"],
    ["-xd", "-wrap", "-eq", "-nop", "-bcf"],
    ["-xd", "-wrap", "-ibp"],
    ["-xd", "-wrap", "-eq", "-nop", "-bcf", "-ibp"],
]


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    results = []
    total_ok = total = 0
    for combo_index, combo in enumerate(COMBOS):
        ok = 0
        sizes = []
        for run in range(RUNS):
            output = OUTDIR / f"msg_c{combo_index}_{run}.bin"
            env = dict(os.environ, ZONE_WRAP_SEED=str(100 + run),
                       PYTHONIOENCODING="utf-8")
            with open(RUNDIR / "combo_build.log", "wb") as log:
                built = subprocess.run(
                    [sys.executable, str(SNAP), str(PAYLOAD), *combo,
                     "-o", str(output)],
                    cwd=RUNDIR, stdout=log, stderr=subprocess.STDOUT, env=env)
            if built.returncode != 0:
                print(f"{' '.join(combo)} run {run}: BUILD FAILED")
                results.append((combo_index, run, "BUILD", 0))
                total += 1
                continue
            sizes.append(output.stat().st_size)
            verdict = check_messagebox.check(str(output))
            total += 1
            if verdict.startswith("dialog shown"):
                ok += 1
                total_ok += 1
                results.append((combo_index, run, "OK", output.stat().st_size))
            else:
                print(f"{' '.join(combo)} run {run}: {verdict}")
                results.append((combo_index, run, "FAIL", output.stat().st_size))
        average = sum(sizes) / len(sizes) if sizes else 0
        print(f"{' '.join(combo):40s} {ok}/{RUNS} dialogs, ~{average:.0f} bytes",
              flush=True)
    print(f"TOTAL: {total_ok}/{total}")
    with (OUTDIR / "results.csv").open("w", encoding="utf-8") as handle:
        handle.write("combo,run,status,size\n")
        for row in results:
            handle.write(",".join(str(value) for value in row) + "\n")
    return 0 if total_ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
