import csv, os, re, collections

TECH = {"nop", "eq", "pii", "bcf", "ibp"}
rows = []
with open("test_report.txt", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) < 3:
            continue
        rows.append((row[0].strip(), row[2].strip().upper()))

def parse(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    stem = re.sub(r"\.bin$", "", os.path.basename(p))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in TECH:
        parts.pop()
    return arch, "_".join(parts)

stats = collections.defaultdict(lambda: [0, 0])
for path, res in rows:
    arch, base = parse(path)
    stats[(arch, base)][0] += 1
    if res == "OK":
        stats[(arch, base)][1] += 1

data = sorted(((a, b, ok, tot, ok / tot * 100) for (a, b), (tot, ok) in stats.items()),
              key=lambda x: (x[4], x[0], x[1]))

def table(items):
    print("| Payload | Arch | Working rate | OK/test |")
    print("|---|---|---:|---:|")
    for a, b, ok, tot, r in items:
        link = f"[{b}](original_pl/{a}/{b}.bin)"
        print(f"| {link} | {a} | {r:.1f}% | {ok}/{tot} |")

print("### <=3%")
table([d for d in data if d[4] <= 3.0])
print()
print("### 10-39%")
table([d for d in data if 9.9 <= d[4] <= 39.9])
