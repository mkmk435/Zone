import os, sys, io, contextlib, random, traceback
sys.path.insert(0, r"C:\Users\ubu\Desktop\Zone")
os.chdir(r"C:\Users\ubu\Desktop\Zone")
import pobf
print("start", flush=True)
random.seed(1234)
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        z = pobf.Zone(os.path.join("original_pl", "x64", "windows_x64_messagebox.bin"))
        z.create_label_table()
        z.bogus_control_flow()
        print("bcf done")
    print("instrs", len(z.instructions), flush=True)
except BaseException as e:
    print("EXC", type(e).__name__, e, file=sys.stderr)
    traceback.print_exc()
print("END", flush=True)
