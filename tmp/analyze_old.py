import csv, os, re, collections, json

TECH = {"nop", "eq", "pii", "bcf", "ibp"}

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

rows = []
with open("test_report.txt", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) < 3:
            continue
        rows.append((row[0].strip(), row[1].strip(), row[2].strip().upper()))

stats = collections.defaultdict(lambda: [0, 0, collections.Counter(), collections.defaultdict(lambda: [0,0])])
bad = []
for path, op, res in rows:
    arch, base, tech = parse(path)
    if not tech:
        bad.append((path, res))
        continue
    s = stats[(arch, base)]
    s[0] += 1
    if res == "OK":
        s[1] += 1
    s[2][res] += 1
    s[3][tech][0] += 1
    if res == "OK":
        s[3][tech][1] += 1

print("rows:", len(rows), "| parsed payloads:", len(stats), "| unparsed:", len(bad), bad[:5])
print("messages per payload distribution:", collections.Counter(v[0] for v in stats.values()))

orig = set()
for arch in ("x64", "x86"):
    for fn in os.listdir(f"original_pl/{arch}"):
        if fn.endswith(".bin"):
            orig.add((arch, fn[:-4]))
print("original files:", len(orig), "| in report:", len(set(stats)))
print("missing from report:", sorted(orig - set(stats)))
print("extra in report:", sorted(set(stats) - orig))

buckets = collections.Counter()
for (arch, base), (tot, ok, cnt, techs) in stats.items():
    r = ok / tot * 100
    if r == 0: b = "0%"
    elif r < 10: b = "0-10%"
    elif r < 25: b = "10-25%"
    elif r < 50: b = "25-50%"
    elif r < 75: b = "50-75%"
    else: b = "75-100%"
    buckets[b] += 1
print("buckets:", dict(buckets))

def line(key):
    arch, base = key
    tot, ok, cnt, techs = stats[key]
    return f"{ok/tot*100:6.1f}% {ok:4d}/{tot:<4d} {arch:<4} {base}"

print("\n=== payloads sorted by old working rate ===")
for key in sorted(stats, key=lambda k: (stats[k][1]/stats[k][0], k)):
    tot, ok, cnt, techs = stats[key]
    print(line(key))

print("\n=== <50% per technique ===")
for key in sorted(stats, key=lambda k: (stats[k][1]/stats[k][0], k)):
    tot, ok, cnt, techs = stats[key]
    if ok/tot >= 0.5:
        continue
    print(f"{key[0]:<4} {key[1]:<42} {ok/tot*100:5.1f}%  " + "  ".join(
        f"{t}:{v[1]}/{v[0]}" for t, v in sorted(techs.items())))
