import csv, os, re, collections

def base(name):
    stem = re.sub(r"\.bin$", "", os.path.basename(name.replace("\\", "/")))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        parts.pop()
    return "_".join(parts)

def load(path):
    d = collections.defaultdict(lambda: [0, 0])
    for r in csv.reader(open(path, encoding="utf-8", errors="replace")):
        if len(r) < 3:
            continue
        k = base(r[0])
        d[k][0] += 1
        if r[2].strip().upper() == "OK":
            d[k][1] += 1
    return d

old = load("test_report.txt")
pre = load("test_report_x64_low_xd_ebi_5001.txt")
post = load("test_report_x64_low_getpc.txt")

rows = []
for b, (nt, nk) in post.items():
    ot, ok = old.get(b, [0, 0])
    pt, pk = pre.get(b, [0, 0])
    o = ok / ot * 100 if ot else 0
    p = pk / pt * 100 if pt else 0
    n = nk / nt * 100 if nt else 0
    rows.append((n, b, ok, ot, o, pk, pt, p, nk, nt, n, n - p))

rows.sort()
with open("working_rate_x64_low_getpc.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arch", "payload", "old_ok", "old_total", "old_rate_pct",
                "pre_ok", "pre_total", "pre_rate_pct",
                "new_ok", "new_total", "new_rate_pct", "delta_pre_to_new_pct"])
    for n, b, ok, ot, o, pk, pt, p, nk, nt, nn, d in rows:
        w.writerow(["x64", b, ok, ot, f"{o:.1f}", pk, pt, f"{p:.1f}",
                    nk, nt, f"{nn:.1f}", f"{d:+.1f}"])
print("updated working_rate_x64_low_getpc.csv")
