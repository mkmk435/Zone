import os, shutil
from pathlib import Path

src = Path("mutations_fixed/x64")
dst = Path("tmp/test_reverse/x64")
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
