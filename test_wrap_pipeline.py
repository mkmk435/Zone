"""End-to-end test: run synthetic payloads through pobf.py with -wrap.

For every program and flag combination the original payload and the pobf.py
output are executed on the real CPU; the result buffers must match.

Run with:  python test_wrap_pipeline.py
"""

import os
import subprocess
import sys

import test_asm_wrap as harness

COMBOS = [
    ["-wrap"],
    ["-wrap", "-eq", "-nop"],
    ["-wrap", "-bcf"],
    ["-wrap", "-eq", "-nop", "-bcf"],
]


def build(source, combo, output, seed):
    encoding, _ = harness.ks.asm(source, 0x1000)
    payload = bytes(encoding)
    source_path = output + ".in"
    with open(source_path, "wb") as handle:
        handle.write(payload)
    env = dict(os.environ, ZONE_WRAP_SEED=str(seed))
    with open(output + ".log", "wb") as log:
        result = subprocess.run(
            [sys.executable, "pobf.py", source_path, *combo, "-o", output],
            stdout=log, stderr=subprocess.STDOUT, env=env)
    if result.returncode != 0:
        return payload, None
    with open(output, "rb") as handle:
        return payload, handle.read()


def main():
    runner = harness.Runner()
    failures = 0
    checked = 0
    for name, source in harness.PROGRAMMES.items():
        for combo_index, combo in enumerate(COMBOS):
            for seed in range(2):
                checked += 1
                output = f"tmp/pipeline_{name}_{combo_index}_{seed}.bin"
                original, wrapped = build(source, combo, output, seed)
                expected = runner(original)
                if wrapped is None:
                    failures += 1
                    print(f"FAIL {name} {' '.join(combo)} seed={seed}: build")
                    continue
                got = runner(wrapped)
                if got is None:
                    failures += 1
                    print(f"FAIL {name} {' '.join(combo)} seed={seed}: "
                          "crash")
                    continue
                if got != expected:
                    failures += 1
                    print(f"FAIL {name} {' '.join(combo)} seed={seed}: "
                          "result mismatch")
    print(f"pipeline: {checked - failures}/{checked} matched")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
