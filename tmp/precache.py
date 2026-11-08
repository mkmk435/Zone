import os, subprocess, sys, time
from pathlib import Path

PAYLOADS = [
    "windows_x64_custom_reverse_https",
    "windows_x64_custom_reverse_winhttp",
    "windows_x64_custom_reverse_winhttps",
    "windows_x64_meterpreter_reverse_http",
    "windows_x64_meterpreter_reverse_https",
    "windows_x64_meterpreter_reverse_winhttp",
    "windows_x64_vncinject_reverse_http",
    "windows_x64_vncinject_reverse_winhttp",
    "windows_x64_vncinject_reverse_winhttps",
    "windows_x64_meterpreter_reverse_winhttps",
    "windows_x64_vncinject_reverse_https",
    "windows_x64_messagebox",
    "windows_x64_custom_reverse_http",
]

root = Path.cwd()
env = dict(os.environ)
env["PYTHONPATH"] = str(root / "tmp" / "capstone506")

for n, name in enumerate(PAYLOADS, 1):
    src = root / "original_pl" / "x64" / f"{name}.bin"
    log = root / "tmp" / f"cache_{name}.log"
    print(f"[{n}/{len(PAYLOADS)}] -fd {name}", flush=True)
    t0 = time.time()
    with open(log, "wb") as f:
        p = subprocess.run([sys.executable, "pobf.py", str(src), "-fd", "--data-timeout", "60"],
                           cwd=root, env=env, stdout=f, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    txt = log.read_text(errors="replace")
    sections = "Data sections:" in txt
    print(f"    rc={p.returncode} {dt:.1f}s sections_printed={sections}", flush=True)

print("[DONE]", flush=True)
