"""Build the x86 5-run staging set and filtered report.

Keeps every x64 result (already complete) and x86 results for variants 1..5.
Creates hardlinks in mutations_new_xd_ebi_5run/x86 so the tester only sees
the first five variants of every configuration.
"""
import csv
import os
import re
import shutil
from pathlib import Path

SRC = Path("mutations_new_xd_ebi/x86")
DST = Path("mutations_new_xd_ebi_5run/x86")
DST.mkdir(parents=True, exist_ok=True)

n = 0
for f in sorted(SRC.glob("*.bin")):
    m = re.match(r"^(.*)_(\d+)\.bin$", f.name)
    if not m or int(m.group(2)) > 5:
        continue
    target = DST / f.name
    if target.exists():
        continue
    try:
        os.link(f, target)
    except OSError:
        shutil.copy2(f, target)
    n += 1
print("staged", n, "x86 files")

# Filter report
report_in = Path("new_test_report.csv")
report_out = Path("new_test_report_5run.csv")
rows = []
with report_in.open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.reader(f):
        if not row or "/" not in row[0]:
            continue
        if row[0].startswith("x64/"):
            rows.append(row)
        elif row[0].startswith("x86/"):
            m = re.search(r"_(\d+)\.bin$", row[0])
            if m and int(m.group(1)) <= 5:
                rows.append(row)
with report_out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for row in rows:
        w.writerow(row)
print("report rows", len(rows), "->", report_out)
