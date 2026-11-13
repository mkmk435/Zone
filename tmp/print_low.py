import csv

rows = list(csv.DictReader(open("low_working_rate_payloads.csv", encoding="utf-8")))
for r in rows:
    print(f"{r['arch']}  {float(r['old_rate_pct']):5.1f}%  {r['payload']}")
