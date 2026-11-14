#!/usr/bin/env python3
"""Generate bench/ALL_TESTS_REPORT.md from the consolidated CSVs."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def read_csv(name: str) -> list:
    path = RESULTS / name
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def number(value):
    if value in ("", None):
        return None
    try:
        return int(value)
    except ValueError:
        return float(value)


def aggregate(rows: list) -> dict:
    attempts = sum(number(row["attempts"]) or 0 for row in rows)
    build = sum(number(row["build_ok"]) or 0 for row in rows
                if row["build_ok"] != "")
    exec_ok = sum(number(row["exec_ok"]) or 0 for row in rows
                  if row["exec_ok"] != "")
    correct = sum(number(row["correct"]) or 0 for row in rows
                  if row["correct"] != "")
    hashes = {row["unique_output_sha256"] for row in rows
              if row["unique_output_sha256"]}
    has_build = any(row["build_ok"] != "" for row in rows)
    class_rows = [row for row in rows if row["class_exact"] != ""]
    return {
        "attempts": attempts, "build": build, "exec_ok": exec_ok,
        "correct": correct, "unique": len(hashes), "has_build": has_build,
        "class_runs": len(class_rows),
        "class_exact": sum(number(row["class_exact"]) or 0
                           for row in class_rows),
        "cost": sum(float(row["cost_usd"] or 0) for row in rows),
    }


def rate(numerator, denominator):
    if not denominator:
        return "—"
    return f"{100 * numerator / denominator:.1f}%"


def main() -> int:
    runs = read_csv("all_test_runs.csv")
    matrix = read_csv("coverage_matrix.csv")
    gaps = read_csv("remaining_gaps.csv")
    summarize = json.loads((RESULTS / "consolidated_summary.json").read_text(
        encoding="utf-8"))
    classifier_raw = [json.loads(line) for line in
                      (RESULTS / "classifier_compare.jsonl").read_text(
                          encoding="utf-8").splitlines()] if (
        RESULTS / "classifier_compare.jsonl").exists() else []

    def campaign(name: str) -> list:
        return [row for row in runs if row["campaign"] == name]

    def grouped(name: str, key_fields: tuple) -> dict:
        groups = defaultdict(list)
        for row in campaign(name):
            groups[tuple(row[field] for field in key_fields)].append(row)
        return groups

    lines = []
    add = lines.append
    add("# Tutti i test — consolidamento, copertura e limiti")
    add("")
    add("Questo documento accorpa i risultati disponibili, ma **non è una "
        "campagna completa sull'intero corpus originale**: il nuovo benchmark "
        "funzionale copre 13 fixture innocue (7 x64, 6 x86) più 6 fixture "
        "classifier; i 102 payload Metasploit restano coperti solo dalle "
        "campagne storiche, e i loro risultati non vengono mescolati con "
        "quelli del corpus benigno.")
    add("")
    add("## 1. Fonti e denominatari")
    add("")
    add("| Campagna | Fonte | Tipo | Granularità | Dati grezzi |")
    add("|---|---|---|---|---|")
    sources = [
        ("bench_block1_native", "bench/results/native_attempts.jsonl",
         "funzionale", "run", "sì (log + hash per run)"),
        ("bench_block2_wrap86", "bench/results/native_wrap86.jsonl",
         "funzionale", "run", "sì"),
        ("bench_block1_llm", "bench/results/llm_attempts.jsonl",
         "funzionale LLM", "chiamata", "sì (stats + log)"),
        ("bench_block2_llm", "bench/results/llm_attempts_x86.jsonl",
         "funzionale LLM", "chiamata", "sì"),
        ("bench_block2_classifier", "bench/results/llm_data_attempts.jsonl",
         "classifier", "chiamata", "sì"),
        ("bench_block2_classifier_fixtures",
         "bench/results/classifier_compare.jsonl", "classifier",
         "chiamata", "sì (ground truth + predizione)"),
        ("prev_2026_wrap", "mutations_wrap/manifest.jsonl + "
         "tmp/wrap_report.csv", "campagna precedente", "tentativo", "sì"),
        ("prev_2026_llm", "tmp/llm_run/stats + tmp/llm_morph_report.csv",
         "campagna precedente LLM", "tentativo API", "sì"),
        ("prev_2026_classifier", "tmp/lldata_run/stats + "
         "tmp/llm_data_report.csv", "campagna precedente classifier",
         "cella", "sì"),
        ("legacy_2025_working", "test_report.txt", "storico 2025",
         "cella riassuntiva", "parziale: righe grezze, artefatti non "
         "rieseguiti"),
        ("legacy_2025_vt", "results.json", "storico VT", "dataset",
         "parziale: 8.049/15.021 artefatti verificati"),
        ("prev_2026_vt", "vt_manifest.json + tmp/vt_results.jsonl",
         "VT 2026", "dataset", "sì (hash ricalcolati)"),
    ]
    for name, source, kind, granularity, verified in sources:
        add(f"| `{name}` | `{source}` | {kind} | {granularity} | {verified} |")
    add("")
    add("### 1.1 Denominatori")
    add("")
    add("- **Build / tentativi**: binari prodotti sul totale dei tentativi di "
        "build (o chiamate LLM).")
    add("- **Corrette / build**: esecuzioni con buffer uguale al ground truth "
        "sui binari prodotti.")
    add("- **Corrette / tentativi**: esecuzioni corrette sul totale dei "
        "tentativi, incluse build fallite e rifiuti.")
    add("- **Unici / prodotti**: SHA-256 distinti sui binari prodotti; output "
        "identici non sono campioni indipendenti.")
    add("- **Classificazione esatta**: sezioni predette uguali agli "
        "intervalli ground truth (offset e lunghezza).")
    add("- **Byte mancati / byte di codice come dati**: byte di ground truth "
        "non coperti / byte predetti fuori dagli intervalli attesi.")
    add("- **VT completate / scansioni**: scansioni con risultato valido sul "
        "totale dei record; i non verificabili sono contati a parte.")
    add("## 2. Nuovo benchmark benigno")
    add("")
    add("### 2.1 Baseline")
    add("")
    baseline = aggregate(campaign("baseline_original_fixtures"))
    add(f"- Payload originali: {baseline['correct']}/{baseline['attempts']} "
        "risultati attesi verificati prima delle trasformazioni.")
    add("- Baseline `-xd`: 4 estrazioni, 4 corrette "
        "(`bench_block1_baseline` + `bench_block2_baseline`).")
    add("")
    add("### 2.2 Trasformazioni native")
    add("")
    add("| Arch | Tecnica | Versione | Tentativi | Build | Corrette/build | "
        "Corrette/tentativi | Unici/prodotti |")
    add("|---|:--:|---|---:|---:|---:|---:|---:|")
    native_rows = campaign("bench_block1_native") + \
        campaign("bench_block2_wrap86")
    native_groups = defaultdict(list)
    for row in native_rows:
        native_groups[(row["arch"], row["technique"],
                       row["engine_version"])].append(row)
    for key in sorted(native_groups):
        item = aggregate(native_groups[key])
        add(f"| {key[0]} | `{key[1]}` | `{key[2]}` | {item['attempts']} | "
            f"{item['build']} | {rate(item['correct'], item['build'])} | "
            f"{rate(item['correct'], item['attempts'])} | "
            f"{item['unique']}/{item['build']} |")
    add("")
    add("Fonte: `bench/results/native_attempts.jsonl` (block1) e "
        "`bench/results/native_wrap86.jsonl` (block2). Denominatori: "
        "tentativi = run native; build = binari prodotti; corrette = buffer "
        "uguale al ground truth dichiarato; unici = SHA-256 distinti.")
    add("")
    add("### 2.3 LLM morphing")
    add("")
    add("| Arch | Tecnica | Shot | Versione | Chiamate | Build | "
        "Corrette/build | Corrette/chiamate | Unici/prodotti | Costo |")
    add("|---|:--:|:--:|---|---:|---:|---:|---:|---:|---:|")
    llm_groups = defaultdict(list)
    for row in campaign("bench_block1_llm") + campaign("bench_block2_llm"):
        llm_groups[(row["arch"], row["technique"], row["shot"],
                    row["engine_version"])].append(row)
    for key in sorted(llm_groups, key=lambda value: tuple(str(part)
                                                          for part in value)):
        item = aggregate(llm_groups[key])
        add(f"| {key[0]} | `{key[1]}` | {key[2]} | `{key[3]}` | "
            f"{item['attempts']} | {item['build']} | "
            f"{rate(item['correct'], item['build'])} | "
            f"{rate(item['correct'], item['attempts'])} | "
            f"{item['unique']}/{item['build']} | ${item['cost']:.4f} |")
    add("")
    llm_all = campaign("bench_block1_llm") + campaign("bench_block2_llm")
    for arch, version in (("x64", "2026-11-13_block1"),
                          ("x86", "2026-11-13_block2")):
        rows = [row for row in llm_all if row["arch"] == arch
                and row["engine_version"] == version]
        item = aggregate(rows)
        add(f"- {arch} (`{version}`): {item['attempts']} chiamate, "
            f"{item['build']} build, {item['correct']} corrette, "
            f"{item['unique']} output unici, costo ${item['cost']:.4f}. "
            f"Le percentuali restano per cella/tecnica nelle tabelle sopra: "
            "x64 e x86 usano versioni diverse e non vengono sommati in "
            "un'unica percentuale.")
    add("")
    add("Fonte: `bench/results/llm_attempts.jsonl` (x64, block1) e "
        "`bench/results/llm_attempts_x86.jsonl` (x86, block2). Una chiamata = "
        "una generazione; massimo 3 per cella, retry inclusi.")
    add("")
    add("### 2.4 Classifier sul corpus benigno (3 casi dati)")
    add("")
    add("| Caso | Chiamate | Classificazione esatta | Build | Esecuzione | "
        "Costo |")
    add("|---|---:|---:|---:|---:|---:|")
    classifier_groups = defaultdict(list)
    for row in campaign("bench_block2_classifier"):
        classifier_groups[(row["arch"], row["case"])].append(row)
    for key in sorted(classifier_groups):
        item = aggregate(classifier_groups[key])
        add(f"| {key[0]}/`{key[1]}` | {item['attempts']} | "
            f"{item['class_exact']}/{item['class_runs']} | {item['build']} | "
            f"{item['correct']} | ${item['cost']:.4f} |")
    add("")
    add("### 2.5 Classifier con ground truth indipendente (6 fixture)")
    add("")
    add("| Caso | Arch | Metodo | Run | Esatte | Byte mancati | Byte di "
        "codice classificati come dati | Build | Esecuzione | Tempo medio | "
        "Costo |")
    add("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    compare_groups = defaultdict(list)
    for row in campaign("bench_block2_classifier_fixtures"):
        compare_groups[(row["case"], row["arch"],
                        row["technique"])].append(row)
    timing = defaultdict(list)
    costs = defaultdict(float)
    for row in classifier_raw:
        key = (row["case"], row["arch"], row["method"])
        timing[key].append(row.get("elapsed") or 0.0)
        costs[key] += row.get("cost_usd") or 0.0
    for key in sorted(compare_groups):
        rows = compare_groups[key]
        item = aggregate(rows)
        missed = sum(number(row["class_missed_bytes"]) or 0 for row in rows)
        false_positive = sum(number(row["class_false_positive_bytes"]) or 0
                             for row in rows)
        times = timing.get((key[0], key[1], key[2]), [])
        mean_time = sum(times) / len(times) if times else 0.0
        add(f"| `{key[0]}` | {key[1]} | {key[2]} | {item['attempts']} | "
            f"{item['class_exact']}/{item['class_runs']} | {missed} | "
            f"{false_positive} | {item['build']} | {item['correct']} | "
            f"{mean_time:.1f}s | ${costs.get((key[0], key[1], key[2]), 0):.4f} |")
    add("")
    agreements = 0
    comparisons = 0
    for key in sorted({(row["arch"], row["case"])
                       for row in classifier_raw}):
        symbolic = [row for row in classifier_raw
                    if (row["arch"], row["case"]) == key
                    and row["method"] == "symbolic"]
        llm_rows = [row for row in classifier_raw
                    if (row["arch"], row["case"]) == key
                    and row["method"] == "llm"]
        if not symbolic:
            continue
        reference = symbolic[0]["evaluation"]["predicted"]
        for row in llm_rows:
            comparisons += 1
            agreements += row["evaluation"]["predicted"] == reference
    add(f"Concordanza LLM ↔ estrattore simbolico: **{agreements}/"
        f"{comparisons}** chiamate. È una concordanza tra metodi, distinta "
        "dalla correttezza rispetto al ground truth (colonne qui sopra).")
    add("")
    add("Fonti: `bench/results/llm_data_attempts.jsonl` e "
        "`bench/results/classifier_compare.jsonl`. Il ground truth è in "
        "`bench/fixtures/classifier_cases.json` ed è stato definito prima "
        "delle chiamate; il modello non lo ha ricevuto.")
    add("")
    add("## 3. Campagne precedenti (2026, prima di questo consolidamento)")
    add("")
    prev_wrap = aggregate(campaign("prev_2026_wrap"))
    add(f"- `prev_2026_wrap`: {prev_wrap['attempts']} tentativi, "
        f"{prev_wrap['build']} build, {prev_wrap['correct']} corrette, "
        f"{prev_wrap['unique']} output unici. Include 60 build fallite sui "
        "payload `*_winhttps`.")
    prev_llm = aggregate(campaign("prev_2026_llm"))
    add(f"- `prev_2026_llm`: {prev_llm['attempts']} tentativi registrati nei "
        f"file stats (più 3 della run fallita iniziale, conservata solo come "
        f"aggregato), {prev_llm['build']} accettati, {prev_llm['correct']} "
        f"corretti, costo ${prev_llm['cost']:.4f}.")
    prev_data = aggregate(campaign("prev_2026_classifier"))
    add(f"- `prev_2026_classifier`: {prev_data['attempts']} tentativi, "
        f"{prev_data['correct']} corretti, costo ${prev_data['cost']:.4f}.")
    add("")
    add("Fonte: `mutations_wrap/manifest.jsonl`, `tmp/wrap_report.csv`, "
        "`tmp/llm_run/stats/`, `tmp/lldata_run/stats/`. Sono campagne "
        "precedenti: non vengono ricalcolate né sostituite dai nuovi run.")
    add("")
    add("## 4. Campagne storiche 2025")
    add("")
    legacy = aggregate(campaign("legacy_2025_working"))
    add(f"- Working rate storico: {legacy['attempts']} righe, "
        f"{legacy['correct']} OK, {len(campaign('legacy_2025_working'))} celle "
        "(payload × tecnica). La build non è registrata e gli artefatti non "
        "sono stati rieseguiti: è un riepilogo, non una riverifica.")
    add("- VirusTotal 2025: 15.021 record, 8.049 verificabili, 6.972 non "
        "verificabili (artefatto assente); 102 originali e 102 SGN.")
    add("")
    add("Fonte: `test_report.txt`, `results.json`, `results_original.json`, "
        "`results_sgn.json`. Il working rate 2025 è un riepilogo da righe "
        "grezze ma **non è verificato sui dati grezzi** (artefatti non "
        "rieseguiti, build non registrata).")
    add("")
    add("## 5. VirusTotal storico (solo lettura)")
    add("")
    add("| Dataset | Scansioni | Completate | Zero rilevamenti | Rilevati | "
        "Non verificabili |")
    add("|---|---:|---:|---:|---:|---:|")
    for name in ("legacy_2025_vt", "legacy_2025_vt_originals",
                 "legacy_2025_vt_sgn", "prev_2026_vt",
                 "prev_2026_vt_originals"):
        rows = campaign(name)
        if not rows:
            continue
        item = rows[0]
        add(f"| `{name}` | {item['vt_scans']} | {item['vt_completed']} | "
            f"{item['vt_zero_detections']} | {item['vt_detected']} | "
            f"{item['vt_unverifiable']} |")
    add("")
    add("Motori 2026: 3.259 `type-unsupported`, 283 timeout, 73 failure su "
        "16.500 risposte. Zero rilevamenti non è una prova di invisibilità; "
        "analisi incomplete e risultati mancanti restano visibili sopra.")
    add("")
    add("## 6. Fallimenti osservati")
    add("")
    add("- **IBP x86**: 18 tentativi, 17 build, 0 esecuzioni corrette; un "
        "build termina con `IndexError` in `shuffle_blocks`. Resta un "
        "fallimento noto del blocco 1; la causa non è attribuita oltre "
        "l'eccezione osservata.")
    llm_fail = [row for row in
                campaign("bench_block1_llm") + campaign("bench_block2_llm")
                if row["correct"] == "0"]
    validated = [row for row in llm_fail
                 if "IBP did not permute" in (row["notes"] or "")]
    network = [row for row in llm_fail
               if "IncompleteRead" in (row["notes"] or "")]
    other = len(llm_fail) - len(validated) - len(network)
    total_llm = len(campaign("bench_block1_llm")) + \
        len(campaign("bench_block2_llm"))
    add(f"- **LLM nuovo benchmark**: {len(llm_fail)} chiamate non corrette "
        f"su {total_llm}: {len(validated)} rifiuti del validatore "
        f"(IBP non permutato, x86 branch e x64 branch), "
        f"{len(network)} errori di rete (`IncompleteRead`, risposta troncata, "
        f"costo 0), {other} altri. Nessuno è stato sostituito.")
    add("- **Wrap precedente**: 60 build fallite (tre payload `*_winhttps`) e "
        "2 esecuzioni fallite sui 200 binari costruiti.")
    add("")
    add("## 7. Copertura e gap")
    add("")
    cell_gaps = [gap for gap in gaps
                 if gap["reason"].startswith("cella")]
    add(f"Celle di matrice mancanti: **{sum(int(gap['missing']) for gap in cell_gaps)}**.")
    if cell_gaps:
        grouped_gaps = Counter((gap["corpus"], gap["arch"], gap["technique"])
                               for gap in cell_gaps)
        for key, count in grouped_gaps.most_common(12):
            add(f"- {key[0]} {key[1]} `{key[2]}`: {count} celle incomplete")
    else:
        add("- Nessuna cella della matrice attesa risulta incompleta.")
    add("")
    add("Gap dichiarati:")
    for gap in gaps:
        if gap["reason"].startswith("cella"):
            continue
        add(f"- {gap['corpus']} / {gap['case']} / `{gap['technique']}`: "
            f"{gap['reason']} (missing={gap['missing']}).")
    add("")
    add("## 8. Costi")
    add("")
    add("| Campagna | Tentativi/chiamate | Costo | Fonte |")
    add("|---|---:|---:|---|")
    for name in ("bench_block1_llm", "bench_block2_llm",
                 "bench_block2_classifier",
                 "bench_block2_classifier_fixtures", "prev_2026_llm",
                 "prev_2026_classifier"):
        rows = campaign(name)
        if not rows:
            continue
        item = aggregate(rows)
        add(f"| `{name}` | {item['attempts']} | ${item['cost']:.4f} | "
            "campo `cost_usd` dei risultati |")
    add("")
    add("Nota: `bench_block2_classifier_fixtures` conta 24 run (18 chiamate "
        "LLM + 6 esecuzioni simboliche gratuite); solo le 18 LLM hanno costo. "
        "`prev_2026_llm` non include $0,0796 di una run fallita "
        "registrata solo come aggregato nel log; il costo delle nuove "
        "chiamate è quello dei file di risultato per chiamata. I costi non "
        "sono sommati in un unico totale.")
    add("")
    add("## 9. File")
    add("")
    add("- `bench/results/all_test_runs.csv` — una riga per run/chiamata o "
        "cella riassuntiva, con fonte.")
    add("- `bench/results/coverage_matrix.csv` — matrice aggregata.")
    add("- `bench/results/remaining_gaps.csv` — celle e dati mancanti.")
    add("- `bench/results/classifier_compare.jsonl` — predizioni e ground "
        "truth del classifier.")
    add("- `bench/engines/2026-11-13_block1|block2/VERSION.json` — versioni.")
    add("- `bench/VT_AUDIT.md`, `bench/INVENTORY.md`, `bench/BUDGET.md`.")
    add("")
    add("## 10. Conclusione")
    add("")
    add("Completati: corpus benigno 13/13, matrice nativa, LLM x64 e x86 con "
        "3 chiamate per cella, classifier su corpus e su 6 fixture con ground "
        "truth, audit VT. Fallimenti osservati: IBP x86 (0/18 corrette), "
        "5 rifiuti del validatore LLM e 2 errori di rete LLM, 60 build wrap "
        "storiche. Non coperti: `-pii`/`-ip`, payload originali 2025 non "
        "rieseguiti, 6.972 record VT 2025 senza artefatto, nessuna scansione "
        "VT del corpus benigno.")
    add("")

    (HERE / "ALL_TESTS_REPORT.md").write_text("\n".join(lines),
                                              encoding="utf-8")
    print("written bench/ALL_TESTS_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
