"""Matrice di test dei passi di zone.py.

1) fixture: il PE di tmp/make_test_pe.py ritorna 42 -> l'exit code e' il
   risultato atteso (test semantico);
2) ploader.exe: il loader deve ancora eseguire il payload (reverse_tcp su
   127.0.0.1:1234);
3) --check deve riportare zero errori su ogni output.
"""
import itertools
import os
import socket
import subprocess
import sys

FIXTURE = "tmp/test_pe.exe"
LOADER = "ploader.exe"
PAYLOAD = "original_pl/x64/windows_x64_custom_reverse_tcp.bin"
SEEDS = (7, 21, 42)

COMBOS = [
    [],
    ["--nop"],
    ["--bcf"],
    ["--ibp"],
    ["--ebi"],
    ["--ebi", "--ibp", "--bcf", "--nop"],
]


def run_zone(source, output, combo, seed):
    command = [sys.executable, "zone.py", source, "-o", output,
               "--seed", str(seed), "--bcf-probability", "100",
               "--nop-probability", "100", "--ibp-probability", "100",
               "--check"] + combo
    result = subprocess.run(command, capture_output=True, text=True)
    errors = [line for line in result.stdout.splitlines() if "ERRORE" in line]
    verified = [line for line in result.stdout.splitlines() if line.startswith("verifica")]
    return result.returncode, errors, (verified[0] if verified else "")


def exit_code(path):
    try:
        return subprocess.run([path], timeout=10).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def payload_ok(path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 1234))
    sock.listen(1)
    sock.settimeout(7)
    proc = subprocess.Popen([path, PAYLOAD], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        connection, _ = sock.accept()
        connection.close()
        return True
    except socket.timeout:
        return False
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        sock.close()


def main():
    failures = 0
    checks = 0
    print("== fixture (exit code atteso 42) ==")
    for combo in COMBOS:
        for seed in SEEDS:
            checks += 1
            output = "tmp/mx_fixture.exe"
            code, errors, verified = run_zone(FIXTURE, output, combo, seed)
            got = exit_code(output)
            good = (got == 42 and not errors)
            failures += 0 if good else 1
            print("  %-28s seed=%-3d exit=%-6s %-28s %s" % (
                " ".join(combo) or "(eq)", seed, got, verified,
                "OK" if good else "FAIL " + str(errors[:2])))

    print("== ploader.exe (payload deve connettersi) ==")
    for combo in COMBOS[1:]:
        for seed in SEEDS[:2]:
            checks += 1
            output = "tmp/mx_loader.exe"
            code, errors, verified = run_zone(LOADER, output, combo, seed)
            ok = payload_ok(output) and not errors
            failures += 0 if ok else 1
            print("  %-28s seed=%-3d payload=%-6s %-28s %s" % (
                " ".join(combo), seed, "OK" if ok else "FAIL", verified,
                "OK" if ok else "FAIL " + str(errors[:2])))

    total = checks - failures
    print("\n%d/%d test passati" % (total, checks))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
