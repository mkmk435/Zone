import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
payloads = {}
for arch in ("x86", "x64"):
    d = os.path.join(ROOT, "original_pl", arch)
    payloads[arch] = sorted((f[:-4] for f in os.listdir(d) if f.endswith(".bin")), key=len, reverse=True)

per = collections.defaultdict(lambda: [0, 0])
tech_only_nop = collections.defaultdict(lambda: [0, 0])
with open(os.path.join(ROOT, "test_report.txt"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        p = line.split(",")
        if len(p) < 3 or "/" not in p[0]:
            continue
        arch, fname = p[0].split("/", 1)
        if arch not in payloads:
            continue
        name = re.sub(r"_\d+$", "", fname[:-4])
        base = tech = None
        for cand in payloads[arch]:
            if name.startswith(cand + "_"):
                base, tech = cand, name[len(cand) + 1:]
                break
        if base is None:
            continue
        ok = 1 if p[2].strip() == "OK" else 0
        per[(arch, base)][0] += ok
        per[(arch, base)][1] += 1
        if tech in ("nop", "eq"):
            tech_only_nop[(arch, base, tech)][0] += ok
            tech_only_nop[(arch, base, tech)][1] += 1

print(f"{'arch':4s} {'payload':44s} {'OK':>5s} {'tot':>5s} {'rate':>6s}  nop   eq")
for (arch, base), v in sorted(per.items(), key=lambda kv: (kv[0][0], kv[1][0] / kv[1][1])):
    n = tech_only_nop[(arch, base, 'nop')]
    e = tech_only_nop[(arch, base, 'eq')]
    nr = f"{n[0]}/{n[1]}" if n[1] else "-"
    er = f"{e[0]}/{e[1]}" if e[1] else "-"
    print(f"{arch:4s} {base:44s} {v[0]:5d} {v[1]:5d} {v[0]/v[1]*100:5.1f}%  {nr:>6s} {er:>6s}")
