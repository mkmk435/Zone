import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
payloads = {}
for arch in ("x86", "x64"):
    d = os.path.join(ROOT, "original_pl", arch)
    payloads[arch] = sorted((f[:-4] for f in os.listdir(d) if f.endswith(".bin")), key=len, reverse=True)

per = collections.defaultdict(lambda: [0, 0])
with open(os.path.join(ROOT, "test_report.txt"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        p = line.split(",")
        if len(p) < 3 or "/" not in p[0]:
            continue
        arch, fname = p[0].split("/", 1)
        if arch not in payloads:
            continue
        name = re.sub(r"_\d+$", "", fname[:-4])
        for cand in payloads[arch]:
            if name.startswith(cand + "_"):
                per[(arch, cand)][0] += 1 if p[2].strip() == "OK" else 0
                per[(arch, cand)][1] += 1
                break


def short(arch, name):
    n = name[len("windows_"):]
    if arch == "x64":
        n = n[len("x64_"):]
    return n


x86map = {short("x86", b): v for (a, b), v in per.items() if a == "x86"}
x64map = {short("x64", b): v for (a, b), v in per.items() if a == "x64"}

common = sorted(set(x86map) & set(x64map))
print(f"{'family':34s} {'x86':>10s} {'rate':>6s} {'x64':>10s} {'rate':>6s} {'diff':>7s}")
tot86 = [0, 0]
tot64 = [0, 0]
for c in common:
    a = x86map[c]
    b = x64map[c]
    tot86[0] += a[0]; tot86[1] += a[1]
    tot64[0] += b[0]; tot64[1] += b[1]
    ra, rb = a[0] / a[1] * 100, b[0] / b[1] * 100
    print(f"{c:34s} {a[0]:4d}/{a[1]:<5d} {ra:5.1f}% {b[0]:4d}/{b[1]:<5d} {rb:5.1f}% {ra-rb:+6.1f}")
print(f"{'MATCHED TOTAL':34s} {tot86[0]:4d}/{tot86[1]:<5d} {tot86[0]/tot86[1]*100:5.1f}% "
      f"{tot64[0]:4d}/{tot64[1]:<5d} {tot64[0]/tot64[1]*100:5.1f}% "
      f"{(tot86[0]/tot86[1]-tot64[0]/tot64[1])*100:+6.1f}")

print("\nx86-only families:")
for c in sorted(set(x86map) - set(x64map)):
    a = x86map[c]
    print(f"  {c:34s} {a[0]:4d}/{a[1]:<5d} {a[0]/a[1]*100:5.1f}%")
print("x64-only families:")
for c in sorted(set(x64map) - set(x86map)):
    b = x64map[c]
    print(f"  {c:34s} {b[0]:4d}/{b[1]:<5d} {b[0]/b[1]*100:5.1f}%")
