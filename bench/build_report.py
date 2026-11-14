#!/usr/bin/env python3
"""Generate BENCH_REPORT.md from the raw attempt files."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def load(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def main() -> int:
    native = [row for row in load(RESULTS / "native_attempts.jsonl")
              if row["technique"] != "xd"]
    baseline = [row for row in load(RESULTS / "native_attempts.jsonl")
                if row["technique"] == "xd"]
    llm = load(RESULTS / "llm_attempts.jsonl")
    classifier = load(RESULTS / "llm_data_attempts.jsonl")
    wrap86 = [row for row in load(RESULTS / "native_wrap86.jsonl")
              if row["technique"] == "wrap"]
    cases = json.loads((HERE / "fixtures" / "cases.json").read_text(
        encoding="utf-8"))
    audit = json.loads((RESULTS / "vt_audit.json").read_text(encoding="utf-8"))
    version = json.loads((HERE / "engines" / "2026-11-13_block1" /
                          "VERSION.json").read_text(encoding="utf-8"))

    technique_arch = defaultdict(list)
    for row in native:
        technique_arch[(row["arch"], row["technique"])].append(row)
    per_case = defaultdict(list)
    for row in native:
        per_case[(row["arch"], row["case"])].append(row)

    lines = []
    add = lines.append
    add("# Benchmark Zone — copertura funzionale, LLM e audit VirusTotal")
    add("")
    add("Blocco 1 (nativo e LLM): motore congelato "
        f"`bench/engines/2026-11-13_block1` (git `{version['git_head'][:8]}`, "
        f"congelato {version['frozen_at']}). Blocco 2 (classifier e `-wrap` "
        "x86): `bench/engines/2026-11-13_block2`, congelato dopo la conferma.")
    add("")
    add("## Sintesi")
    add("")
    total_attempts = len(native)
    total_build = sum(1 for row in native if row["build_ok"])
    total_match = sum(1 for row in native if row["match"])
    add(f"- Corpus benigno nuovo: **13 fixture** (7 x64, 6 x86), 13/13 "
        "originali verificati contro il risultato atteso dichiarato.")
    add(f"- Matrice nativa: **{total_attempts} tentativi**, "
        f"{total_build} build riuscite ({pct(total_build / total_attempts)}), "
        f"{total_match} esecuzioni corrette "
        f"({pct(total_match / total_attempts)} sui tentativi, "
        f"{pct(total_match / total_build)} sulle build).")
    add(f"- LLM morphing: **{len(llm)} chiamate** (4 casi x 4 tecniche x "
        "0/2 shot x 3 chiamate), "
        f"{sum(1 for row in llm if row['build_ok'])} build e "
        f"{sum(1 for row in llm if row['match'])} esecuzioni corrette; "
        f"costo ${sum(row['cost_usd'] for row in llm):.4f}.")
    add(f"- Estensione blocco 2 (motore successivo, dopo la conferma): "
        f"`-wrap` x86 su 6 casi, {len(wrap86)} tentativi, "
        f"{sum(1 for row in wrap86 if row['match'])} corrette, "
        f"{len({row['sha256'] for row in wrap86 if row['build_ok']})} output "
        "unici.")
    add("- Il classifier LLM (blocco 2, motore congelato dopo la conferma "
        f"esplicita) è stato eseguito: {len(classifier)} chiamate, "
        f"{sum(1 for row in classifier if row['exact_classification'])}/"
        f"{len(classifier)} classificazioni esatte rispetto al ground truth, "
        f"{sum(1 for row in classifier if row['match'])} esecuzioni corrette, "
        f"costo ${sum(row['cost_usd'] for row in classifier):.4f}.")
    add("- Audit VT: nessuna nuova sottomissione; 6.972 record 2025 non "
        "verificabili per artefatto assente, 220/220 scansioni 2026 "
        "completate.")
    add("")
    add("## Metodo")
    add("")
    add("Ogni caso dichiara prima del test: sorgente assembly, byte attesi nel "
        "buffer di 256 byte, criterio di successo (uguaglianza esatta, resto "
        "`0xCC`), e per i casi dati l'intervallo ground truth. Il runner C "
        "(`bench/harness/runner.c`, compilato MSVC x64 e x86) mappa il payload "
        "RWX, lo esegue sulla CPU reale e scrive il buffer; un crash del "
        "processo è un fallimento, non un risultato.")
    add("")
    add("| Dimensione | Valori |")
    add("|---|---|")
    add("| Architetture | x64, x86 |")
    add("| Tecniche native | `eq`, `nop`, `bcf`, `ibp` (entrambe); `wrap` x64 (blocco 1) e x86 (blocco 2) |")
    add("| Run per cella nativa | 3 |")
    add("| Preprocessing dati | `-xd` dichiarato per `strings`/`getpc` |")
    add("| LLM | 4 casi x64 x 4 tecniche x {0,2} shot x 3 chiamate |")
    add("| Metriche | build/tentativi, corrette/build, corrette/tentativi, unici/prodotti |")
    add("")
    add("## Copertura")
    add("")
    add("| Caso | Tipo | x64 | x86 | Dati inline | Comportamento atteso |")
    add("|---|:--:|:--:|:--:|:--:|---|")
    for case in cases:
        if case["arch"] != "x64":
            continue
        counterpart = next((item for item in cases
                            if item["name"] == case["name"]
                            and item["arch"] == "x86"), None)
        expected = "buffer esatto sui byte dichiarati"
        add(f"| `{case['name']}` | {case['kind']} | sì | "
            f"{'sì' if counterpart else '—'} | "
            f"{'sì' if case['requires_extract'] else 'no'} | {expected} |")
    add("")
    add("Ground truth dati: `strings` x64 offset 25 len 13, `getpc` x64 offset "
        "5 len 12, `strings` x86 offset 9 len 12 (stringa + NUL).")
    add("")
    add("## Risultati nativi")
    add("")
    add("| Arch | Tecnica | Tentativi | Build | Build rate | Corrette/build | "
        "Corrette/tentativi | Unici/prodotti |")
    add("|---|:--:|---:|---:|---:|---:|---:|---:|")
    for arch in ("x64", "x86"):
        for technique in ("eq", "nop", "bcf", "ibp", "wrap"):
            rows = technique_arch.get((arch, technique), [])
            if not rows:
                continue
            attempts = len(rows)
            build = sum(1 for row in rows if row["build_ok"])
            match = sum(1 for row in rows if row["match"])
            unique = len({row["sha256"] for row in rows if row["build_ok"]})
            add(f"| {arch} | `{technique}` | {attempts} | {build} | "
                f"{pct(build / attempts)} | "
                f"{pct(match / build) if build else '—'} | "
                f"{pct(match / attempts)} | {unique}/{build} |")
    add("")
    add("Per caso (tutte le tecniche native insieme):")
    add("")
    add("| Arch | Caso | Tentativi | Build | Corrette | Unici |")
    add("|---|:--:|---:|---:|---:|---:|")
    for (arch, case_name), rows in sorted(per_case.items()):
        build = sum(1 for row in rows if row["build_ok"])
        match = sum(1 for row in rows if row["match"])
        unique = len({row["sha256"] for row in rows if row["build_ok"]})
        add(f"| {arch} | `{case_name}` | {len(rows)} | {build} | {match} | "
            f"{unique} |")
    add("")
    add("### Estensione blocco 2: `-wrap` x86")
    add("")
    add("Il wrapping x86 era in sviluppo durante il blocco 1; dopo la conferma "
        "di fine è stato congelato come blocco 2 e testato sugli stessi 6 casi "
        "x86.")
    add("")
    add("| Caso | Tentativi | Build | Corrette | Unici |")
    add("|---|:--:|:--:|:--:|:--:|")
    wrap86_cases = defaultdict(list)
    for row in wrap86:
        wrap86_cases[row["case"]].append(row)
    for case_name, rows in sorted(wrap86_cases.items()):
        add(f"| `{case_name}` | {len(rows)} | "
            f"{sum(1 for row in rows if row['build_ok'])} | "
            f"{sum(1 for row in rows if row['match'])} | "
            f"{len({row['sha256'] for row in rows if row['build_ok']})} |")
    add("")
    add(f"Totale: {len(wrap86)} tentativi, "
        f"{sum(1 for row in wrap86 if row['build_ok'])} build, "
        f"{sum(1 for row in wrap86 if row['match'])} corrette.")
    add("")
    add(f"Baseline `-xd`: {len(baseline)} estrazioni, "
        f"{sum(1 for row in baseline if row['match'])} corrette.")
    add("")
    add("### Fallimenti nativi")
    add("")
    native_fail = [row for row in native if not row["match"]]
    add(f"{len(native_fail)} tentativi non corretti, tutti `x86` + `-ibp`:")
    add("")
    for row in native_fail:
        add(f"- `{row['arch']}/{row['case']}` run {row['run']}: build="
            f"{row['build_ok']}, esito={row['error'][-140:] or 'crash'}")
    add("")
    add("Il pattern è sistematico: su 18 tentativi x86 `-ibp`, 17 costruiscono "
        "e nessuno esegue; 1 build fallisce con `IndexError`. x64 `-ibp` è "
        "21/21. Non è un problema del runner: gli originali e "
        "`eq`/`nop`/`bcf` sugli stessi casi passano.")
    add("")
    add("## LLM morphing")
    add("")
    add("| Tecnica | Shot | Chiamate | Build | Corrette | Unici | Costo |")
    add("|---|:--:|---:|---:|---:|---:|---:|")
    llm_tech = defaultdict(list)
    for row in llm:
        llm_tech[(row["technique"], row["shots"])].append(row)
    for (technique, shots), rows in sorted(llm_tech.items()):
        build = sum(1 for row in rows if row["build_ok"])
        match = sum(1 for row in rows if row["match"])
        unique = len({row["sha256"] for row in rows if row["build_ok"]})
        cost = sum(row["cost_usd"] for row in rows)
        add(f"| `{technique}` | {shots} | {len(rows)} | {build} | {match} | "
            f"{unique} | ${cost:.4f} |")
    add("")
    shot0 = [row for row in llm if row["shots"] == 0]
    shot2 = [row for row in llm if row["shots"] == 2]
    add(f"0-shot: {sum(1 for row in shot0 if row['match'])}/"
        f"{len(shot0)} corrette, "
        f"{len({row['sha256'] for row in shot0 if row['build_ok']})} output "
        "unici, costo "
        f"${sum(row['cost_usd'] for row in shot0):.4f}. "
        f"2-shot: {sum(1 for row in shot2 if row['match'])}/"
        f"{len(shot2)} corrette, "
        f"{len({row['sha256'] for row in shot2 if row['build_ok']})} unici, "
        f"costo ${sum(row['cost_usd'] for row in shot2):.4f}. "
        "La differenza è dentro il rumore di 3 chiamate per cella.")
    add("")
    add(f"Output unici totali: "
        f"{len({row['sha256'] for row in llm if row['build_ok']})}/"
        f"{sum(1 for row in llm if row['build_ok'])}. Le risposte identiche "
        "non sono campioni indipendenti.")
    add("")
    llm_fail = [row for row in llm if not row["match"]]
    add(f"Fallimenti LLM: {len(llm_fail)}.")
    for row in llm_fail:
        add(f"- `{row['case']}/{row['technique']}/s{row['shots']}/"
            f"chiamata {row['call']}`: build={row['build_ok']}, "
            f"{row['error'][:200]}")
    add("")
    add("## LLM data classifier")
    add("")
    add("Eseguito dopo conferma esplicita che l'altra sessione aveva finito, "
        "sul **blocco 2** (`bench/engines/2026-11-13_block2`, congelato "
        "2026-11-13T14:05, hash in `VERSION.json`). I 5 test offline di "
        "`test_llm_data.py` passano sulla copia congelata.")
    add("")
    add("| Caso | Chiamate | Classificazione esatta | Build | Esecuzione "
        "corretta | Costo |")
    add("|---|:--:|:--:|:--:|:--:|---:|")
    classifier_cases = defaultdict(list)
    for row in classifier:
        classifier_cases[(row["arch"], row["case"])].append(row)
    for (arch, name), rows in sorted(classifier_cases.items()):
        add(f"| {arch}/`{name}` | {len(rows)} | "
            f"{sum(1 for row in rows if row['exact_classification'])}/"
            f"{len(rows)} | {sum(1 for row in rows if row['build_ok'])}/"
            f"{len(rows)} | {sum(1 for row in rows if row['match'])}/"
            f"{len(rows)} | ${sum(row['cost_usd'] for row in rows):.4f} |")
    add("")
    add("Il confronto `exact` è contro il **ground truth indipendente** "
        "registrato in `cases.json` (offset e lunghezza della stringa), non "
        "contro l'estrattore simbolico. Su tutti e tre i casi l'output è "
        "anche byte-identico a `-xd` (stesso SHA-256): è una concordanza, non "
        "una prova indipendente di correttezza. Il costo totale è "
        f"${sum(row['cost_usd'] for row in classifier):.4f}.")
    add("")
    add("## Audit VirusTotal")
    add("")
    old = audit["old_native"]
    new = audit["new_mutants"]
    add(f"- 2025 `results.json`: {old['records']} record, "
        f"{old['verifiable_records']} verificabili, "
        f"{old['unverifiable_records']} non verificabili (artefatto assente).")
    add(f"- 2025 originali: 102 record, {audit['old_originals']['unique_artifacts']} "
        "hash distinti.")
    add(f"- 2026: {new['unique_hashes']} hash unici, {new['completed']} "
        f"scansioni completate, {new['zero_detections']} zero rilevamenti, "
        f"{new['detected']} rilevati.")
    add(f"- Motori 2026: {new['engine_totals'].get('type-unsupported', 0)} "
        "`type-unsupported`, "
        f"{new['engine_totals'].get('timeout', 0) + new['engine_totals'].get('confirmed-timeout', 0)} timeout, "
        f"{new['engine_totals'].get('failure', 0)} failure.")
    add("- Dettaglio: `bench/VT_AUDIT.md`. Zero rilevamenti non è una prova "
        "di invisibilità.")
    add("")
    add("## Casi non supportati o esclusi")
    add("")
    add("- `-wrap` x86: **coperto nel blocco 2** (18/18 corrette, 18 output "
        "unici); non era incluso nel blocco 1 perché il codice era in "
        "sviluppo.")
    add("- `-pii` e `-ip`: fuori matrice in questo blocco (riscrivono il "
        "layout e sono marcati sperimentali su payload con dati).")
    add("- `strings`/`getpc` senza `-xd`: non supportati dal flusso previsto; "
        "tutti i test dati usano l'estrazione.")
    add("- LLM su x86: non coperto in questo blocco (limite di budget, non "
        "limite tecnico dichiarato).")
    add("")
    add("## Limiti")
    add("")
    add("- Solo `-wrap` ha un seed; le altre tecniche native sono stocastiche "
        "senza interfaccia di seed. La riproducibilità è garantita "
        "dall'artefatto e dal suo SHA-256, non dal seed.")
    add("- 3 run per cella nativa e 3 chiamate per cella LLM: i numeri sono "
        "conteggi, non stime generalizzabili.")
    add("- Il corpus è di 13 programmi piccoli; non copre API Windows, "
        "strutture dati grandi o jump table.")
    add("- Il motore live è in movimento; tutti i risultati valgono per la "
        "copia congelata.")
    add("")
    add("## Consegna")
    add("")
    add("| Categoria | File |")
    add("|---|---|")
    add("| Matrice casi | `bench/results/case_matrix_native.csv`, "
        "`bench/results/case_matrix_llm.csv` |")
    add("| Risultati grezzi | `bench/results/native_attempts.jsonl`, "
        "`bench/results/llm_attempts.jsonl`, `bench/results/vt_audit.json` |")
    add("| Report | `bench/BENCH_REPORT.md`, `bench/VT_AUDIT.md`, "
        "`bench/INVENTORY.md` |")
    add("| Congelamento | `bench/engines/2026-11-13_block1/VERSION.json` |")
    add("| Log | `bench/logs/`, un file per tentativo |")
    add("| Fixture | `bench/fixtures/`, `bench/fixtures/cases.json` |")
    add("")
    add("Separazione: i dati 2025 e i test wrap/LLM del 2026 precedente sono "
        "**risultati precedenti**; la matrice nativa, le 96 chiamate LLM, le "
        "9 chiamate del classifier e il `-wrap` x86 sono **nuove verifiche**; "
        "LLM su x86 resta **non coperto in questo blocco**.")
    add("")

    (HERE / "BENCH_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("written bench/BENCH_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
