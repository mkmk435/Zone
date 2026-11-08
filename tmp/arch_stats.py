import os, re, collections, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

payloads = {}
for arch in ("x86", "x64"):
    d = os.path.join(ROOT, "original_pl", arch)
    payloads[arch] = sorted((f[:-4] for f in os.listdir(d) if f.endswith(".bin")), key=len, reverse=True)

stats = collections.defaultdict(lambda: [0, 0])
per_payload = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
unknown = []

with open(os.path.join(ROOT, "test_report.txt"), "r", encoding="utf-8", errors="replace") as fh:
    lines = fh.read().splitlines()

for line in lines:
    parts = line.split(",")
    if len(parts) < 3:
        continue
    path, cat, res = parts[0], parts[1], parts[2]
    if "/" not in path:
        continue
    arch, fname = path.split("/", 1)
    if arch not in ("x86", "x64"):
        continue
    name = fname[:-4] if fname.endswith(".bin") else fname
    name = re.sub(r"_\d+$", "", name)
    tech = None
    for p in payloads[arch]:
        if name.startswith(p + "_"):
            tech = name[len(p) + 1:]
            break
    if tech is None:
        unknown.append(line)
        continue
    ok = 1 if res.strip() == "OK" else 0
    stats[(arch, tech)][0] += ok
    stats[(arch, tech)][1] += 1
    per_payload[arch][tech][0] += ok
    per_payload[arch][tech][1] += 1

print("unknown lines:", len(unknown))
for u in unknown[:5]:
    print("  ", u)

techs = sorted({t for (_, t) in stats})
print(f"{'tech':14s} {'x86 OK/tot':>14s} {'rate':>7s} {'x64 OK/tot':>14s} {'rate':>7s}")
for t in techs:
    a = stats[("x86", t)]
    b = stats[("x64", t)]
    ra = a[0] / a[1] * 100 if a[1] else 0
    rb = b[0] / b[1] * 100 if b[1] else 0
    print(f"{t:14s} {a[0]:5d}/{a[1]:<8d} {ra:6.1f}% {b[0]:5d}/{b[1]:<8d} {rb:6.1f}%")

for arch in ("x86", "x64"):
    tot_ok = sum(v[0] for (a, _), v in stats.items() if a == arch)
    tot = sum(v[1] for (a, _), v in stats.items() if a == arch)
    print(f"{arch} overall: {tot_ok}/{tot} = {tot_ok/tot*100:.1f}%")

# also per-category
cats = collections.defaultdict(lambda: [0, 0])
for line in lines:
    p = line.split(",")
    if len(p) < 3 or "/" not in p[0]:
        continue
    arch = p[0].split("/")[0]
    if arch not in ("x86", "x64"):
        continue
    cats[(arch, p[1])][0] += 1 if p[2].strip() == "OK" else 0
    cats[(arch, p[1])][1] += 1
print("\nby category:")
for (arch, cat), v in sorted(cats.items()):
    print(f"  {arch:4s} {cat:10s} {v[0]:5d}/{v[1]:<6d} {v[0]/v[1]*100:5.1f}%")
