"""Run a PE payload-loader with a raw shellcode payload and check it works.

Usage: python tmp/run_payload_test.py <exe> <payload.bin> [reverse|bind]

reverse: bind a listener on 127.0.0.1:1234, run exe, expect an inbound connection.
Success means the (possibly obfuscated) loader executed the payload.
"""
import socket
import subprocess
import sys
import time


def main():
    exe = sys.argv[1]
    payload = sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 else "reverse"
    port = 1234
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1" if kind == "reverse" else "0.0.0.0", port))
    except OSError as exc:
        print("RESULT: PORT_BUSY", exc)
        return 2
    sock.listen(1)
    sock.settimeout(8)
    proc = subprocess.Popen([exe, payload],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        conn, _ = sock.accept()
        conn.close()
        print("RESULT: OK")
        return 0
    except socket.timeout:
        print("RESULT: FAIL (no connection); child rc=%s" % proc.poll())
        return 1
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        sock.close()


if __name__ == "__main__":
    sys.exit(main())
