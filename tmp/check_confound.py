import json, re, statistics, collections

TECHS = ["eq_nop_pii","eq_nop_bcf","eq_nop_ibp","nop_pii","nop_bcf","nop_ibp",
         "eq_pii","eq_bcf","eq_ibp","eq_nop","nop_eq",
         "pii","bcf","ibp","eq","nop"]

def parse(name):
    b = re.sub(r"_\d+$", "", name)          # strip variant index
    for t in TECHS:
        if b.endswith("_" + t):
            return b[: -(len(t) + 1)], t
    return None, None

rows = json.load(open("results.json", encoding="utf-8"))
data = collections.defaultdict(list)
skipped = 0
for r in rows:
    f = r["file"]
    if "\\mutations\\" not in f.lower():
        continue
    arch = "x64" if "\\x64\\" in f.lower() else "x86"
    payload, tech = parse(f.rsplit("\\", 1)[-1][:-4])
    if tech is None:
        skipped += 1
        continue
    rate = 100.0 * r["malicious"] / r["total_scans"]
    data[(arch, tech)].append((r["date"], rate, payload))

print(f"rows mapped: {sum(len(v) for v in data.values())}, skipped: {skipped}")

for arch in ("x64", "x86"):
    print(f"\n=== {arch} ===")
    print(f"{'tech':<12}{'n':>5}{'mean%':>9}{'dates':>26}")
    for t in TECHS:
        v = data.get((arch, t), [])
        if not v:
            continue
        ds = sorted(x[0] for x in v)
        mean = statistics.mean(x[1] for x in v)
        print(f"{t:<12}{len(v):>5}{mean:>9.2f}{ds[0][:10]:>14} -> {ds[-1][:10]}")

# correlation date vs detection overall
allv = [x for v in data.values() for x in v]
print("\ntotal mapped:", len(allv))
