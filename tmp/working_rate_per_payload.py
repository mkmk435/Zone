import csv, os, re, collections

TECH = {"nop", "eq", "pii", "bcf", "ibp"}

rows = []
with open("test_report.txt", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) < 3:
            continue
        path, op, result = row[0].strip(), row[1].strip(), row[2].strip().upper()
        rows.append((path, op, result))

print("rows:", len(rows))
prefixes = collections.Counter(p.split("/")[0] for p, _, _ in rows)
print("prefixes:", prefixes.most_common(10))

def parse(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    name = os.path.basename(p)
    stem = re.sub(r"\.bin$", "", name)
    stem = re.sub(r"_\d+$", "", stem)  # instance
    parts = stem.split("_")
    tech = []
    while parts and parts[-1] in TECH:
        tech.append(parts.pop())
    return arch, "_".join(parts), "_".join(reversed(tech))

stats = collections.defaultdict(lambda: [0, 0, collections.Counter()])
bad = []
for path, op, res in rows:
    arch, base, tech = parse(path)
    if not tech:
        bad.append(path)
        continue
    key = (arch, base)
    stats[key][0] += 1
    if res == "OK":
        stats[key][1] += 1
    stats[key][2][res] += 1

print("unparsed/no technique:", len(bad), bad[:5])
print("distinct base payloads:", len(stats))

rates = []
for (arch, base), (tot, ok, cnt) in stats.items():
    rates.append((ok / tot * 100, tot, ok, arch, base, cnt))
rates.sort()

print(f"\n{'rate%':>6} {'ok':>4} {'tot':>4}  arch  base")
for r, tot, ok, arch, base, cnt in rates:
    print(f"{r:6.1f} {ok:4d} {tot:4d}  {arch:<4}  {base}")
