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

stats = collections.defaultdict(lambda: [0, 0, collections.defaultdict(lambda: [0, 0])])
for path, op, res in rows:
    arch, base, tech = parse(path)
    s = stats[(arch, base)]
    s[0] += 1
    if res == "OK":
        s[1] += 1
    s[2][tech][0] += 1
    if res == "OK":
        s[2][tech][1] += 1

data = []
for (arch, base), (tot, ok, techs) in stats.items():
    data.append({"arch": arch, "base": base, "ok": ok, "tot": tot,
                 "rate": ok / tot * 100 if tot else 0.0,
                 "techs": {t: (v[1], v[0]) for t, v in techs.items()}})
data.sort(key=lambda d: (d["rate"], d["arch"], d["base"]))

# write full csv
with open("tmp/original_pl_working_rates.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arch", "payload", "ok", "total", "working_rate_pct", "best_technique", "best_rate_pct"])
    for d in data:
        best = max(d["techs"].items(), key=lambda kv: (kv[1][0] / kv[1][1] if kv[1][1] else 0, kv[1][0]))
        br = best[1][0] / best[1][1] * 100 if best[1][1] else 0
        w.writerow([d["arch"], d["base"], d["ok"], d["tot"], f'{d["rate"]:.1f}',
                    f'{best[0]} ({best[1][0]}/{best[1][1]})', f"{br:.1f}"])

print("=== <= 3% ===")
for d in data:
    if d["rate"] <= 3.0:
        print(f'{d["rate"]:5.1f}%  {d["ok"]:3d}/{d["tot"]:<3d}  {d["arch"]:<4} {d["base"]}')

print("\n=== 10% - 39% ===")
for d in data:
    if 9.9 <= d["rate"] <= 39.9:
        print(f'{d["rate"]:5.1f}%  {d["ok"]:3d}/{d["tot"]:<3d}  {d["arch"]:<4} {d["base"]}')

print("\n=== >= 70% ===")
n = sum(1 for d in data if d["rate"] >= 70)
print("count:", n)
print("\nTotals:", len(data), "payloads;")
for arch in ("x86", "x64"):
    sub = [d for d in data if d["arch"] == arch]
    tot = sum(d["tot"] for d in sub)
    ok = sum(d["ok"] for d in sub)
    print(f"  {arch}: {ok}/{tot} = {ok/tot*100:.1f}%")
