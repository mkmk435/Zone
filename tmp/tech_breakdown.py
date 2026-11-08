import csv, re, collections

def tech_of(name):
    stem = re.sub(r"\.bin$", "", name)
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    toks = []
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        toks.append(parts.pop())
    return "_".join(reversed(toks))

for report, label in [("tmp/test_report_msgbox_fixed.txt", "messagebox")]:
    stats = collections.defaultdict(lambda: [0, 0])
    for row in csv.reader(open(report)):
        if len(row) < 3:
            continue
        t = tech_of(row[0].split("/")[-1])
        stats[t][0] += 1
        if row[2].upper() == "OK":
            stats[t][1] += 1
    print("==", label)
    for t in sorted(stats):
        ok, tot = stats[t][1], stats[t][0]
        print(f"  {t:<12} {ok:3d}/{tot:<3d} {ok/tot*100:5.1f}%")
    tot = sum(v[0] for v in stats.values()); ok = sum(v[1] for v in stats.values())
    print(f"  {'TOTAL':<12} {ok:3d}/{tot:<3d} {ok/tot*100:5.1f}%")
