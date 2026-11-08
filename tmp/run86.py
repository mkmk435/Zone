import subprocess
import sys
import time

exe = r"C:\Users\ubu\Desktop\Zone\ploader86.exe"
payload = sys.argv[1]
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0

start = time.time()
proc = subprocess.Popen([exe, payload],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
code = proc.poll()
while code is None and time.time() - start < timeout:
    time.sleep(0.05)
    code = proc.poll()
elapsed = time.time() - start
if code is None:
    proc.kill()
    print(f"ALIVE at {elapsed:.2f}s (blocking) -> OK")
else:
    print(f"EXITED after {elapsed:.2f}s code=0x{code & 0xFFFFFFFF:X} -> "
          f"{'OK' if elapsed < 1.0 else 'returned early'}")
