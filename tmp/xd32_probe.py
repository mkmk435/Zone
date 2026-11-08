import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import pobf86

payloads = ["windows_messagebox.bin", "windows_custom_reverse_tcp.bin",
            "windows_custom_reverse_http.bin", "windows_shell_reverse_tcp.bin"]

for p in payloads:
    path = os.path.join("original_pl", "x86", p)
    if not os.path.exists(path):
        continue
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        z = pobf86.Zone(path)
        z.mark_data_ranges32()
        printable = list(z.data_ranges32)
        try:
            sections = z.extract_data32()
        except Exception as e:
            print(p, "ERROR", e)
            continue
    print(f"\n=== {p}  ({len(z.raw_code)} B, {len(z.instructions)} instr)")
    print(f"  printable ranges (mark_data_ranges32): {len(printable)}")
    print(f"  extract_data32 sections: {len(sections)}")
    for s in sections:
        off, ln = s["offset"], s["length"]
        data = s["bytes"]
        printable_ratio = sum(1 for b in data if 32 <= b < 127) / max(1, ln)
        preview = data[:24].hex(" ")
        print(f"    off=0x{off:x} len={ln:3d} printable={printable_ratio:4.0%}  {preview}")
