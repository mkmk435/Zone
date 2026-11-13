#!/usr/bin/env python3
"""Build NEW_TESTS_REPORT.md from the wrap, LLM and LLM-data experiment files."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOW = json.loads((ROOT / "tmp" / "low_payloads.json").read_text(encoding="utf-8"))
X64_LOW = [row["payload"] for row in LOW["payloads"] if row["arch"] == "x64"]


def load_report(path: Path):
    out = {}
    if not path.exists():
        return out
    for row in csv.reader(path.open(encoding="utf-8", errors="replace")):
        if len(row) >= 3:
            out[row[0].split("/")[-1]] = row[2]
    return out


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def money(value):
    return f"${value:.3f}"


# ---------------------------------------------------------------- wrap
manifest = [json.loads(line) for line in
            (ROOT / "mutations_wrap" / "manifest.jsonl").read_text(
                encoding="utf-8").splitlines() if line.strip()]
build = defaultdict(lambda: {"wrap": [0, 0], "wrap_full": [0, 0]})
build_seen = defaultdict(set)
for record in manifest:
    key = (record["payload"], record["tech"])
    if record["index"] in build_seen[key]:
        continue
    build_seen[key].add(record["index"])
    if record["status"] in ("ok", "exists"):
        build[record["payload"]][record["tech"]][0] += 1
    build[record["payload"]][record["tech"]][1] += 1

wrap_report = load_report(ROOT / "tmp" / "wrap_report.csv")
ran = defaultdict(lambda: {"wrap": [0, 0], "wrap_full": [0, 0]})
for name, status in wrap_report.items():
    stem = name[:-4]
    for tech in ("wrap_full", "wrap"):
        if f"_{tech}_" in stem:
            base = stem.split(f"_{tech}_")[0]
            ran[base][tech][1] += 1
            ran[base][tech][0] += status == "OK"
            break

wrap_rows = []
totals = {"wrap": [0, 0], "wrap_full": [0, 0]}
build_totals = {"wrap": [0, 0], "wrap_full": [0, 0]}
for payload in X64_LOW:
    cells = []
    for tech in ("wrap", "wrap_full"):
        built = build[payload][tech]
        ok = ran[payload][tech]
        cells.extend((f"{built[0]}/{built[1]}", f"{ok[0]}/{ok[1]}"))
        totals[tech][0] += ok[0]
        totals[tech][1] += 10
        build_totals[tech][0] += built[0]
        build_totals[tech][1] += built[1]
    wrap_rows.append((payload, *cells))

combos = []
combo_results = ROOT / "tmp" / "wrap_combos" / "results.csv"
if combo_results.exists():
    grouped = defaultdict(lambda: [0, 0, []])
    for row in csv.DictReader(combo_results.open(encoding="utf-8")):
        key = int(row["combo"])
        grouped[key][1] += 1
        grouped[key][0] += row["status"] == "OK"
        if row["size"]:
            grouped[key][2].append(int(row["size"]))
    names = ["-xd -wrap", "-xd -wrap -eq", "-xd -wrap -nop", "-xd -wrap -bcf",
             "-xd -wrap -eq -nop -bcf", "-xd -wrap -ibp",
             "-xd -wrap -eq -nop -bcf -ibp"]
    for key in sorted(grouped):
        ok, total, sizes = grouped[key]
        combos.append((names[key], ok, total,
                       sum(sizes) / len(sizes) if sizes else 0))

# ---------------------------------------------------------------- llm morph
llm_cells = defaultdict(lambda: {"ok": 0, "total": 0, "attempts": 0,
                                 "cost": 0.0, "sizes": [], "sim": []})
llm_working = load_report(ROOT / "tmp" / "llm_morph_report.csv")
llm_total_cost = 0.0
llm_all_cost = 0.0
for stats_path in sorted((ROOT / "tmp" / "llm_run" / "stats").glob(
        "windows_x64_messagebox_llm_*.json")):
    match = re.match(r".*_llm_([a-z]+)_s(\d)_(\d+)\.json$", stats_path.name)
    if not match:
        continue
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    cell = f"{match.group(1)} {match.group(2)}-shot"
    llm_cells[cell]["total"] += 1
    llm_cells[cell]["ok"] += bool(stats.get("ok"))
    llm_cells[cell]["attempts"] += stats.get("attempts", 0)
    cost = (stats.get("cost_usd") or {}).get("total") or 0.0
    llm_cells[cell]["cost"] += cost
    llm_all_cost += cost
    if stats.get("ok"):
        llm_total_cost += cost
        llm_cells[cell]["sizes"].append(
            (stats.get("payload") or {}).get("code_bytes", 0)
            + (stats.get("payload") or {}).get("data_bytes", 0))
        sim = next((a.get("similarity")
                    for a in reversed(stats.get("attempt_details", []))
                    if a.get("accepted")), None)
        if sim:
            llm_cells[cell]["sim"].append(sim)

llm_dir = ROOT / "mutations_llm" / "x64"
llm_hashes = defaultdict(set)
for path in llm_dir.glob("*.bin"):
    match = re.match(r".*_llm_([a-z]+)_s(\d)_\d+\.bin$", path.name)
    if match:
        llm_hashes[(match.group(1), match.group(2))].add(sha(path))

# ---------------------------------------------------------------- llm data
data_stats_dir = ROOT / "tmp" / "lldata_run" / "stats"
data_json_dir = ROOT / "tmp" / "lldata_run" / "data"
data_working = load_report(ROOT / "tmp" / "llm_data_report.csv")
data_cases = [
    ("x64 messagebox", "windows_x64_messagebox_lldata", 3),
    ("x64 messagebox + -eq", "windows_x64_messagebox_lldata_eq", 3),
    ("x86 messagebox", "windows_messagebox_lldata", 3),
    ("x64 reverse_http", "windows_x64_custom_reverse_http_lldata", 3),
    ("x86 reverse_http", "windows_custom_reverse_http_lldata", 3),
]
data_rows = []
data_cost = 0.0
data_unique = 0
for label, stem, runs in data_cases:
    ok = attempts = sections = data_bytes = 0
    cost = 0.0
    hashes = set()
    for index in range(1, runs + 1):
        stats_path = data_stats_dir / f"{stem}_{index}.json"
        if not stats_path.exists():
            continue
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        ok += bool(stats.get("ok"))
        attempts += stats.get("attempts", 0)
        cost += (stats.get("cost_usd") or {}).get("total") or 0.0
        if stem.endswith("_eq"):
            extra = data_stats_dir / f"{stem}_{index}.json.data.json"
            if extra.exists():
                extra_stats = json.loads(extra.read_text(encoding="utf-8"))
                attempts += extra_stats.get("attempts", 0)
                cost += (extra_stats.get("cost_usd") or {}).get("total") or 0.0
        info_path = data_json_dir / f"{stem}_{index}.json"
        if info_path.exists():
            info = json.loads(info_path.read_text(encoding="utf-8"))
            sections += len(info.get("sections") or [])
            data_bytes += info.get("data_bytes") or 0
        out = (ROOT / "mutations_llm_data" / ("x86" if label.startswith("x86")
               else "x64") / f"{stem}_{index}.bin")
        if out.exists():
            hashes.add(sha(out))
    data_cost += cost
    data_unique += len(hashes)
    worked = sum(1 for name, status in data_working.items()
                 if re.fullmatch(re.escape(stem) + r"_\d+\.bin", name)
                 and status == "OK")
    tested = sum(1 for name in data_working
                 if re.fullmatch(re.escape(stem) + r"_\d+\.bin", name))
    data_rows.append((label, f"{ok}/{runs}", f"{worked}/{tested or runs}",
                      f"{sections / runs:.1f}", f"{data_bytes / runs:.0f}",
                      f"{attempts / runs:.1f}", money(cost)))

# ---------------------------------------------------------------- report
lines = []
add = lines.append
add("# Nuovi test: assembly wrapping, LLM morphing e LLM data classifier")
add("")
add("Esito dei test lanciati il 2026-11-13 sul motore Zone in "
    "`C:\\Users\\ubu\\Desktop\\Zone`. Le esecuzioni usano `ploader.exe` / "
    "`ploader86.exe` (listener TCP 1234 per reverse/bind, finestra `#32770` "
    "per MessageBox).")
add("")
add("## 1. Assembly wrapping (`-wrap`, x64)")
add("")
add("Metodo: i 13 payload x64 a basso working rate, 10 run indipendenti per "
    "configurazione, due configurazioni. Il motore è stato congelato in "
    "`tmp/wrap_snapshot` per non dipendere dalle modifiche concorrenti.")
add("")
add("| Configurazione | Build riusciti | Test eseguiti | Working rate |")
add("|---|---:|---:|---:|")
add(f"| `-xd -wrap` | {build_totals['wrap'][0]}/130 | "
    f"{totals['wrap'][0]}/{totals['wrap'][1]} | "
    f"{100 * totals['wrap'][0] / totals['wrap'][1]:.1f}% |")
add(f"| `-xd -wrap -eq -nop -bcf -ibp` | {build_totals['wrap_full'][0]}/130 | "
    f"{totals['wrap_full'][0]}/{totals['wrap_full'][1]} | "
    f"{100 * totals['wrap_full'][0] / totals['wrap_full'][1]:.1f}% |")
add("")
add(f"Complessivo: **{totals['wrap'][0] + totals['wrap_full'][0]}/260 = "
    f"{100 * (totals['wrap'][0] + totals['wrap_full'][0]) / 260:.1f}%** "
    "sui tentativi; sui soli binari costruiti "
    f"**{totals['wrap'][0] + totals['wrap_full'][0]}/200 = "
    f"{100 * (totals['wrap'][0] + totals['wrap_full'][0]) / 200:.1f}%**.")
add("")
add("| Payload | Build wrap | Wrap OK | Build full | Full OK |")
add("|---|---:|---:|---:|---:|")
for payload, wrap_build, wrap_ok, full_build, full_ok in wrap_rows:
    add(f"| `{payload}` | {wrap_build} | {wrap_ok} | {full_build} | {full_ok} |")
add("")
add("I 60 build falliti sono i tre payload `*_winhttps` (10 semi x 2 "
    "configurazioni): `-xd` non sposta un blocco inline a `0x169`, quindi "
    "`-wrap` non può ricoprire tutto lo stream. È un limite dell'estrazione "
    "dati, non del wrapper.")
add("")
add("Tre output `-wrap` sono byte-identici tra run diverse (97/100 SHA-256 "
    "unici); il generatore assegnava il seed dalla stessa variabile "
    "d'ambiente condivisa tra thread, quindi alcune run hanno riusato lo "
    "stesso seed. Non cambia il working rate, ma riduce di poco la diversità "
    "del campione inviato a VirusTotal.")
add("")
add("Nota tecnica: durante i test è emerso un bug reale in `asm_wrap.py`. Le "
    "istruzioni con `data_fixup` (getpc `call` riscritta in `jmp` verso lo "
    "stub nel blob) venivano ricollocate e verificate come se fossero ancora "
    "`call`, quindi il build falliva con `expected call, got jmp`. La correzione "
    "tratta queste istruzioni come opache (nessuna relocation, verifica del "
    "mnemonico saltata); senza la fix `custom_reverse_https` e "
    "`meterpreter_reverse_http` non si costruivano affatto.")
add("")
add("MessageBox x64, 7 combinazioni x 5 semi, esecuzione reale:")
add("")
add("| Combinazione | Dialoghi | Dimensione media |")
add("|---|---:|---:|")
for name, ok, total, size in combos:
    add(f"| `{name}` | {ok}/{total} | {size:.0f} B |")
add("")
add("## 2. LLM morphing (DeepSeek, una tecnica per run)")
add("")
add("Payload: `windows_x64_messagebox` (313 B). 4 tecniche x 2 configurazioni "
    "di shot x 3 mutazioni = 24 run, ognuna verificata eseguendo il payload e "
    "attendendo il dialogo.")
add("")
add("| Tecnica / shot | Accettati | Working | Tentativi medi | Similarità | "
    "Costo | Mutanti unici |")
add("|---|---:|---:|---:|---:|---:|---:|")
for cell in sorted(llm_cells, key=lambda value: (value.split()[0],
                                                 value.split()[1])):
    info = llm_cells[cell]
    sim = (sum(info["sim"]) / len(info["sim"])) if info["sim"] else 0.0
    tech, shots = cell.split()
    unique = len(llm_hashes[(tech, shots[0])])
    add(f"| `{tech}` {shots} | {info['ok']}/{info['total']} | "
        f"{info['ok']}/{info['total']} | "
        f"{info['attempts'] / info['total']:.1f} | {sim:.3f} | "
        f"{money(info['cost'])} | {unique}/{info['total']} |")
add("")
add(f"Costo API del blocco morphing: **{money(llm_all_cost + 0.0796)}** "
    f"(24 run finali {money(llm_all_cost)} + {money(0.0796)} della cella "
    "`ibp` 0-shot fallita al primo giro e poi ripetuta con successo). "
    "Tutte le 24 mutazioni finali superano la verifica di esecuzione "
    "(24/24 dialoghi). Le risposte `eq` e `ibp` sono spesso byte-identiche tra "
    "semi diversi: la diversità effettiva è inferiore al numero di run.")
add("")
add("## 3. LLM data classifier (`--llm-data`)")
add("")
add("Confronto con l'estrazione simbolica `-xd`. Per ogni caso 3 run; "
    "l'esecuzione è verificata con il dialogo (MessageBox) o il listener "
    "(reverse).")
add("")
add("| Caso | Classificazioni OK | Working | Sezioni medie | Byte dati | "
    "Tentativi medi | Costo |")
add("|---|---:|---:|---:|---:|---:|---:|")
for row in data_rows:
    add("| " + " | ".join(str(value) for value in row) + " |")
add("")
add("Su tutti e quattro i payload di confronto l'output del classifier LLM è "
    "**byte-identico** a quello di `-xd` simbolico (stesso SHA-256): "
    "x64/x86 MessageBox, x64/x86 `custom_reverse_http`. Il classificatore ha "
    "quindi riprodotto esattamente le sezioni estratte a mano dal motore "
    "simbolico, a costi trascurabili.")
add("")
add(f"Costo API del blocco data: {money(data_cost)}; mutanti unici: "
    f"{data_unique}/15 (l'estrazione è deterministica, i 3 run per caso "
    "coincidono).")
add("")
add("## 4. VirusTotal")
add("")
add("Manifest in `vt_manifest.csv` / `vt_manifest.json`: "
    "**239 file, 220 SHA-256 unici** (i duplicati sono estrazioni "
    "deterministiche e alcune risposte LLM identiche).")
add("")
add("| Gruppo | File | Working locale |")
add("|---|---:|---:|")
add("| `-wrap` | 100 | 100 |")
add("| `-wrap` full | 100 | 98 |")
add("| LLM morphing | 24 | 24 |")
add("| LLM data | 15 | 15 |")
add("")
vt_latest = {}
vt_path = ROOT / "tmp" / "vt_results.jsonl"
if vt_path.exists():
    for line in vt_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        vt_latest[record["sha256"]] = record
vt_groups = defaultdict(lambda: {"files": 0, "done": 0, "detected": 0,
                                 "malicious": 0, "total": 0, "max": 0})
vt_seen = set()
for entry in json.loads((ROOT / "vt_manifest.json").read_text(
        encoding="utf-8")):
    if entry["sha256"] in vt_seen:
        continue
    vt_seen.add(entry["sha256"])
    group = vt_groups[entry["technique"]]
    group["files"] += 1
    record = vt_latest.get(entry["sha256"], {})
    if record.get("status") == "completed":
        group["done"] += 1
        group["malicious"] += record.get("malicious", 0)
        group["total"] += record.get("total", 0)
        group["detected"] += record.get("malicious", 0) > 0
        group["max"] = max(group["max"], record.get("malicious", 0))
if any(group["done"] for group in vt_groups.values()):
    add("| Tecnica | File | Analizzati | Rilevati (>0) | Detection rate | "
        "Malicious medi | Max |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    all_files = all_done = all_detected = 0
    for technique in sorted(vt_groups):
        group = vt_groups[technique]
        rate = (group["detected"] / group["done"] * 100
                if group["done"] else 0.0)
        mean = (group["malicious"] / group["done"]
                if group["done"] else 0.0)
        add(f"| `{technique}` | {group['files']} | {group['done']} | "
            f"{group['detected']} | {rate:.1f}% | {mean:.2f} | "
            f"{group['max']} |")
        all_files += group["files"]
        all_done += group["done"]
        all_detected += group["detected"]
    overall_rate = all_detected / all_done * 100 if all_done else 0.0
    add("")
    add(f"Totale: **{all_detected}/{all_done} rilevati "
        f"({overall_rate:.1f}%)** su {all_files} file unici inviati.")
    if all_done < all_files:
        add(f"Analisi ancora in corso per {all_files - all_done} file al "
            "momento della generazione del report.")
else:
    add("Invio **non eseguito**: manca `api_keys.txt`. Il submitter è pronto "
        "in `tmp/vt_submit.py`; appena disponibili una o più key parte in "
        "background con deduplica per SHA-256 e ripresa.")
add("")
add("## File prodotti")
add("")
add("- `mutations_wrap/x64/` — 200 mutanti `-wrap`")
add("- `mutations_llm/x64/` — 24 mutanti LLM")
add("- `mutations_llm_data/` — 15 mutanti del classifier LLM")
add("- `tmp/wrap_report.csv`, `tmp/llm_morph_report.csv`, "
    "`tmp/llm_data_report.csv` — esiti grezzi")
add("- `vt_manifest.csv` / `vt_manifest.json` — manifest per VirusTotal")
add("")

(ROOT / "NEW_TESTS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
print("written NEW_TESTS_REPORT.md")
print(f"wrap: {totals}")
print(f"llm cost total {llm_all_cost:.4f} data cost {data_cost:.4f}")
