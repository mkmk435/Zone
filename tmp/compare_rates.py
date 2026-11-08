import csv, os, re, collections, sys

TECH = {"nop", "eq", "pii", "bcf", "ibp"}

def parse_name(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    stem = re.sub(r"\.bin$", "", os.path.basename(p))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in TECH:
        parts.pop()
    return arch, "_".join(parts)

def load_old(path):
    stats = collections.defaultdict(lambda: [0, 0])
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            arch, base = parse_name(row[0])
            stats[(arch, base)][0] += 1
            if row[2].strip().upper() == "OK":
                stats[(arch, base)][1] += 1
    return stats

def load_new(paths):
    stats = collections.defaultdict(lambda: [0, 0])
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.reader(f):
                if len(row) < 3:
                    continue
                arch, base = parse_name(row[0])
                stats[(arch, base)][0] += 1
                if row[2].strip().upper() == "OK":
                    stats[(arch, base)][1] += 1
    return stats

old = load_old("test_report.txt")
new = load_new(["tmp/test_report_reverse_fixed.txt", "tmp/test_report_msgbox_fixed.txt"])

payloads = sorted([k for k in new if k[0] == "x64"], key=lambda k: (old.get(k, [1, 0])[1] / old.get(k, [1, 1])[0]))
print(f"{'payload':<48} {'old':>12} {'new':>12} {'delta':>8}")
print("-" * 84)
tot_old = [0, 0]
tot_new = [0, 0]
for k in payloads:
    o_t, o_k = old.get(k, [0, 0])
    n_t, n_k = new[k]
    o = o_k / o_t * 100 if o_t else 0
    n = n_k / n_t * 100 if n_t else 0
    print(f"{k[1]:<48} {o:6.1f}% {o_k:3d}/{o_t:<3d} {n:6.1f}% {n_k:3d}/{n_t:<3d} {n-o:+7.1f}")
    tot_old[0] += o_t; tot_old[1] += o_k
    tot_new[0] += n_t; tot_new[1] += n_k
print("-" * 84)
print(f"{'TOTALE':<48} {tot_old[1]/tot_old[0]*100:6.1f}% {tot_old[1]:3d}/{tot_old[0]:<3d} "
      f"{tot_new[1]/tot_new[0]*100:6.1f}% {tot_new[1]:3d}/{tot_new[0]:<3d} "
      f"{(tot_new[1]/tot_new[0]-tot_old[1]/tot_old[0])*100:+7.1f}")
