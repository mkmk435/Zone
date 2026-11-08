import csv, re, collections

def tech(name):
    stem = re.sub(r"\.bin$", "", name.split("/")[-1])
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    toks = []
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        toks.append(parts.pop())
    return "_".join(reversed(toks))

def base(name):
    stem = re.sub(r"\.bin$", "", name.split("/")[-1])
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        parts.pop()
    return "_".join(parts)

def stats(path, only=None):
    d = collections.defaultdict(lambda: [0, 0])
    for r in csv.reader(open(path, encoding="utf-8", errors="replace")):
        if len(r) < 3:
            continue
        if only is not None and base(r[0]) not in only:
            continue
        t = tech(r[0])
        d[t][0] += 1
        if r[2].upper() == "OK":
            d[t][1] += 1
    return d

new = stats("test_report_x64_low_xd_ebi.txt")
only = {base(p) for p in []}
# payload set = bases present in new report
import os
only = set()
for r in csv.reader(open("test_report_x64_low_xd_ebi.txt", encoding="utf-8", errors="replace")):
    if len(r) >= 3:
        only.add(base(r[0]))
old = stats("test_report.txt", only)
print(f"{'tech':<12} {'old':>12} {'new':>12}")
for t in sorted(new):
    o = old.get(t, [0, 0])
    orate = o[1] / o[0] * 100 if o[0] else 0
    nrate = new[t][1] / new[t][0] * 100 if new[t][0] else 0
    print(f"{t:<12} {orate:6.1f}% {o[1]:3d}/{o[0]:<3d} {nrate:6.1f}% {new[t][1]:3d}/{new[t][0]:<3d}")
