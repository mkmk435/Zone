"""Working-rate check: wrap the MessageBox payload with several flag
combinations and verify the dialog still appears, N runs each."""

import os
import subprocess
import sys

import check_messagebox

PAYLOAD = "original_pl/x64/windows_x64_messagebox.bin"
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


def main():
    total_ok = 0
    total = 0
    for combo_index, combo in enumerate(COMBOS):
        ok = 0
        sizes = []
        for run in range(RUNS):
            output = f"tmp/msg_combo_{combo_index}_{run}.bin"
            env = dict(os.environ, ZONE_WRAP_SEED=str(100 + run))
            with open("tmp/msg_build.log", "wb") as log:
                built = subprocess.run(
                    [sys.executable, "pobf.py", PAYLOAD, *combo, "-o", output],
                    stdout=log, stderr=subprocess.STDOUT, env=env)
            if built.returncode != 0:
                print(f"{' '.join(combo)} run {run}: BUILD FAILED")
                continue
            sizes.append(os.path.getsize(output))
            result = check_messagebox.check(output)
            total += 1
            if result.startswith("dialog shown"):
                ok += 1
                total_ok += 1
            else:
                print(f"{' '.join(combo)} run {run}: {result}")
        average = sum(sizes) / len(sizes) if sizes else 0
        print(f"{' '.join(combo):40s} {ok}/{RUNS} dialogs, "
              f"~{average:.0f} bytes")
    print(f"TOTAL: {total_ok}/{total}")
    return 0 if total_ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
