import re

for f in ("pobf.py", "pobf86.py"):
    src = open(f, encoding="utf-8", errors="replace").read().splitlines()
    print("=" * 20, f, len(src), "lines")
    for i, l in enumerate(src, 1):
        m = re.match(r"\s*def (\w+)", l)
        if m:
            print(f"  {i:6d} {m.group(1)}")
