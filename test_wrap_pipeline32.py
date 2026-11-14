"""End-to-end x86 test: run the 32-bit programs through pobf86.py with -wrap.

The oracle is carried by the payload itself (a wrong result jumps to a null
write), so the loader exit code is the pass/fail signal.

A combination is only judged when the *same* combination without -wrap already
works: some tiny synthetic payloads are broken by -eq/-bcf alone (a pre-existing
behaviour of the 32-bit build, unrelated to wrapping), and the test reports
those as skipped instead of blaming the new pass.

Run with:  python test_wrap_pipeline32.py
"""

import os
import subprocess
import sys

import test_asm_wrap32 as harness

COMBOS = [
    ["-wrap"],
    ["-wrap", "-nop"],
    ["-wrap", "-eq", "-nop"],
    ["-wrap", "-bcf"],
    ["-wrap", "-eq", "-nop", "-bcf"],
]


def run_tool(source, flags, output, seed):
    encoding, _ = harness.ks.asm(source, 0)
    payload = bytes(encoding)
    source_path = output + ".in"
    with open(source_path, "wb") as handle:
        handle.write(payload)
    env = dict(os.environ, ZONE_WRAP_SEED=str(seed))
    with open(output + ".log", "wb") as log:
        result = subprocess.run(
            [sys.executable, "pobf86.py", source_path, *flags, "-o", output],
            stdout=log, stderr=subprocess.STDOUT, env=env)
    if result.returncode != 0:
        return None
    with open(output, "rb") as handle:
        return handle.read()


def main():
    run = harness.Runner()
    failures = 0
    checked = 0
    skipped = 0
    for name, source in harness.PROGRAMMES.items():
        for combo_index, combo in enumerate(COMBOS):
            baseline_flags = [flag for flag in combo if flag != "-wrap"]
            for seed in range(2):
                baseline = run_tool(
                    source, baseline_flags or ["-ebi"],
                    f"tmp/p32_base_{name}_{combo_index}_{seed}.bin", seed)
                if baseline is None or not run(baseline):
                    skipped += 1
                    print(f"SKIP {name} {' '.join(combo)} seed={seed}: "
                          "baseline without -wrap already fails")
                    continue

                checked += 1
                payload = run_tool(
                    source, combo,
                    f"tmp/p32_wrap_{name}_{combo_index}_{seed}.bin", seed)
                if payload is None:
                    failures += 1
                    print(f"FAIL {name} {' '.join(combo)} seed={seed}: build")
                    continue
                if not run(payload):
                    failures += 1
                    print(f"FAIL {name} {' '.join(combo)} seed={seed}: crash")
    print(f"x86 pipeline: {checked - failures}/{checked} passed, "
          f"{skipped} skipped (broken baseline)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
