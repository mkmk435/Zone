import csv, collections, json

TECHS = ["nop","eq","pii","bcf","ibp","eq_nop_pii","eq_nop_bcf","eq_nop_ibp",
         "nop_eq","nop_pii","nop_bcf","nop_ibp","eq_pii","eq_bcf","eq_ibp"]
ORDER = ["nop","eq","pii","bcf","ibp","eq_nop_pii","eq_nop_bcf","eq_nop_ibp",
         "nop_eq","eq_bcf","eq_ibp","eq_pii","nop_bcf","nop_ibp","nop_pii"]

low = json.load(open("tmp/low_payloads.json", encoding="utf-8"))["payloads"]
low_keys = {(r["arch"], r["payload"]) for r in low}

def load(path, dataset):
    stats = collections.defaultdict(lambda: [0,0])
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["dataset"] != dataset:
            continue
        key = (r["arch"], r["payload"], r["technique"])
        stats[key][1] += 1
        if r["status"] == "OK":
            stats[key][0] += 1
    return stats

new = load("working_rate_unified_tests.csv", "new_xd_ebi")
old = load("working_rate_unified_tests.csv", "old_original")

def rate(arch, tech, stats):
    ok=tot=0
    for (a,b,t),v in stats.items():
        if a==arch and t==tech and (a,b) in low_keys:
            ok+=v[0]; tot+=v[1]
    return (ok/tot*100 if tot else 0.0), ok, tot

for arch in ("x64","x86"):
    print("==",arch)
    for t in ORDER:
        nr,no,nt = rate(arch,t,new)
        orr,oo,ot = rate(arch,t,old)
        print(f"{t:<12} new {nr:5.1f}% ({no}/{nt})   old {orr:5.1f}% ({oo}/{ot})")
    new_avg = sum(rate(arch,t,new)[0] for t in ORDER)/len(ORDER)
    old_avg = sum(rate(arch,t,old)[0] for t in ORDER)/len(ORDER)
    print(f"avg new {new_avg:.2f}  old {old_avg:.2f}\n")
