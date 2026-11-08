import csv, os, re, collections

GOOD = {
    "windows_x64_custom_reverse_http",
    "windows_x64_custom_reverse_https",
    "windows_x64_meterpreter_reverse_winhttp",
    "windows_x64_meterpreter_reverse_winhttps",
    "windows_x64_messagebox",
}

def base(name):
    stem = re.sub(r"\.bin$", "", os.path.basename(name.replace("\\", "/")))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        parts.pop()
    return "_".join(parts)

def tech(name):
    stem = re.sub(r"\.bin$", "", os.path.basename(name.replace("\\", "/")))
    stem = re.sub(r"_\d+$", "", stem)
    parts = stem.split("_")
    toks = []
    while parts and parts[-1] in {"nop", "eq", "pii", "bcf", "ibp"}:
        toks.append(parts.pop())
    return "_".join(reversed(toks))

def load(paths):
    stats = collections.defaultdict(lambda: [0, 0])
    for p in paths:
        for r in csv.reader(open(p, encoding="utf-8", errors="replace")):
            if len(r) < 3:
                continue
            k = base(r[0])
            stats[k][0] += 1
            if r[2].strip().upper() == "OK":
                stats[k][1] += 1
    return stats

paths = ["tmp/test_report_reverse_5001.txt", "tmp/test_report_msgbox_5001.txt"]
new = load(paths)
old = load(["test_report.txt"])
prev = load(["test_report_x64_low_xd_ebi.txt"])

print(f"{'payload':<45} {'old':>12} {'5.0.6':>12} {'5.0.0.post1':>14} {'delta vs old':>13}")
print("-" * 100)
for b in sorted(new, key=lambda x: new[x][1] / new[x][0]):
    ot, ok = old.get(b, [0, 0]); pt, pk = prev.get(b, [0, 0]); nt, nk = new[b]
    o = ok / ot * 100 if ot else 0
    p = pk / pt * 100 if pt else 0
    n = nk / nt * 100 if nt else 0
    print(f"{b:<45} {o:5.1f}% {ok:3d}/{ot:<3d} {p:5.1f}% {pk:3d}/{pt:<3d} {n:6.1f}% {nk:3d}/{nt:<3d} {n-o:+12.1f}")

def agg(subset, exclude_ibp=False):
    t = k = 0
    for p in subset:
        for r in csv.reader(open("test_report_x64_low_xd_ebi_5001.txt", encoding="utf-8", errors="replace")):
            if len(r) < 3:
                continue
            if base(r[0]) != p:
                continue
            if exclude_ibp and "ibp" in tech(r[0]):
                continue
            t += 1
            if r[2].upper() == "OK":
                k += 1
    return k, t

# write merged report + csv
rows = []
for p in paths:
    for r in csv.reader(open(p, encoding="utf-8", errors="replace")):
        if len(r) >= 3:
            rows.append(r[:3])
rows.sort(key=lambda r: (r[0].split("/")[0], r[0]))
with open("test_report_x64_low_xd_ebi_5001.txt", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

with open("working_rate_x64_low_xd_ebi_5001.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arch", "payload", "old_ok", "old_total", "old_rate_pct",
                "new_ok", "new_total", "new_rate_pct", "delta_pct"])
    for b in sorted(new, key=lambda x: new[x][1] / new[x][0]):
        ot, ok = old.get(b, [0, 0]); nt, nk = new[b]
        o = ok / ot * 100 if ot else 0; n = nk / nt * 100 if nt else 0
        w.writerow(["x64", b, ok, ot, f"{o:.1f}", nk, nt, f"{n:.1f}", f"{n-o:+.1f}"])

all_k = sum(v[1] for v in new.values()); all_t = sum(v[0] for v in new.values())
g_k, g_t = agg(GOOD)
gb_k, gb_t = agg(GOOD, exclude_ibp=True)
print()
print(f"TOTALE 13 payload: {all_k}/{all_t} = {all_k/all_t*100:.1f}%")
print(f"5 payload non rotti: {g_k}/{g_t} = {g_k/g_t*100:.1f}%")
print(f"5 payload non rotti, senza tecniche -ibp: {gb_k}/{gb_t} = {gb_k/gb_t*100:.1f}%")
old_good_t = sum(old.get(b, [0, 0])[0] for b in GOOD)
old_good_k = sum(old.get(b, [0, 0])[1] for b in GOOD)
print(f"5 payload non rotti, vecchio: {old_good_k}/{old_good_t} = {old_good_k/old_good_t*100:.1f}%")
