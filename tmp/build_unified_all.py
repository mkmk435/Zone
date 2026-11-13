#!/usr/bin/env python3
"""Unified working-rate report including ALL old datasets and the new run.

Datasets:
  old_original        test_report.txt (all 102 payloads, no -xd/-ebi)
  old_xd_ebi          test_report_x64_low_xd_ebi.txt (13 x64 low)
  old_xd_ebi_5001     test_report_x64_low_xd_ebi_5001.txt (13 x64 low, pre-getpc)
  old_xd_ebi_getpc    test_report_x64_low_getpc.txt (13 x64 low, getpc)
  new_xd_ebi          new_test_report_5run.csv (49 regenerated payloads)
  baseline_original   tmp/original_baseline.csv (49 originals, 3 runs)

Outputs:
  working_rate_unified.csv          wide, one row per payload (all 102)
  working_rate_unified_tests.csv    long, every old/new test row
  working_rate_unified.xlsx         multi-sheet workbook
  WORKING_RATE_UNIFIED.md           readable report
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TECH_TOKENS = {"nop", "eq", "pii", "bcf", "ibp"}
TECHS = [
    "nop", "eq", "pii", "bcf", "ibp",
    "eq_nop_pii", "eq_nop_bcf", "eq_nop_ibp",
    "nop_eq", "nop_pii", "nop_bcf", "nop_ibp",
    "eq_pii", "eq_bcf", "eq_ibp",
]
EXTRA = ["xd", "xd_ebi"]
ALL_TECHS = TECHS + EXTRA


def parse_path(path):
    p = path.replace("\\", "/")
    arch = "x64" if "x64" in p else "x86"
    name = os.path.basename(p)
    stem = re.sub(r"\.bin$", "", name)
    run_m = re.search(r"_(\d+)$", stem)
    run = run_m.group(1) if run_m else ""
    stem = re.sub(r"_\d+$", "", stem)
    if stem.endswith("_xd_ebi"):
        return arch, stem[:-len("_xd_ebi")], "xd_ebi", run
    if stem.endswith("_xd"):
        return arch, stem[:-len("_xd")], "xd", run
    parts = stem.split("_")
    tech = []
    while parts and parts[-1] in TECH_TOKENS:
        tech.append(parts.pop())
    return arch, "_".join(parts), "_".join(reversed(tech)), run


def load_rows(path, dataset):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3 or "/" not in row[0]:
                continue
            arch, base, tech, run = parse_path(row[0].strip())
            if not tech:
                tech = "none"
            rows.append({
                "dataset": dataset, "arch": arch, "payload": base,
                "technique": tech, "run": run,
                "file": row[0].strip(),
                "kind": row[1].strip(),
                "status": row[2].strip().upper(),
                "detail": row[3].strip() if len(row) > 3 else "",
            })
    return rows


def aggregate(rows, dataset, tech_filter=None):
    stats = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r["dataset"] != dataset:
            continue
        if tech_filter is not None and r["technique"] not in tech_filter:
            continue
        key = (r["arch"], r["payload"], r["technique"])
        stats[key][1] += 1
        if r["status"] == "OK":
            stats[key][0] += 1
    return stats


def per_payload(stats, tech_filter=None):
    out = collections.defaultdict(lambda: [0, 0])
    for (arch, base, tech), (ok, total) in stats.items():
        if tech_filter is not None and tech not in tech_filter:
            continue
        out[(arch, base)][0] += ok
        out[(arch, base)][1] += total
    return out


def pct(ok, total):
    return (ok / total * 100.0) if total else None


def fmt_pct(v):
    return "—" if v is None else f"{v:.1f}%"


def fmt_rate(ok, total):
    return "—" if not total else f"{pct(ok, total):.1f}% ({ok}/{total})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-prefix", default="working_rate_unified")
    ap.add_argument("--md", default="WORKING_RATE_UNIFIED.md")
    ap.add_argument("--low", default="tmp/low_payloads.json")
    ap.add_argument("--manifest", default="mutations_new_xd_ebi/manifest.jsonl")
    ap.add_argument("--baseline", default="tmp/original_baseline.csv")
    args = ap.parse_args()

    low_data = json.load(open(args.low, encoding="utf-8"))
    low_rows = low_data["payloads"]
    low_keys = {(r["arch"], r["payload"]) for r in low_rows}
    threshold = low_data.get("threshold_pct", 50.0)

    datasets = [
        ("old_original", "test_report.txt"),
        ("old_xd_ebi", "test_report_x64_low_xd_ebi.txt"),
        ("old_xd_ebi_5001", "test_report_x64_low_xd_ebi_5001.txt"),
        ("old_xd_ebi_getpc", "test_report_x64_low_getpc.txt"),
        ("new_xd_ebi", "new_test_report_5run.csv"),
    ]
    all_rows = []
    for name, path in datasets:
        rows = load_rows(path, name)
        print(f"{name}: {len(rows)} rows from {path}")
        all_rows.extend(rows)

    baseline_rows = []
    if os.path.exists(args.baseline):
        with open(args.baseline, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.reader(f):
                if len(row) < 3 or "/" not in row[0]:
                    continue
                arch, fname = row[0].split("/", 1)
                base = re.sub(r"\.bin$", "", fname)
                baseline_rows.append({
                    "dataset": "baseline_original", "arch": arch,
                    "payload": base, "technique": "none", "run": "",
                    "file": row[0].strip(),
                    "kind": row[1].strip(), "status": row[2].strip().upper(),
                    "detail": row[3].strip() if len(row) > 3 else "",
                })
    all_rows.extend(baseline_rows)
    print(f"baseline_original: {len(baseline_rows)} rows")

    # aggregate per dataset/arch/payload/technique
    agg = {}
    for name, _ in datasets:
        agg[name] = aggregate(all_rows, name)
    agg["baseline_original"] = aggregate(all_rows, "baseline_original")

    old_pp = per_payload(agg["old_original"], TECHS)
    old_pp_all = per_payload(agg["old_original"])
    old5001_pp = per_payload(agg["old_xd_ebi_5001"], TECHS)
    oldgetpc_pp = per_payload(agg["old_xd_ebi_getpc"], TECHS)
    new_morph_pp = per_payload(agg["new_xd_ebi"], TECHS)
    new_xd_pp = per_payload(agg["new_xd_ebi"], EXTRA)
    new_all_pp = per_payload(agg["new_xd_ebi"], ALL_TECHS)
    base_pp = per_payload(agg["baseline_original"])

    all_payloads = sorted(set(old_pp_all) | low_keys, key=lambda k: (k[0], k[1]))

    # manifest generation counts
    gen = collections.defaultdict(lambda: {"ok": 0, "fail": 0})
    if os.path.exists(args.manifest):
        with open(args.manifest, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (rec.get("arch"), rec.get("payload"), rec.get("tech"))
                if rec.get("status") in ("ok", "exists"):
                    gen[key]["ok"] += 1
                else:
                    gen[key]["fail"] += 1

    records = []
    for arch, base in all_payloads:
        def vals(d):
            ok, tot = d.get((arch, base), [0, 0])
            return ok, tot, pct(ok, tot)

        o_ok, o_tot, o_r = vals(old_pp)
        oa_ok, oa_tot, oa_r = vals(old_pp_all)
        a_ok, a_tot, a_r = vals(old5001_pp)
        g_ok, g_tot, g_r = vals(oldgetpc_pp)
        nm_ok, nm_tot, nm_r = vals(new_morph_pp)
        nx_ok, nx_tot, nx_r = vals(new_xd_pp)
        na_ok, na_tot, na_r = vals(new_all_pp)
        b_ok, b_tot, b_r = vals(base_pp)
        gen_ok = sum(gen[(arch, base, t)]["ok"] for t in ALL_TECHS)
        gen_fail = sum(gen[(arch, base, t)]["fail"] for t in ALL_TECHS)

        notes = []
        if (arch, base) in low_keys:
            notes.append("basso working rate")
        if b_tot and b_ok < b_tot:
            notes.append(f"originale {b_ok}/{b_tot}")
        if "messagebox" in base:
            notes.append("old harness non rilevava il dialog")
        if g_tot and nx_tot and nx_r is not None and nx_r >= 90 and g_r < 50:
            notes.append(f"-xd recupera (getpc {g_r:.1f}% -> {nx_r:.1f}%)")
        if g_tot and nx_tot and nx_r is not None and g_r >= 50 and nx_r < g_r - 5:
            notes.append(f"regressione vs getpc {nx_r-g_r:+.1f} pp")
        if na_tot and o_tot and na_r is not None and o_r is not None:
            d = na_r - o_r
            if d <= -5:
                notes.append(f"regressione {d:+.1f} pp")
            elif d >= 20:
                notes.append(f"miglioramento {d:+.1f} pp")

        records.append({
            "arch": arch, "payload": base, "is_low": (arch, base) in low_keys,
            "old_original": (o_ok, o_tot, o_r),
            "old_original_all": (oa_ok, oa_tot, oa_r),
            "old_5001": (a_ok, a_tot, a_r),
            "old_getpc": (g_ok, g_tot, g_r),
            "new_morph": (nm_ok, nm_tot, nm_r),
            "new_xd": (nx_ok, nx_tot, nx_r),
            "new_all": (na_ok, na_tot, na_r),
            "baseline": (b_ok, b_tot, b_r),
            "gen_ok": gen_ok, "gen_fail": gen_fail,
            "tested": na_tot,
            "notes": "; ".join(notes),
        })

    # ---------------- wide CSV ----------------
    wide_path = f"{args.out_prefix}.csv"
    cols = [
        "arch", "payload", "is_low",
        "old_original_ok", "old_original_total", "old_original_rate_pct",
        "old_5001_ok", "old_5001_total", "old_5001_rate_pct",
        "old_getpc_ok", "old_getpc_total", "old_getpc_rate_pct",
        "new_morph_ok", "new_morph_total", "new_morph_rate_pct",
        "new_xd_ok", "new_xd_total", "new_xd_rate_pct",
        "new_all_ok", "new_all_total", "new_all_rate_pct",
        "baseline_ok", "baseline_total", "baseline_rate_pct",
        "delta_original_to_new_pct", "delta_getpc_to_new_pct",
        "delta_original_to_xd_pct", "delta_getpc_to_xd_pct",
        "generated_ok", "generation_fail", "tested", "notes",
    ]
    with open(wide_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            o = r["old_original"]; a = r["old_5001"]; g = r["old_getpc"]
            nm = r["new_morph"]; nx = r["new_xd"]; na = r["new_all"]; b = r["baseline"]
            def d(x, y):
                return "" if x[2] is None or y[2] is None else f"{y[2]-x[2]:+.1f}"
            w.writerow([
                r["arch"], r["payload"], "yes" if r["is_low"] else "no",
                o[0], o[1], "" if o[2] is None else f"{o[2]:.1f}",
                a[0], a[1], "" if a[2] is None else f"{a[2]:.1f}",
                g[0], g[1], "" if g[2] is None else f"{g[2]:.1f}",
                nm[0], nm[1], "" if nm[2] is None else f"{nm[2]:.1f}",
                nx[0], nx[1], "" if nx[2] is None else f"{nx[2]:.1f}",
                na[0], na[1], "" if na[2] is None else f"{na[2]:.1f}",
                b[0], b[1], "" if b[2] is None else f"{b[2]:.1f}",
                d(o, na), d(g, na), d(o, nx), d(g, nx),
                r["gen_ok"], r["gen_fail"], r["tested"], r["notes"],
            ])
    print("written", wide_path)

    # ---------------- long CSV ----------------
    long_path = f"{args.out_prefix}_tests.csv"
    with open(long_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dataset", "file", "arch", "payload", "technique", "run",
                    "kind", "status", "detail"])
        for r in all_rows:
            w.writerow([r["dataset"], r["file"], r["arch"], r["payload"],
                        r["technique"], r["run"], r["kind"], r["status"],
                        r["detail"]])
    print("written", long_path, len(all_rows), "rows")

    # ---------------- aggregates ----------------
    def sum_pp(d, keys):
        ok = tot = 0
        for k in keys:
            v = d.get(k)
            if v:
                ok += v[0]; tot += v[1]
        return ok, tot

    x64_low = [(r["arch"], r["payload"]) for r in records if r["is_low"] and r["arch"] == "x64"]
    x86_low = [(r["arch"], r["payload"]) for r in records if r["is_low"] and r["arch"] == "x86"]
    all_low = x64_low + x86_low

    summary_rows = []
    def add_summary(label, dataset_label, keys, pp, tech_filter=None):
        ok = tot = 0
        for k in keys:
            v = pp.get(k)
            if v:
                ok += v[0]; tot += v[1]
        summary_rows.append({"label": label, "dataset": dataset_label,
                             "payloads": len(keys), "ok": ok, "total": tot,
                             "rate": pct(ok, tot)})

    add_summary("Vecchio originale — tutti i payload", "old_original", all_payloads, old_pp_all)
    add_summary("Vecchio originale — 49 low", "old_original", all_low, old_pp)
    add_summary("Vecchio -xd -ebi (prima versione) — 13 x64 low", "old_xd_ebi", x64_low,
                per_payload(agg["old_xd_ebi"], TECHS))
    add_summary("Vecchio -xd -ebi (pre-getpc) — 13 x64 low", "old_xd_ebi_5001", x64_low, old5001_pp)
    add_summary("Vecchio -xd -ebi + getpc — 13 x64 low", "old_xd_ebi_getpc", x64_low, oldgetpc_pp)
    add_summary("Nuovo morph 15 tecniche — 13 x64 low", "new_xd_ebi", x64_low, new_morph_pp)
    add_summary("Nuovo morph 15 tecniche — 36 x86 low", "new_xd_ebi", x86_low, new_morph_pp)
    add_summary("Nuovo morph 15 tecniche — 49 low", "new_xd_ebi", all_low, new_morph_pp)
    add_summary("Nuovo solo -xd/-xd -ebi — 13 x64 low", "new_xd_ebi", x64_low, new_xd_pp)
    add_summary("Nuovo solo -xd/-xd -ebi — 36 x86 low", "new_xd_ebi", x86_low, new_xd_pp)
    add_summary("Nuovo solo -xd/-xd -ebi — 49 low", "new_xd_ebi", all_low, new_xd_pp)
    add_summary("Nuovo totale (17 config) — 13 x64 low", "new_xd_ebi", x64_low, new_all_pp)
    add_summary("Nuovo totale (17 config) — 36 x86 low", "new_xd_ebi", x86_low, new_all_pp)
    add_summary("Nuovo totale (17 config) — 49 low", "new_xd_ebi", all_low, new_all_pp)
    add_summary("Baseline originali — 49 low", "baseline_original", all_low, base_pp)

    # ---------------- per-technique ----------------
    def tech_aggregate(dataset, keys, tech):
        ok = tot = 0
        for arch, base in keys:
            v = agg[dataset].get((arch, base, tech))
            if v:
                ok += v[0]; tot += v[1]
        return ok, tot

    tech_x64 = []
    for t in TECHS:
        tech_x64.append({
            "tech": t,
            "old_original": tech_aggregate("old_original", x64_low, t),
            "old_5001": tech_aggregate("old_xd_ebi_5001", x64_low, t),
            "old_getpc": tech_aggregate("old_xd_ebi_getpc", x64_low, t),
            "new_morph": tech_aggregate("new_xd_ebi", x64_low, t),
        })
    for t in EXTRA:
        tech_x64.append({
            "tech": t,
            "old_original": (0, 0),
            "old_5001": (0, 0),
            "old_getpc": (0, 0),
            "new_morph": tech_aggregate("new_xd_ebi", x64_low, t),
        })

    tech_x86 = []
    for t in TECHS:
        tech_x86.append({
            "tech": t,
            "old_original": tech_aggregate("old_original", x86_low, t),
            "new_morph": tech_aggregate("new_xd_ebi", x86_low, t),
        })
    for t in EXTRA:
        tech_x86.append({
            "tech": t,
            "old_original": (0, 0),
            "new_morph": tech_aggregate("new_xd_ebi", x86_low, t),
        })

    # ---------------- Markdown ----------------
    lines = []
    lines.append("# Working rate unificato — tutti i dataset vecchi + nuovo\n")
    lines.append(f"Generato: {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
    lines.append(f"Soglia low: **< {threshold:.0f}%** sul vecchio originale. "
                 f"Payload selezionati: **{len(low_rows)}** "
                 f"(x64 {len(x64_low)}, x86 {len(x86_low)}).\n")

    lines.append("## Dataset inclusi\n")
    lines.append("| Dataset | File | Copertura |")
    lines.append("|---|---|---|")
    lines.append("| `old_original` | `test_report.txt` | tutti i 102 payload, 15 tecniche, nessuna flag |")
    lines.append("| `old_xd_ebi` | `test_report_x64_low_xd_ebi.txt` | 13 x64 low, `-xd -ebi` (prima versione) |")
    lines.append("| `old_xd_ebi_5001` | `test_report_x64_low_xd_ebi_5001.txt` | 13 x64 low, `-xd -ebi`, capstone 5.0.0.post1 |")
    lines.append("| `old_xd_ebi_getpc` | `test_report_x64_low_getpc.txt` | 13 x64 low, `-xd -ebi` + fix getpc |")
    lines.append("| `new_xd_ebi` | `new_test_report_5run.csv` | 49 low, 15 morph + `xd` + `xd_ebi` |")
    lines.append("| `baseline_original` | `tmp/original_baseline.csv` | 49 originali, 3 run ciascuno |")
    lines.append("")

    lines.append("## Riepilogo per dataset\n")
    lines.append("| Dataset / ambito | Payload | OK/test | Working rate |")
    lines.append("|---|---:|---:|---:|")
    for s in summary_rows:
        lines.append(f"| {s['label']} | {s['payloads']} | {s['ok']}/{s['total']} | "
                     f"{fmt_pct(s['rate'])} |")
    lines.append("")

    lines.append("## Payload a basso working rate: vecchi set → nuovo\n")
    lines.append("| # | Arch | Payload | Old orig. | Old getpc | Nuovo `-xd` | Nuovo morph | Δ vs getpc |")
    lines.append("|---:|:--:|---|---:|---:|---:|---:|---:|")
    low_sorted = sorted([r for r in records if r["is_low"]],
                        key=lambda r: (r["old_original"][2] is None,
                                       r["old_original"][2] or 0))
    for i, r in enumerate(low_sorted, 1):
        g = r["old_getpc"]; nx = r["new_xd"]; nm = r["new_morph"]
        dg = "—" if g[2] is None or nx[2] is None else f"{nx[2]-g[2]:+.1f} pp"
        lines.append(
            f"| {i} | {r['arch']} | `{r['payload']}` | "
            f"{fmt_rate(*r['old_original'][:2])} | {fmt_rate(*g[:2])} | "
            f"{fmt_rate(*nx[:2])} | {fmt_rate(*nm[:2])} | {dg} |")
    lines.append("")

    lines.append("## x64 low: per tecnica, tutti i set vecchi + nuovo\n")
    lines.append("| Tecnica | Old orig. | Old 5001 | Old getpc | Nuovo morph |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in tech_x64:
        lines.append(f"| `{row['tech']}` | {fmt_rate(*row['old_original'])} | "
                     f"{fmt_rate(*row['old_5001'])} | {fmt_rate(*row['old_getpc'])} | "
                     f"{fmt_rate(*row['new_morph'])} |")
    lines.append("")
    lines.append("Nota: `xd` e `xd_ebi` non esistevano nei vecchi set; la colonna "
                 "`Nuovo morph` per queste righe mostra le configurazioni di sola estrazione.\n")

    lines.append("## x86 low: per tecnica, vecchio + nuovo\n")
    lines.append("| Tecnica | Old orig. | Nuovo morph |")
    lines.append("|---|---:|---:|")
    for row in tech_x86:
        lines.append(f"| `{row['tech']}` | {fmt_rate(*row['old_original'])} | "
                     f"{fmt_rate(*row['new_morph'])} |")
    lines.append("")

    lines.append("## Note\n")
    lines.append("- **messagebox**: il vecchio report trattava il payload come \"other\" e aspettava "
                 "l'uscita del processo; il dialog bloccava il test. I nuovi dati usano il rilevamento "
                 "della finestra, quindi il confronto vecchio/nuovo per questi due payload non e omogeneo.")
    lines.append("- **x64 `*_winhttps`**: old getpc 6.7%; il nuovo `-xd`/`-xd -ebi` da solo e 10/10. "
                 "Il morphing e il limite, non l'estrazione.")
    lines.append("- **x86 winhttp** (`custom`, `meterpreter`): regressione. La call getpc salta il primo "
                 "blocco dati ma il consumer e dopo un secondo blocco; l'estrattore sposta il primo blocco "
                 "senza riscrivere la call. Old getpc = —, nuovo `-xd` = 0/10.")
    lines.append("- **x86 nonx**: `-xd` 10/10, morph 0/75: e il morphing a rompere, non l'estrazione.")
    lines.append("- **x86**: 5 run per configurazione (sui 10 generati) per contenere il runtime; "
                 "x64 10 run. I totali per payload/arch restano su centinaia di test.")
    lines.append("")

    lines.append("## Appendice: tutti i 102 payload vecchi\n")
    lines.append("| Arch | Payload | Old orig. | Old getpc | Nuovo `-xd` | Nuovo morph | Nuovo totale |")
    lines.append("|:--:|---|---:|---:|---:|---:|---:|")
    for r in sorted(records, key=lambda r: (r["arch"], r["payload"])):
        lines.append(f"| {r['arch']} | `{r['payload']}` | "
                     f"{fmt_rate(*r['old_original'][:2])} | {fmt_rate(*r['old_getpc'][:2])} | "
                     f"{fmt_rate(*r['new_xd'][:2])} | {fmt_rate(*r['new_morph'][:2])} | "
                     f"{fmt_rate(*r['new_all'][:2])} |")
    lines.append("")

    lines.append("## File\n")
    lines.append(f"- `{wide_path}` — tabella wide, tutti i 102 payload e tutti i dataset.")
    lines.append(f"- `{long_path}` — dati grezzi aggregabili: una riga per test (vecchi + nuovi).")
    lines.append("- `working_rate_unified.xlsx` — workbook con riepilogo, confronto, per tecnica, "
                 "matrice, dati completi.")
    lines.append("- `low_working_rate_payloads.csv` — lista dei 49 payload sotto soglia.")
    lines.append("- `mutations_new_xd_ebi/` — payload rigenerati (x64/x86).")
    lines.append("")
    open(args.md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("written", args.md)

    # ---------------- XLSX ----------------
    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="1F3864")
    head_font = Font(bold=True, color="FFFFFF")
    thin = Side(style="thin", color="B4C6E7")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def add_table(ws, headers, rows, widths=None, pct_cols=(), start_row=1):
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=c, value=h)
            cell.fill = head_fill
            cell.font = head_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        for r, row in enumerate(rows, start_row + 1):
            for c, val in enumerate(row, 1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.border = border
                if c in pct_cols and isinstance(val, (int, float)):
                    cell.number_format = "0.0"
        if widths:
            for i, w in enumerate(widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)

    ws = wb.active
    ws.title = "Riepilogo"
    ws["A1"] = "Zone — working rate unificato (tutti i dataset vecchi + nuovo)"
    ws["A1"].font = Font(bold=True, size=14, color="1F3864")
    ws["A2"] = (f"Generato {datetime.datetime.now():%Y-%m-%d %H:%M} · "
                f"soglia low < {threshold:.0f}% · {len(low_rows)} payload")
    ws["A2"].font = Font(italic=True, color="555555")
    add_table(ws, ["Dataset / ambito", "Payload", "OK", "Test", "Working rate %"],
              [[s["label"], s["payloads"], s["ok"], s["total"], s["rate"]]
               for s in summary_rows],
              widths=[52, 10, 10, 10, 14], pct_cols=(5,), start_row=4)
    ws.conditional_formatting.add(
        f"E5:E{4+len(summary_rows)}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws2 = wb.create_sheet("Confronto payload")
    headers2 = ["Arch", "Payload", "Low",
                "Old orig. OK", "Old orig. test", "Old orig. %",
                "Old 5001 OK", "Old 5001 test", "Old 5001 %",
                "Old getpc OK", "Old getpc test", "Old getpc %",
                "New morph OK", "New morph test", "New morph %",
                "New xd OK", "New xd test", "New xd %",
                "New total OK", "New total test", "New total %",
                "Baseline", "Δ orig→new", "Δ getpc→new", "Gen fail", "Note"]
    rows2 = []
    for r in records:
        o = r["old_original"]; a = r["old_5001"]; g = r["old_getpc"]
        nm = r["new_morph"]; nx = r["new_xd"]; na = r["new_all"]; b = r["baseline"]
        def d(x, y):
            return None if x[2] is None or y[2] is None else y[2] - x[2]
        rows2.append([
            r["arch"], r["payload"], "sì" if r["is_low"] else "",
            o[0], o[1], o[2], a[0], a[1], a[2], g[0], g[1], g[2],
            nm[0], nm[1], nm[2], nx[0], nx[1], nx[2], na[0], na[1], na[2],
            f"{b[0]}/{b[1]}", d(o, na), d(g, na), r["gen_fail"], r["notes"],
        ])
    add_table(ws2, headers2, rows2,
              widths=[7, 44, 5, 9, 9, 8, 9, 9, 8, 9, 9, 8, 9, 9, 8, 8, 8, 8, 9, 9, 8, 9, 10, 10, 8, 34],
              pct_cols=(6, 9, 12, 15, 18, 21, 23, 24), start_row=1)
    ws2.auto_filter.ref = f"A1:Z{len(rows2)+1}"
    for col in ("F", "I", "L", "O", "R", "U"):
        ws2.conditional_formatting.add(
            f"{col}2:{col}{len(rows2)+1}",
            ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                           mid_type="num", mid_value=50, mid_color="FFEB84",
                           end_type="num", end_value=100, end_color="63BE7B"))

    ws3 = wb.create_sheet("Per tecnica x64")
    headers3 = ["Tecnica", "Old orig. OK", "Old orig. test", "Old orig. %",
                "Old 5001 OK", "Old 5001 test", "Old 5001 %",
                "Old getpc OK", "Old getpc test", "Old getpc %",
                "New morph OK", "New morph test", "New morph %"]
    rows3 = []
    for row in tech_x64:
        vals = []
        for key in ("old_original", "old_5001", "old_getpc", "new_morph"):
            ok, tot = row[key]
            vals += [ok, tot, pct(ok, tot)]
        rows3.append([row["tech"]] + vals)
    add_table(ws3, headers3, rows3,
              widths=[14, 10, 10, 9, 10, 10, 9, 10, 10, 9, 10, 10, 9],
              pct_cols=(4, 7, 10, 13), start_row=1)
    ws3.auto_filter.ref = f"A1:M{len(rows3)+1}"

    ws4 = wb.create_sheet("Per tecnica x86")
    headers4 = ["Tecnica", "Old orig. OK", "Old orig. test", "Old orig. %",
                "New morph OK", "New morph test", "New morph %"]
    rows4 = []
    for row in tech_x86:
        o = row["old_original"]; n = row["new_morph"]
        rows4.append([row["tech"], o[0], o[1], pct(o[0], o[1]),
                      n[0], n[1], pct(n[0], n[1])])
    add_table(ws4, headers4, rows4, widths=[14, 10, 10, 9, 10, 10, 9],
              pct_cols=(4, 7), start_row=1)
    ws4.auto_filter.ref = f"A1:G{len(rows4)+1}"

    ws5 = wb.create_sheet("Matrice nuova")
    hdr = ["Arch", "Payload"] + ALL_TECHS
    mat = []
    for r in records:
        if not r["is_low"]:
            continue
        row = [r["arch"], r["payload"]]
        for t in ALL_TECHS:
            v = agg["new_xd_ebi"].get((r["arch"], r["payload"], t))
            row.append(pct(v[0], v[1]) if v else None)
        mat.append(row)
    add_table(ws5, hdr, mat, widths=[7, 44] + [8] * len(ALL_TECHS),
              pct_cols=tuple(range(3, 3 + len(ALL_TECHS))), start_row=1)
    ws5.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{len(mat)+1}"
    ws5.conditional_formatting.add(
        f"C2:{get_column_letter(len(hdr))}{len(mat)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws6 = wb.create_sheet("Dati completi")
    headers6 = ["Dataset", "File", "Arch", "Payload", "Tecnica", "Run", "Kind",
                "Status", "Detail"]
    rows6 = [[r["dataset"], r["file"], r["arch"], r["payload"], r["technique"],
              r["run"], r["kind"], r["status"], r["detail"]] for r in all_rows]
    add_table(ws6, headers6, rows6, widths=[16, 52, 7, 40, 14, 6, 10, 8, 50],
              start_row=1)
    ws6.auto_filter.ref = f"A1:I{len(rows6)+1}"

    ws7 = wb.create_sheet("Baseline")
    b_rows = []
    for r in records:
        if not r["is_low"]:
            continue
        b_rows.append([r["arch"], r["payload"], r["baseline"][0],
                       r["baseline"][1], r["baseline"][2]])
    add_table(ws7, ["Arch", "Payload", "OK", "Test", "Rate %"],
              b_rows, widths=[7, 44, 8, 8, 9], pct_cols=(5,), start_row=1)

    xlsx_path = f"{args.out_prefix}.xlsx"
    wb.save(xlsx_path)
    print("written", xlsx_path)

    # console
    print("\n=== SUMMARY ===")
    for s in summary_rows:
        print(f"{s['label']:<52} {s['ok']:5d}/{s['total']:<5d} {fmt_pct(s['rate'])}")


if __name__ == "__main__":
    main()
