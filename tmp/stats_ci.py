import json, re, collections, math

TECHS = ["eq_nop_pii","eq_nop_bcf","eq_nop_ibp","nop_pii","nop_bcf","nop_ibp",
         "eq_pii","eq_bcf","eq_ibp","eq_nop","nop_eq",
         "pii","bcf","ibp","eq","nop"]

def parse(name):
    b = re.sub(r"_\d+$", "", name)
    for t in TECHS:
        if b.endswith("_" + t):
            return b[: -(len(t) + 1)], t
    return None, None

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    r = z*math.sqrt(max(p*(1-p)/n + z*z/(4*n*n), 0.0))
    return ((c - r)/d*100, (c + r)/d*100)

rows = json.load(open("results.json", encoding="utf-8"))
S = collections.defaultdict(lambda: [0, 0, 0])   # files, engine-scans, detections
B = collections.defaultdict(lambda: [0, 0])
for r in rows:
    f = r["file"].lower()
    if "\\mutations\\" not in f: continue
    arch = "x64" if "\\x64\\" in f else "x86"
    _, tech = parse(r["file"].rsplit("\\", 1)[-1][:-4])
    if not tech: continue
    s = S[(arch, tech)]
    s[0] += 1; s[1] += r["total_scans"]; s[2] += r["malicious"]
    b = "spring" if r["date"] < "2025-06-01" else "autumn"
    B[(arch, b)][0] += r["total_scans"]; B[(arch, b)][1] += r["malicious"]

for arch in ("x64", "x86"):
    print(f"\n=== {arch} ===")
    print(f"{'tech':<12}{'files':>6}{'scans':>7}{'det':>5}{'rate%':>8}   95% CI (engine-level)")
    for t in TECHS:
        n, sc, k = S[(arch, t)]
        if not n: continue
        lo, hi = wilson(k, sc)
        print(f"{t:<12}{n:>6}{sc:>7}{k:>5}{100*k/sc:>8.2f}   [{lo:.2f}, {hi:.2f}]")
    # zero-detection techniques: file-level upper bound
    print("  zero-detection techniques, file-level 95% upper bound (rule of three):")
    for t in TECHS:
        n, sc, k = S[(arch, t)]
        if n and k == 0:
            print(f"    {t:<10} 0/{n} files -> < {300/n:.2f}% of files")

print("\n=== batches ===")
for k_, (sc, d) in sorted(B.items()):
    print(k_, "scans:", sc, "det:", d, f"{100*d/sc:.3f}%")
