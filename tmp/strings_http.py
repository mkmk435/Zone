import glob, os, re, struct

files = sorted(glob.glob(r"original_pl/**/*.bin", recursive=True))
for path in files:
    if "http" not in os.path.basename(path):
        continue
    data = open(path, "rb").read()
    strs = [(m.start(), m.group().decode("ascii")) for m in re.finditer(rb"[\x20-\x7e]{4,}", data)]
    print("=" * 80)
    print(path, len(data))
    for off, s in strs:
        print(f"  {off:04x}: {s!r}")
