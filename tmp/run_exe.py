import subprocess, sys
try:
    p = subprocess.run(["tmp/test_pe.exe"], timeout=6)
    print("exit:", p.returncode, hex(p.returncode & 0xffffffff))
except subprocess.TimeoutExpired:
    print("TIMEOUT (non termina)")
