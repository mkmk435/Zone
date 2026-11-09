"""Print and persist the low-old-working-rate payload set."""
import argparse
import json
import sys

sys.path.insert(0, "tmp")
import work_rate_data as W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="test_report.txt")
    ap.add_argument("--threshold", type=float, default=50.0)
    ap.add_argument("--out", default="tmp/low_payloads.json")
    args = ap.parse_args()

    stats, _ = W.load_report(args.report)
    pp = W.per_payload(stats)
    orig = W.load_original_names()
    # only payloads that actually exist in original_pl
    pp = {k: v for k, v in pp.items() if k in orig}

    rows = []
    for (arch, base), (ok, total) in pp.items():
        rows.append({
            "arch": arch,
            "payload": base,
            "old_ok": ok,
            "old_total": total,
            "old_rate": round(W.rate(ok, total), 2),
        })
    rows.sort(key=lambda r: (r["old_rate"], r["arch"], r["payload"]))
    low = [r for r in rows if r["old_rate"] < args.threshold]

    print(f"Old report: {args.report}")
    print(f"Threshold: working rate < {args.threshold:.0f}%")
    print(f"Payloads below threshold: {len(low)} / {len(rows)}\n")
    print(f"{'#':>3}  {'arch':4}  {'old rate':>8}  {'ok/total':>10}  payload")
    print("-" * 92)
    for i, r in enumerate(low, 1):
        print(f"{i:3d}  {r['arch']:4}  {r['old_rate']:7.1f}%  "
              f"{r['old_ok']:4d}/{r['old_total']:<5d}  {r['payload']}")

    by_arch = {}
    for r in low:
        by_arch[r["arch"]] = by_arch.get(r["arch"], 0) + 1
    print("\nBy architecture:", by_arch)
    print(f"Planned mutants: {len(low)} payloads x 15 techniques x 10 = "
          f"{len(low) * 150}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({
            "source_report": args.report,
            "threshold_pct": args.threshold,
            "payloads": low,
        }, f, indent=2)
    print(f"\nWritten {args.out}")


if __name__ == "__main__":
    main()
