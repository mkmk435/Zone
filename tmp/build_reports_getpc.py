import csv, os, re, collections

GOOD = {
    "windows_x64_custom_reverse_http",
    "windows_x64_custom_reverse_https",
    "windows_x64_meterpreter_reverse_winhttp",
    "windows_x64_meterpreter_reverse_winhttps",
    "windows_x64_messagebox",
}
BROKEN = {
    "windows_x64_meterpreter_reverse_http",
    "windows_x64_vncinject_reverse_http",
    "windows_x64_custom_reverse_winhttp",
    "windows_x64_custom_reverse_winhttps",
    "windows_x64_meterpreter_reverse_https",
    "windows_x64_vncinject_reverse_https",
    "windows_x64_vncinject_reverse_winhttp",
    "windows_x64_vncinject_reverse_winhttps",
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
        if not os.path.exists(p):
            continue
        for r in csv.reader(open(p, encoding="utf-8", errors="replace")):
            if len(r) < 3:
                continue
            stats[base(r[0])][0] += 1
            if r[2].strip().upper() == "OK":
                stats[base(r[0])][1] += 1
    return stats

rev = "tmp/test_report_reverse_getpc.txt"
msg = "tmp/test_report_msgbox_getpc.txt"
new = load([rev, msg])
old = load(["test_report.txt"])
prev = load(["test_report_x64_low_xd_ebi_5001.txt"])

print(f"{'payload':<45} {'old':>11} {'5.0.0.post1':>13} {'getpc fix':>13}")
print("-" * 90)
for b in sorted(new, key=lambda x: new[x][1] / new[x][0]):
    ot, ok = old.get(b, [0, 0]); pt, pk = prev.get(b, [0, 0]); nt, nk = new[b]
    o = ok / ot * 100 if ot else 0
    p = pk / pt * 100 if pt else 0
    n = nk / nt * 100 if nt else 0
    print(f"{b:<45} {o:5.1f}% {ok:3d}/{ot:<3d} {p:5.1f}% {pk:3d}/{pt:<3d} {n:6.1f}% {nk:3d}/{nt:<3d}")

def agg(subset, exclude_ibp=False):
    t = k = 0
    for p in subset:
        for r in csv.reader(open("tmp/test_report_reverse_getpc.txt", encoding="utf-8", errors="replace")):
            if len(r) < 3 or base(r[0]) != p:
                continue
            if exclude_ibp and "ibp" in tech(r[0]):
                continue
            t += 1; k += r[2].upper() == "OK"
    return k, t

# merged report + csv
rows = []
for p in (rev, msg):
    if not os.path.exists(p):
        continue
    for r in csv.reader(open(p, encoding="utf-8", errors="replace")):
        if len(r) >= 3:
            rows.append(r[:3])
rows.sort(key=lambda r: (r[0].split("/")[0], r[0]))
with open("test_report_x64_low_getpc.txt", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)

with open("working_rate_x64_low_getpc.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["arch", "payload", "old_ok", "old_total", "old_rate_pct",
                "new_ok", "new_total", "new_rate_pct", "delta_pct"])
    for b in sorted(new, key=lambda x: new[x][1] / new[x][0]):
        ot, ok = old.get(b, [0, 0]); nt, nk = new[b]
        o = ok / ot * 100 if ot else 0; n = nk / nt * 100 if nt else 0
        w.writerow(["x64", b, ok, ot, f"{o:.1f}", nk, nt, f"{n:.1f}", f"{n-o:+.1f}"])

all_k = sum(v[1] for v in new.values()); all_t = sum(v[0] for v in new.values())
g_k, g_t = agg(GOOD); b_k, b_t = agg(BROKEN)
print()
print(f"TOTALE 13 payload: {all_k}/{all_t} = {all_k/all_t*100:.1f}%")
print(f"5 gia' buoni: {g_k}/{g_t} = {g_k/g_t*100:.1f}%")
print(f"8 ex rotti: {b_k}/{b_t} = {b_k/b_t*100:.1f}%")
print(f"8 ex rotti senza -ibp: ", end="")
tb = tk = 0
for p in BROKEN:
    for r in csv.reader(open("tmp/test_report_reverse_getpc.txt", encoding="utf-8", errors="replace")):
        if len(r) < 3 or base(r[0]) != p or "ibp" in tech(r[0]):
            continue
        tb += 1; tk += r[2].upper() == "OK"
print(f"{tk}/{tb} = {tk/tb*100:.1f}%")
