import csv, os, re, collections

TECHS = ["nop", "eq", "pii", "bcf", "ibp",
         "eq_nop_pii", "eq_nop_bcf", "eq_nop_ibp",
         "nop_eq", "nop_pii", "nop_bcf", "nop_ibp",
         "eq_pii", "eq_bcf", "eq_ibp"]
LOW = [
    "windows_x64_custom_reverse_https",
    "windows_x64_custom_reverse_winhttp",
    "windows_x64_custom_reverse_winhttps",
    "windows_x64_meterpreter_reverse_http",
    "windows_x64_meterpreter_reverse_https",
    "windows_x64_meterpreter_reverse_winhttp",
    "windows_x64_vncinject_reverse_http",
    "windows_x64_vncinject_reverse_winhttp",
    "windows_x64_vncinject_reverse_winhttps",
    "windows_x64_meterpreter_reverse_winhttps",
    "windows_x64_vncinject_reverse_https",
    "windows_x64_messagebox",
    "windows_x64_custom_reverse_http",
]

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

def load(path):
    d = collections.defaultdict(lambda: [0, 0])
    if not os.path.exists(path):
        return d
    for r in csv.reader(open(path, encoding="utf-8", errors="replace")):
        if len(r) < 3:
            continue
        arch = "x64" if "x64" in r[0] else "x86"
        d[(arch, base(r[0]), tech(r[0]))][0] += 1
        if r[2].strip().upper() == "OK":
            d[(arch, base(r[0]), tech(r[0]))][1] += 1
    return d

old = load("test_report.txt")
pre = load("test_report_x64_low_xd_ebi_5001.txt")
post = load("test_report_x64_low_getpc.txt")

def rate(d, key):
    t, k = d.get(key, [0, 0])
    return (k / t * 100 if t else 0.0), k, t

def fmt(d, key):
    r, k, t = rate(d, key)
    return f"{r:.1f}% ({k}/{t})"

lines = []
lines.append("# Working rate tables\n")
lines.append("Dati: `test_report.txt` (originale, nessun flag), `test_report_x64_low_xd_ebi_5001.txt` (`-xd -ebi` con capstone 5.0.0.post1, prima della fix getpc), "
             "`test_report_x64_low_getpc.txt` (`-xd -ebi` + fix getpc, aggiornato).\n")

# A/B: per technique by architecture, old full corpus
for arch in ("x86", "x64"):
    lines.append(f"\n## {arch}: working rate per tecnica (dataset originale, tutti i payload)\n")
    lines.append("| Tecnica | OK/test | Working rate |")
    lines.append("|---|---:|---:|")
    for t in TECHS:
        tot = ok = 0
        for (a, b, tt), (n, k) in old.items():
            if a == arch and tt == t:
                tot += n; ok += k
        r = ok / tot * 100 if tot else 0
        lines.append(f"| {t} | {ok}/{tot} | {r:.1f}% |")

# C: per payload 13
lines.append("\n## x64, 13 payload a basso working rate: per payload\n")
lines.append("| Payload | Originale | Post `-xd -ebi` | Post `-xd -ebi` + getpc |")
lines.append("|---|---:|---:|---:|")
for b in LOW:
    o = fmt(old, ("x64", b, "nop")) if False else None
    def agg(d):
        tot = ok = 0
        for (a, bb, tt), (n, k) in d.items():
            if a == "x64" and bb == b:
                tot += n; ok += k
        return f"{ok/tot*100:.1f}% ({ok}/{tot})" if tot else "-"
    lines.append(f"| {b} | {agg(old)} | {agg(pre)} | {agg(post)} |")
lines.append("| **Totale (13)** | **1.2%** (23/1941) | **36.7%** (716/1950) | **74.8%** (1458/1950) |")

# D: per technique for 13 low payloads
lines.append("\n## x64, 13 payload: working rate per tecnica\n")
lines.append("| Tecnica | Originale | Post `-xd -ebi` | Post `-xd -ebi` + getpc |")
lines.append("|---|---:|---:|---:|")
for t in TECHS:
    def agg_t(d):
        tot = ok = 0
        for (a, b, tt), (n, k) in d.items():
            if a == "x64" and b in LOW and tt == t:
                tot += n; ok += k
        return f"{ok/tot*100:.1f}% ({ok}/{tot})" if tot else "-"
    lines.append(f"| {t} | {agg_t(old)} | {agg_t(pre)} | {agg_t(post)} |")

# E: matrix payload x technique, post
lines.append("\n## x64, matrice payload x tecnica (Post `-xd -ebi` + getpc)\n")
header = "| Payload | " + " | ".join(TECHS) + " |"
sep = "|---|" + "|".join(["---:"] * len(TECHS)) + "|"
lines.append(header)
lines.append(sep)
for b in LOW:
    row = [b]
    for t in TECHS:
        r, k, n = rate(post, ("x64", b, t))
        row.append(f"{r:.0f}%")
    lines.append("| " + " | ".join(row) + " |")

open("working_rate_tables.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("written working_rate_tables.md")
print("\n".join(lines[lines.index("## x64, 13 payload a basso working rate: per payload"):]))
