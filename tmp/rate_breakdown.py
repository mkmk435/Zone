import csv, os, re, collections

TECH = {"nop", "eq", "pii", "bcf", "ibp"}

rows = []
with open("test_report.txt", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) < 3:
            continue
        rows.append((row[0].strip(), row[1].strip(), row[2].strip().upper()))

def parse(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    name = os.path.basename(p)
    stem = re.sub(r"\.bin$", "", name)
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    tech = []
    while parts and parts[-1] in TECH:
        tech.append(parts.pop())
    return arch, "_".join(parts), "_".join(reversed(tech))

stats = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for path, op, res in rows:
    arch, base, tech = parse(path)
    stats[(arch, base)][tech][0] += 1
    if res == "OK":
        stats[(arch, base)][tech][1] += 1

# all original names
orig = set()
for root, _, files in os.walk("original_pl"):
    for fn in files:
        if fn.endswith(".bin"):
            orig.add((os.path.basename(root), fn[:-4]))

bases = set(stats)
print("bases in report:", len(bases), "| original files:", len(orig))
print("in report not in original_pl:")
for a, b in sorted(bases - orig):
    print("   ", a, b)
print("in original_pl but not in report:")
for a, b in sorted(orig - bases):
    print("   ", a, b)

print("\nERROR rows:")
for path, op, res in rows:
    if res == "ERROR":
        print("   ", path, op, res)

# per-technique breakdown for lowest bases
sel = [
    ("x64", "windows_x64_custom_reverse_https"),
    ("x64", "windows_x64_custom_reverse_http"),
    ("x86", "windows_messagebox"),
    ("x64", "windows_x64_messagebox"),
    ("x86", "windows_custom_reverse_nonx_tcp"),
    ("x86", "windows_vncinject_reverse_winhttp"),
    ("x86", "windows_vncinject_reverse_tcp"),
]
for key in sel:
    print("\n==", key, "total:", sum(v[0] for v in stats[key].values()))
    for tech in sorted(stats[key]):
        tot, ok = stats[key][tech]
        print(f"   {tech:<12} {ok:3d}/{tot:<3d}  {ok/tot*100 if tot else 0:5.1f}%")
