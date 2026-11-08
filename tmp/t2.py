import os, sys, io, contextlib, random
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
os.chdir(r"C:\Users\ubu\Desktop\Zone")
import pobf
print("import done", flush=True)
for p in ["windows_x64_messagebox.bin", "windows_x64_custom_reverse_tcp.bin"]:
    print("payload", p, flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        z = pobf.Zone(os.path.join("original_pl", "x64", p))
    print("  instrs", len(z.instructions), flush=True)
print("END", flush=True)
