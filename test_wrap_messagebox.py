"""Working-rate check for both builds.

Wraps the MessageBox payload of the selected architecture with several flag
combinations and verifies that the dialog still appears, N runs each.

    python test_wrap_messagebox.py x64
    python test_wrap_messagebox.py x86
"""

import os
import subprocess
import sys

import check_messagebox

ARCHITECTURES = {
    "x64": {
        "payload": "original_pl/x64/windows_x64_messagebox.bin",
        "loader": "ploader.exe",
        "tool": "pobf.py",
    },
    "x86": {
        "payload": "original_pl/x86/windows_messagebox.bin",
        "loader": "ploader86.exe",
        "tool": "pobf86.py",
    },
}

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


def main(arch_name):
    arch = ARCHITECTURES[arch_name]
    total_ok = 0
    total = 0
    for combo_index, combo in enumerate(COMBOS):
        ok = 0
        sizes = []
        for run in range(RUNS):
            output = f"tmp/msg_{arch_name}_{combo_index}_{run}.bin"
            env = dict(os.environ, ZONE_WRAP_SEED=str(100 + run))
            with open(f"tmp/msg_{arch_name}_build.log", "wb") as log:
                built = subprocess.run(
                    [sys.executable, arch["tool"], arch["payload"], *combo,
                     "-o", output],
                    stdout=log, stderr=subprocess.STDOUT, env=env)
            if built.returncode != 0:
                print(f"{' '.join(combo)} run {run}: BUILD FAILED")
                continue
            sizes.append(os.path.getsize(output))
            result = check_messagebox.check(output, loader=arch["loader"])
            total += 1
            if result.startswith("dialog shown"):
                ok += 1
                total_ok += 1
            else:
                print(f"{' '.join(combo)} run {run}: {result}")
        average = sum(sizes) / len(sizes) if sizes else 0
        print(f"{arch_name} {' '.join(combo):40s} {ok}/{RUNS} dialogs, "
              f"~{average:.0f} bytes")
    print(f"{arch_name} TOTAL: {total_ok}/{total}")
    return 0 if total_ok == total else 1


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "x64"
    sys.exit(main(name))
