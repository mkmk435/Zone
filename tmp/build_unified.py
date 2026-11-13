#!/usr/bin/env python3
"""Build the unified old-vs-new working-rate report.

Outputs:
  working_rate_unified.csv
  working_rate_unified.xlsx
  WORKING_RATE_UNIFIED.md

Run with the bundled Python (needs openpyxl).
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
    stem = re.sub(r"_\d+$", "", stem)
    if stem.endswith("_xd_ebi"):
        return arch, stem[:-len("_xd_ebi")], "xd_ebi"
    if stem.endswith("_xd"):
        return arch, stem[:-len("_xd")], "xd"
    parts = stem.split("_")
    tech = []
    while parts and parts[-1] in TECH_TOKENS:
        tech.append(parts.pop())
    return arch, "_".join(parts), "_".join(reversed(tech))


def load_report(path):
    stats = collections.defaultdict(lambda: [0, 0])
    rows = []
    if not os.path.exists(path):
        return stats, rows
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            arch, base, tech = parse_path(row[0].strip())
            if not tech:
                continue
            key = (arch, base, tech)
            stats[key][1] += 1
            if row[2].strip().upper() == "OK":
                stats[key][0] += 1
            rows.append((arch, base, tech, row[1].strip(), row[2].strip().upper()))
    return stats, rows


def load_simple(path):
    stats = collections.defaultdict(lambda: [0, 0])
    if not os.path.exists(path):
        return stats
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) < 3 or "/" not in row[0]:
                continue
            arch, fname = row[0].split("/", 1)
            base = re.sub(r"\.bin$", "", fname)
            stats[(arch, base)][1] += 1
            if row[2].strip().upper() == "OK":
                stats[(arch, base)][0] += 1
    return stats


def pct(ok, total):
    return (ok / total * 100.0) if total else None


def aggregate(stats, arch, base, techs):
    ok = total = 0
    for t in techs:
        v = stats.get((arch, base, t))
        if v:
            ok += v[0]
            total += v[1]
    return ok, total


def fmt_rate(ok, total):
    r = pct(ok, total)
    return "—" if r is None else f"{r:.1f}% ({ok}/{total})"


def fmt_pct(r):
    return "—" if r is None else f"{r:.1f}%"


def load_manifest(path):
    gen = collections.defaultdict(lambda: {"ok": 0, "fail": 0, "flags": collections.Counter()})
    if not os.path.exists(path):
        return gen
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (rec.get("arch"), rec.get("payload"), rec.get("tech"))
            if rec.get("status") in ("ok", "exists"):
                gen[key]["ok"] += 1
                if rec.get("flags"):
                    gen[key]["flags"][rec["flags"]] += 1
            else:
                gen[key]["fail"] += 1
    return gen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="test_report.txt")
    ap.add_argument("--new", default="new_test_report_5run.csv")
    ap.add_argument("--baseline", default="tmp/original_baseline.csv")
    ap.add_argument("--manifest", default="mutations_new_xd_ebi/manifest.jsonl")
    ap.add_argument("--low", default="tmp/low_payloads.json")
    ap.add_argument("--out-prefix", default="working_rate_unified")
    ap.add_argument("--md", default="WORKING_RATE_UNIFIED.md")
    args = ap.parse_args()

    low_data = json.load(open(args.low, encoding="utf-8"))
    low_rows = low_data["payloads"]
    low_keys = {(r["arch"], r["payload"]) for r in low_rows}
    threshold = low_data.get("threshold_pct", 50.0)

    old, old_rows = load_report(args.old)
    new, new_rows = load_report(args.new)
    baseline = load_simple(args.baseline)
    gen = load_manifest(args.manifest)

    old_pp = collections.defaultdict(lambda: [0, 0])
    for (arch, base, tech), (ok, total) in old.items():
        old_pp[(arch, base)][0] += ok
        old_pp[(arch, base)][1] += total

    payloads = sorted(set(old_pp) | low_keys,
                      key=lambda k: (k[0], k[1]))
    records = []
    for arch, base in payloads:
        old_ok, old_total = old_pp.get((arch, base), [0, 0])
        nm_ok, nm_total = aggregate(new, arch, base, TECHS)
        nx_ok, nx_total = aggregate(new, arch, base, EXTRA)
        na_ok, na_total = aggregate(new, arch, base, ALL_TECHS)
        b_ok, b_total = baseline.get((arch, base), [0, 0])
        g_ok = sum(gen[(arch, base, t)]["ok"] for t in ALL_TECHS)
        g_fail = sum(gen[(arch, base, t)]["fail"] for t in ALL_TECHS)

        notes = []
        if (arch, base) in low_keys:
            notes.append("basso working rate")
        if b_total and b_ok < b_total:
            notes.append(f"originale {b_ok}/{b_total}")
        if "messagebox" in base:
            notes.append("old harness non rilevava il dialog")
        if nx_total and nx_ok / nx_total >= 0.9 and nm_total and nm_ok / nm_total < 0.3:
            notes.append("-xd OK, morphing rompe")
        if na_total and old_total:
            d = (na_ok / na_total - old_ok / old_total) * 100
            if d <= -5:
                notes.append(f"regressione {d:+.1f} pp")
            elif d >= 20:
                notes.append(f"miglioramento {d:+.1f} pp")

        records.append({
            "arch": arch, "payload": base,
            "is_low": (arch, base) in low_keys,
            "old_ok": old_ok, "old_total": old_total,
            "old_rate": pct(old_ok, old_total),
            "baseline_ok": b_ok, "baseline_total": b_total,
            "baseline_rate": pct(b_ok, b_total),
            "new_morph_ok": nm_ok, "new_morph_total": nm_total,
            "new_morph_rate": pct(nm_ok, nm_total),
            "new_xd_ok": nx_ok, "new_xd_total": nx_total,
            "new_xd_rate": pct(nx_ok, nx_total),
            "new_all_ok": na_ok, "new_all_total": na_total,
            "new_all_rate": pct(na_ok, na_total),
            "delta_morph": (pct(nm_ok, nm_total) - pct(old_ok, old_total))
                           if nm_total and old_total else None,
            "delta_xd": (pct(nx_ok, nx_total) - pct(old_ok, old_total))
                        if nx_total and old_total else None,
            "generated_ok": g_ok, "generation_fail": g_fail,
            "tested": na_total,
            "notes": "; ".join(notes),
        })

    # ---------- CSV ----------
    csv_path = f"{args.out_prefix}.csv"
    cols = [
        "arch", "payload", "is_low",
        "old_ok", "old_total", "old_rate_pct",
        "baseline_ok", "baseline_total", "baseline_rate_pct",
        "new_morph_ok", "new_morph_total", "new_morph_rate_pct",
        "new_xd_ok", "new_xd_total", "new_xd_rate_pct",
        "new_all_ok", "new_all_total", "new_all_rate_pct",
        "delta_morph_pct", "delta_xd_pct",
        "generated_ok", "generation_fail", "tested", "notes",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow([
                r["arch"], r["payload"], "yes" if r["is_low"] else "no",
                r["old_ok"], r["old_total"],
                "" if r["old_rate"] is None else f'{r["old_rate"]:.1f}',
                r["baseline_ok"], r["baseline_total"],
                "" if r["baseline_rate"] is None else f'{r["baseline_rate"]:.1f}',
                r["new_morph_ok"], r["new_morph_total"],
                "" if r["new_morph_rate"] is None else f'{r["new_morph_rate"]:.1f}',
                r["new_xd_ok"], r["new_xd_total"],
                "" if r["new_xd_rate"] is None else f'{r["new_xd_rate"]:.1f}',
                r["new_all_ok"], r["new_all_total"],
                "" if r["new_all_rate"] is None else f'{r["new_all_rate"]:.1f}',
                "" if r["delta_morph"] is None else f'{r["delta_morph"]:+.1f}',
                "" if r["delta_xd"] is None else f'{r["delta_xd"]:+.1f}',
                r["generated_ok"], r["generation_fail"], r["tested"],
                r["notes"],
            ])
    print("written", csv_path)

    low_csv = "low_working_rate_payloads.csv"
    with open(low_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "arch", "payload", "old_ok", "old_total",
                    "old_rate_pct", "baseline", "threshold_pct"])
        for i, r in enumerate(sorted([x for x in records if x["is_low"]],
                                     key=lambda r: (r["old_rate"] is None,
                                                    r["old_rate"] or 0)), 1):
            w.writerow([i, r["arch"], r["payload"], r["old_ok"], r["old_total"],
                        f'{r["old_rate"]:.1f}',
                        f'{r["baseline_ok"]}/{r["baseline_total"]}',
                        f"{threshold:.0f}"])
    print("written", low_csv)

    # ---------- aggregates ----------
    def agg_records(subset, ok_key, total_key):
        ok = sum(r[ok_key] for r in subset)
        total = sum(r[total_key] for r in subset)
        return ok, total

    summary = []
    for arch in ("x64", "x86", "both"):
        sub = [r for r in records if arch == "both" or r["arch"] == arch]
        lowsub = [r for r in sub if r["is_low"]]
        o_all = agg_records(sub, "old_ok", "old_total")
        o_low = agg_records(lowsub, "old_ok", "old_total")
        nm = agg_records(lowsub, "new_morph_ok", "new_morph_total")
        nx = agg_records(lowsub, "new_xd_ok", "new_xd_total")
        na = agg_records(lowsub, "new_all_ok", "new_all_total")
        b = agg_records(lowsub, "baseline_ok", "baseline_total")
        summary.append({
            "arch": arch,
            "payloads_all": len(sub),
            "payloads_low": len(lowsub),
            "old_all": o_all, "old_low": o_low, "baseline_low": b,
            "new_morph": nm, "new_xd": nx, "new_all": na,
        })

    # per technique for low set
    tech_rows = []
    for arch in ("x64", "x86"):
        lowsub = [r for r in records if r["arch"] == arch and r["is_low"]]
        for tech in ALL_TECHS:
            old_ok = old_total = new_ok = new_total = 0
            for r in lowsub:
                v = old.get((arch, r["payload"], tech))
                if v:
                    old_ok += v[0]
                    old_total += v[1]
                v = new.get((arch, r["payload"], tech))
                if v:
                    new_ok += v[0]
                    new_total += v[1]
            tech_rows.append({
                "arch": arch, "tech": tech,
                "old_ok": old_ok, "old_total": old_total,
                "new_ok": new_ok, "new_total": new_total,
            })

    # ---------- Markdown ----------
    lines = []
    lines.append("# Working rate unificato: payload vecchi vs rigenerati\n")
    lines.append(f"Generato: {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
    lines.append(f"Soglia \"working rate basso\": **< {threshold:.0f}%** sul test originale "
                 f"(`{args.old}`). Payload selezionati: **{len(low_rows)}** "
                 f"(x64 {sum(1 for r in low_rows if r['arch']=='x64')}, "
                 f"x86 {sum(1 for r in low_rows if r['arch']=='x86')}).\n")
    lines.append("## Metodo\n")
    lines.append("- **Vecchi**: `test_report.txt`, 15 tecniche di morphing x 10 run per payload, nessuna flag `-xd`/`-ebi`.")
    lines.append("- **Nuovi**: stessi 15 setup di morphing rigenerati con `-xd -ebi` (fallback `-xd`), "
                 "10 run per config su x64 e 5 run (sui 10 generati) per config su x86, piu due "
                 "configurazioni di sola estrazione: `-xd` e `-xd -ebi` (10 run x64, 5 run x86).")
    lines.append("- **Test nuovi**: `ploader.exe` (x64) / `ploader86.exe` (x86); reverse con listener "
                 "127.0.0.1:1234, bind con connessione a 127.0.0.1:1234, messagebox con `EnumWindows` + `WM_CLOSE`.")
    lines.append("- **Baseline**: ogni payload originale e stato eseguito 3 volte con lo stesso harness; "
                 "tutti i 49 originali hanno funzionato 3/3, quindi le differenze misurano l'obfuscator, non l'harness.")
    lines.append("- `new_morph` = 15 tecniche storiche; `new_xd` = solo `-xd` / `-xd -ebi`; "
                 "`new_all` = tutte le 17 configurazioni.\n")

    lines.append("## Sintesi\n")
    x64_low = [r for r in records if r["is_low"] and r["arch"] == "x64"]
    x86_low = [r for r in records if r["is_low"] and r["arch"] == "x86"]
    x64_xd_ok = sum(1 for r in x64_low if r["new_xd_rate"] == 100.0)
    x86_xd_ok = sum(1 for r in x86_low
                    if r["new_xd_rate"] is not None and r["new_xd_rate"] >= 90.0)
    x86_xd_bad = [r["payload"] for r in x86_low
                  if r["new_xd_rate"] is not None and r["new_xd_rate"] == 0.0]
    lines.append(f"- **x64**: `-xd`/`-xd -ebi` da solo porta {x64_xd_ok}/{len(x64_low)} "
                 f"payload al 100%; le 15 tecniche di morphing restano al "
                 f"{fmt_pct(pct(*summary[0]['new_morph']))}.")
    bad_txt = ", ".join('`' + p + '`' for p in x86_xd_bad) or "nessuna"
    if len(x86_xd_bad) > 1:
        exc_txt = f"le eccezioni sono {bad_txt}"
    elif x86_xd_bad:
        exc_txt = f"l'eccezione e {bad_txt}"
    else:
        exc_txt = "nessuna eccezione"
    lines.append(f"- **x86**: `-xd`/`-xd -ebi` da solo e al 100% su {x86_xd_ok}/{len(x86_low)} "
                 f"payload; {exc_txt} (getpc con consumer lontano: l'estrattore sposta i dati "
                 f"senza riscrivere la call).")
    lines.append(f"- Il morphing resta il collo di bottiglia: x86 `new_morph` = "
                 f"{fmt_pct(pct(*summary[1]['new_morph']))}, x64 = "
                 f"{fmt_pct(pct(*summary[0]['new_morph']))}. Su diversi payload x86 "
                 f"(`*_nonx_tcp`, HTTP) la sola estrazione e 100% mentre `-nop`/`-bcf`/`-pii` rompono il payload.")
    lines.append("")

    lines.append("## 1. Payload a basso working rate (vecchio → nuovo)\n")
    lines.append("| # | Arch | Payload | Vecchio | Baseline orig. | Nuovo `-xd` | Nuovo morph | Δ morph |")
    lines.append("|---:|:--:|---|---:|---:|---:|---:|---:|")
    low_sorted = sorted([x for x in records if x["is_low"]],
                        key=lambda r: (r["old_rate"] is None, r["old_rate"] or 0))
    for i, r in enumerate(low_sorted, 1):
        delta_m = "—" if r["delta_morph"] is None else f"{r['delta_morph']:+.1f} pp"
        lines.append(
            f"| {i} | {r['arch']} | `{r['payload']}` | {fmt_rate(r['old_ok'], r['old_total'])} | "
            f"{fmt_rate(r['baseline_ok'], r['baseline_total'])} | "
            f"{fmt_rate(r['new_xd_ok'], r['new_xd_total'])} | "
            f"{fmt_rate(r['new_morph_ok'], r['new_morph_total'])} | "
            f"{delta_m} |"
        )
    lines.append("")

    lines.append("## 2. Riepilogo\n")
    lines.append("| Set | Payload | Vecchio | Nuovo morph | Nuovo `-xd` | Nuovo totale |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for s in summary:
        label = {"x64": "x64", "x86": "x86", "both": "**Totale**"}[s["arch"]]
        lines.append(
            f"| {label} | {s['payloads_low']} | {fmt_rate(*s['old_low'])} | "
            f"{fmt_rate(*s['new_morph'])} | {fmt_rate(*s['new_xd'])} | "
            f"{fmt_rate(*s['new_all'])} |")
    lines.append("")
    lines.append("Nota: il tasso \"Vecchio\" del set basso e calcolato sulle 15 tecniche storiche; "
                 "il tasso \"Nuovo totale\" include anche le due configurazioni di sola estrazione.\n")

    lines.append("## 3. Working rate per tecnica (solo payload a basso rate)\n")
    for arch in ("x64", "x86"):
        lines.append(f"### {arch}\n")
        lines.append("| Tecnica | Vecchio | Nuovo | Δ |")
        lines.append("|---|---:|---:|---:|")
        for tr in [t for t in tech_rows if t["arch"] == arch]:
            old_r = pct(tr["old_ok"], tr["old_total"])
            new_r = pct(tr["new_ok"], tr["new_total"])
            delta = "—" if old_r is None or new_r is None else f"{new_r-old_r:+.1f} pp"
            lines.append(
                f"| `{tr['tech']}` | {fmt_rate(tr['old_ok'], tr['old_total'])} | "
                f"{fmt_rate(tr['new_ok'], tr['new_total'])} | {delta} |")
        lines.append("")

    lines.append("## 4. Note e limiti\n")
    msg = [r for r in records if r["is_low"] and "messagebox" in r["payload"]]
    if msg:
        lines.append("- **messagebox**: il vecchio report trattava il payload come \"other\" e aspettava "
                     "l'uscita del processo; il dialog bloccava il test. I nuovi dati usano il rilevamento "
                     "della finestra, quindi il confronto vecchio/nuovo per questi due payload non e omogeneo.")
    lines.append("- **x64 `*_winhttps`**: la sola estrazione `-xd`/`-xd -ebi` funziona 10/10; "
                 "con le 15 tecniche di morphing solo `-eq` regge. Il limite non e la getpc, "
                 "ma il morphing che sposta/riscrive i riferimenti.")
    lines.append("- **x86 HTTP**: la sola estrazione `-xd`/`-xd -ebi` funziona 10/10; "
                 "`-nop` (e le combinazioni che lo includono) rompe il payload, quindi il tasso delle "
                 "15 tecniche storiche resta basso anche dopo la rigenerazione.")
    lines.append("- **x86 winhttp** (`custom`, `meterpreter`): regressione. Il getpc ha la call "
                 "che salta il primo blocco dati ma il consumer e dopo un secondo blocco; "
                 "l'estrattore sposta il primo blocco senza riscrivere la call, quindi `-xd` "
                 "rompe il payload (0/10). Era 21.3% / 11.3% col vecchio morphing.")
    lines.append("- **x86 nonx**: la sola estrazione e 10/10 su tutti i payload `*_nonx_tcp`; "
                 "tutte le 15 tecniche di morphing sono 0/75. Il morphing, non l'estrazione, "
                 "e la causa dei fallimenti.")
    lines.append("- **x86**: per contenere il tempo di esecuzione la matrice nuova usa 5 run per "
                 "configurazione invece di 10; i tassi hanno granularita del 20% per singola "
                 "configurazione, ma i totali per payload/arch restano su centinaia di test.")
    lines.append("- I fallimenti di **generazione** sono contati a parte (`generation_fail` nel CSV/XLSX); "
                 "il denominatore dei tassi nuovi e il numero di test effettivamente eseguiti.")
    lines.append("")
    lines.append("## 5. File\n")
    lines.append(f"- `{csv_path}` — dati completi per payload (tutti i 102 payload originali).")
    lines.append("- `working_rate_unified.xlsx` — riepilogo, per payload, per tecnica, matrice, dettaglio.")
    lines.append("- `new_test_report_5run.csv` — test grezzi dei nuovi payload (x64 10 run, x86 5 run).")
    lines.append("- `mutations_new_xd_ebi/` — payload rigenerati (x64/x86).")
    lines.append("- `tmp/original_baseline.csv` — baseline 3 run/payload degli originali.")
    lines.append("")
    open(args.md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("written", args.md)

    # ---------- XLSX ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "Riepilogo"
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

    ws.append([])
    ws["A1"] = "Zone — working rate unificato (vecchi vs rigenerati con -xd/-ebi)"
    ws["A1"].font = Font(bold=True, size=14, color="1F3864")
    ws["A2"] = f"Generato {datetime.datetime.now():%Y-%m-%d %H:%M} · soglia low < {threshold:.0f}% · {len(low_rows)} payload"
    ws["A2"].font = Font(italic=True, color="555555")

    summary_rows = []
    for s in summary:
        summary_rows.append([
            {"x64": "x64", "x86": "x86", "both": "Totale"}[s["arch"]],
            s["payloads_low"], s["old_low"][1],
            pct(*s["old_low"]), s["new_morph"][1], pct(*s["new_morph"]),
            s["new_xd"][1], pct(*s["new_xd"]), s["new_all"][1], pct(*s["new_all"]),
            s["baseline_low"][1], pct(*s["baseline_low"]),
        ])
    add_table(ws,
              ["Set", "Payload low", "Vecchio test", "Vecchio %",
               "Nuovo morph test", "Nuovo morph %", "Nuovo xd test", "Nuovo xd %",
               "Nuovo tot test", "Nuovo tot %", "Baseline test", "Baseline %"],
              summary_rows,
              widths=[12, 10, 11, 9, 12, 10, 11, 9, 11, 9, 11, 9],
              pct_cols=(4, 6, 8, 10, 12), start_row=4)

    ws2 = wb.create_sheet("Per payload")
    headers2 = ["Arch", "Payload", "Low", "Vecchio OK", "Vecchio tot", "Vecchio %",
                "Nuovo morph OK", "Nuovo morph tot", "Nuovo morph %",
                "Nuovo xd OK", "Nuovo xd tot", "Nuovo xd %",
                "Nuovo tot OK", "Nuovo tot tot", "Nuovo tot %",
                "Δ morph pp", "Δ xd pp", "Baseline", "Gen fail", "Note"]
    rows2 = []
    for r in records:
        rows2.append([
            r["arch"], r["payload"], "sì" if r["is_low"] else "",
            r["old_ok"], r["old_total"], r["old_rate"],
            r["new_morph_ok"], r["new_morph_total"], r["new_morph_rate"],
            r["new_xd_ok"], r["new_xd_total"], r["new_xd_rate"],
            r["new_all_ok"], r["new_all_total"], r["new_all_rate"],
            r["delta_morph"], r["delta_xd"],
            f'{r["baseline_ok"]}/{r["baseline_total"]}',
            r["generation_fail"], r["notes"],
        ])
    add_table(ws2, headers2, rows2,
              widths=[7, 44, 6, 10, 10, 9, 13, 13, 12, 10, 10, 9, 10, 10, 9, 11, 9, 10, 9, 34],
              pct_cols=(6, 9, 12, 15, 16, 17), start_row=1)
    ws2.auto_filter.ref = f"A1:T{len(rows2)+1}"
    ws2.conditional_formatting.add(
        f"F2:F{len(rows2)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))
    ws2.conditional_formatting.add(
        f"I2:I{len(rows2)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))
    ws2.conditional_formatting.add(
        f"L2:L{len(rows2)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws3 = wb.create_sheet("Per tecnica")
    rows3 = []
    for tr in tech_rows:
        old_r = pct(tr["old_ok"], tr["old_total"])
        new_r = pct(tr["new_ok"], tr["new_total"])
        rows3.append([
            tr["arch"], tr["tech"],
            tr["old_ok"], tr["old_total"], old_r,
            tr["new_ok"], tr["new_total"], new_r,
            None if old_r is None or new_r is None else new_r - old_r,
        ])
    add_table(ws3, ["Arch", "Tecnica", "Vecchio OK", "Vecchio tot", "Vecchio %",
                    "Nuovo OK", "Nuovo tot", "Nuovo %", "Δ pp"],
              rows3, widths=[7, 16, 11, 11, 9, 9, 9, 9, 9],
              pct_cols=(5, 8, 9), start_row=1)
    ws3.auto_filter.ref = f"A1:I{len(rows3)+1}"
    ws3.conditional_formatting.add(
        f"H2:H{len(rows3)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws4 = wb.create_sheet("Matrice nuova")
    hdr = ["Arch", "Payload"] + ALL_TECHS
    mat = []
    for r in records:
        if not r["is_low"]:
            continue
        row = [r["arch"], r["payload"]]
        for t in ALL_TECHS:
            v = new.get((r["arch"], r["payload"], t))
            row.append(pct(v[0], v[1]) if v else None)
        mat.append(row)
    add_table(ws4, hdr, mat, widths=[7, 44] + [8] * len(ALL_TECHS),
              pct_cols=tuple(range(3, 3 + len(ALL_TECHS))), start_row=1)
    ws4.auto_filter.ref = f"A1:{get_column_letter(len(hdr))}{len(mat)+1}"
    ws4.conditional_formatting.add(
        f"C2:{get_column_letter(len(hdr))}{len(mat)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws5 = wb.create_sheet("Dettaglio nuovi")
    det = []
    for r in records:
        if not r["is_low"]:
            continue
        for t in ALL_TECHS:
            v = new.get((r["arch"], r["payload"], t))
            g = gen[(r["arch"], r["payload"], t)]
            det.append([
                r["arch"], r["payload"], t,
                v[0] if v else 0, v[1] if v else 0,
                pct(v[0], v[1]) if v else None,
                g["ok"], g["fail"],
            ])
    add_table(ws5, ["Arch", "Payload", "Tecnica", "OK", "Test", "Rate %",
                    "Generati", "Gen fail"],
              det, widths=[7, 44, 16, 8, 8, 9, 10, 9],
              pct_cols=(6,), start_row=1)
    ws5.auto_filter.ref = f"A1:H{len(det)+1}"
    ws5.conditional_formatting.add(
        f"F2:F{len(det)+1}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    ws6 = wb.create_sheet("Baseline")
    b_rows = []
    for r in records:
        if not r["is_low"]:
            continue
        b_rows.append([r["arch"], r["payload"], r["baseline_ok"],
                       r["baseline_total"], r["baseline_rate"]])
    add_table(ws6, ["Arch", "Payload", "OK", "Test", "Rate %"],
              b_rows, widths=[7, 44, 8, 8, 9], pct_cols=(5,), start_row=1)

    xlsx_path = f"{args.out_prefix}.xlsx"
    wb.save(xlsx_path)
    print("written", xlsx_path)

    # console summary
    print("\n=== SUMMARY ===")
    for s in summary:
        print(s["arch"], "low", s["payloads_low"],
              "old", fmt_rate(*s["old_low"]),
              "new_morph", fmt_rate(*s["new_morph"]),
              "new_xd", fmt_rate(*s["new_xd"]),
              "new_all", fmt_rate(*s["new_all"]))


if __name__ == "__main__":
    main()
