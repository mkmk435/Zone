import os, shutil, sys
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else "mutations_fixed_5001/x64")
dst = Path(sys.argv[2] if len(sys.argv) > 2 else "tmp/test_reverse_5001/x64")
dst.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted(src.glob("*.bin")):
    if "messagebox" in f.name:
        continue
    t = dst / f.name
    if t.exists():
        continue
    try:
        os.link(f, t)
    except OSError:
        shutil.copy2(f, t)
    n += 1
print("staged", n, "reverse mutations in", dst)
