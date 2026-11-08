import csv, os, re, collections

rev = "tmp/test_report_reverse_fixed.txt"
msg = "tmp/test_report_msgbox_fixed.txt"

rows = []
for p in (rev, msg):
    with open(p, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.reader(f):
            if len(r) >= 3:
                rows.append(r[:3] + [r[3] if len(r) > 3 else ""])

print("rows:", len(rows))
print("status:", collections.Counter(r[2] for r in rows))

def parse_name(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    stem = re.sub(r"\.bin$", "", os.path.basename(p))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        parts.pop()
    return arch, "_".join(parts)

per = collections.defaultdict(lambda: [0, 0])
for r in rows:
    k = parse_name(r[0])
    per[k][0] += 1
    if r[2].upper() == "OK":
        per[k][1] += 1
print("payloads:", len(per))
for k, v in sorted(per.items()):
    print(f"  {k[0]} {k[1]:<44} {v[1]:3d}/{v[0]}")

# merged report, sorted by arch then name
rows.sort(key=lambda r: (r[0].split("/")[0], r[0]))
with open("test_report_x64_low_xd_ebi.txt", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

# old stats
old = collections.defaultdict(lambda: [0, 0])
with open("test_report.txt", newline="", encoding="utf-8", errors="replace") as f:
    for r in csv.reader(f):
        if len(r) < 3:
            continue
        k = parse_name(r[0])
        old[k][0] += 1
        if r[2].strip().upper() == "OK":
            old[k][1] += 1

with open("working_rate_x64_low_xd_ebi.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arch", "payload", "old_ok", "old_total", "old_rate_pct",
                "new_ok", "new_total", "new_rate_pct", "delta_pct"])
    for (a, b), (nt, nk) in sorted(per.items(), key=lambda kv: kv[1][1] / kv[1][0]):
        ot, ok = old.get((a, b), [0, 0])
        o = ok / ot * 100 if ot else 0
        n = nk / nt * 100 if nt else 0
        w.writerow([a, b, ok, ot, f"{o:.1f}", nk, nt, f"{n:.1f}", f"{n-o:+.1f}"])
print("written test_report_x64_low_xd_ebi.txt and working_rate_x64_low_xd_ebi.csv")
