import json, re, collections, statistics, random

TECHS = ["eq_nop_pii","eq_nop_bcf","eq_nop_ibp","nop_pii","nop_bcf","nop_ibp",
         "eq_pii","eq_bcf","eq_ibp","eq_nop","nop_eq",
         "pii","bcf","ibp","eq","nop"]

def parse(name):
    b = re.sub(r"_\d+$", "", name)
    for t in TECHS:
        if b.endswith("_" + t):
            return b[: -(len(t) + 1)], t
    return None, None

rows = json.load(open("results.json", encoding="utf-8"))
cell = collections.defaultdict(list)   # (arch,payload,tech) -> [per-file rates]
for r in rows:
    f = r["file"].lower()
    if "\\mutations\\" not in f: continue
    arch = "x64" if "\\x64\\" in f else "x86"
    payload, tech = parse(r["file"].rsplit("\\", 1)[-1][:-4])
    if not tech: continue
    cell[(arch, payload, tech)].append(100.0 * r["malicious"] / r["total_scans"])

def mean(xs): return sum(xs)/len(xs) if xs else 0.0

for arch in ("x64","x86"):
    payloads = sorted({p for (a,p,t) in cell if a==arch})
    # per-payload mean across techniques, per-technique mean across payloads
    pm = {p: mean([mean(v) for (a,pp,t),v in cell.items() if a==arch and pp==p]) for p in payloads}
    tm = {t: mean([mean(v) for (a,p,tt),v in cell.items() if a==arch and tt==t]) for t in TECHS}
    print(f"\n=== {arch}: payload means (across techniques), sorted ===")
    for p,v in sorted(pm.items(), key=lambda x:-x[1])[:6]:
        print(f"  {v:6.2f}%  {p}")
    print("  ... lowest:")
    for p,v in sorted(pm.items(), key=lambda x:x[1])[:4]:
        print(f"  {v:6.2f}%  {p}")

    # rank correlation payload-profile between techniques (Spearman on shared payloads)
    def rankmap(t):
        vals = [(pm[p], p) for p in payloads]
        return {p:i for i,(v,p) in enumerate(sorted(vals))}
    rk = {t: rankmap(t) for t in TECHS}
    # correlation between technique mean ordering and payload ordering is not it;
    # instead: does payload ranking agree across techniques that are both non-zero?
    print("  variance of payload means:", round(statistics.pvariance(pm.values()),3))
    print("  variance of technique means:", round(statistics.pvariance(tm.values()),3))
    print("  top-3 techniques:", sorted(tm.items(), key=lambda x:-x[1])[:3])
