# Tutti i test — consolidamento, copertura e limiti

Questo documento accorpa i risultati disponibili, ma **non è una campagna completa sull'intero corpus originale**: il nuovo benchmark funzionale copre 13 fixture innocue (7 x64, 6 x86) più 6 fixture classifier; i 102 payload Metasploit restano coperti solo dalle campagne storiche, e i loro risultati non vengono mescolati con quelli del corpus benigno.

## 1. Fonti e denominatari

| Campagna | Fonte | Tipo | Granularità | Dati grezzi |
|---|---|---|---|---|
| `bench_block1_native` | `bench/results/native_attempts.jsonl` | funzionale | run | sì (log + hash per run) |
| `bench_block2_wrap86` | `bench/results/native_wrap86.jsonl` | funzionale | run | sì |
| `bench_block1_llm` | `bench/results/llm_attempts.jsonl` | funzionale LLM | chiamata | sì (stats + log) |
| `bench_block2_llm` | `bench/results/llm_attempts_x86.jsonl` | funzionale LLM | chiamata | sì |
| `bench_block2_classifier` | `bench/results/llm_data_attempts.jsonl` | classifier | chiamata | sì |
| `bench_block2_classifier_fixtures` | `bench/results/classifier_compare.jsonl` | classifier | chiamata | sì (ground truth + predizione) |
| `prev_2026_wrap` | `mutations_wrap/manifest.jsonl + tmp/wrap_report.csv` | campagna precedente | tentativo | sì |
| `prev_2026_llm` | `tmp/llm_run/stats + tmp/llm_morph_report.csv` | campagna precedente LLM | tentativo API | sì |
| `prev_2026_classifier` | `tmp/lldata_run/stats + tmp/llm_data_report.csv` | campagna precedente classifier | cella | sì |
| `legacy_2025_working` | `test_report.txt` | storico 2025 | cella riassuntiva | parziale: righe grezze, artefatti non rieseguiti |
| `legacy_2025_vt` | `results.json` | storico VT | dataset | parziale: 8.049/15.021 artefatti verificati |
| `prev_2026_vt` | `vt_manifest.json + tmp/vt_results.jsonl` | VT 2026 | dataset | sì (hash ricalcolati) |

### 1.1 Denominatori

- **Build / tentativi**: binari prodotti sul totale dei tentativi di build (o chiamate LLM).
- **Corrette / build**: esecuzioni con buffer uguale al ground truth sui binari prodotti.
- **Corrette / tentativi**: esecuzioni corrette sul totale dei tentativi, incluse build fallite e rifiuti.
- **Unici / prodotti**: SHA-256 distinti sui binari prodotti; output identici non sono campioni indipendenti.
- **Classificazione esatta**: sezioni predette uguali agli intervalli ground truth (offset e lunghezza).
- **Byte mancati / byte di codice come dati**: byte di ground truth non coperti / byte predetti fuori dagli intervalli attesi.
- **VT completate / scansioni**: scansioni con risultato valido sul totale dei record; i non verificabili sono contati a parte.
## 2. Nuovo benchmark benigno

### 2.1 Baseline

- Payload originali: 13/13 risultati attesi verificati prima delle trasformazioni.
- Baseline `-xd`: 4 estrazioni, 4 corrette (`bench_block1_baseline` + `bench_block2_baseline`).

### 2.2 Trasformazioni native

| Arch | Tecnica | Versione | Tentativi | Build | Corrette/build | Corrette/tentativi | Unici/prodotti |
|---|:--:|---|---:|---:|---:|---:|---:|
| x64 | `bcf` | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 21/21 |
| x64 | `eq` | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 16/21 |
| x64 | `ibp` | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 17/21 |
| x64 | `nop` | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 21/21 |
| x64 | `wrap` | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 21/21 |
| x86 | `bcf` | `2026-11-13_block1` | 18 | 18 | 100.0% | 100.0% | 18/18 |
| x86 | `eq` | `2026-11-13_block1` | 18 | 18 | 100.0% | 100.0% | 14/18 |
| x86 | `ibp` | `2026-11-13_block1` | 18 | 17 | 0.0% | 0.0% | 16/17 |
| x86 | `nop` | `2026-11-13_block1` | 18 | 18 | 100.0% | 100.0% | 18/18 |
| x86 | `wrap` | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 18/18 |

Fonte: `bench/results/native_attempts.jsonl` (block1) e `bench/results/native_wrap86.jsonl` (block2). Denominatori: tentativi = run native; build = binari prodotti; corrette = buffer uguale al ground truth dichiarato; unici = SHA-256 distinti.

### 2.3 LLM morphing

| Arch | Tecnica | Shot | Versione | Chiamate | Build | Corrette/build | Corrette/chiamate | Unici/prodotti | Costo |
|---|:--:|:--:|---|---:|---:|---:|---:|---:|---:|
| x64 | `bcf` | 0 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 18/21 | $0.1068 |
| x64 | `bcf` | 2 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 20/21 | $0.0878 |
| x64 | `eq` | 0 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 12/21 | $0.0640 |
| x64 | `eq` | 2 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 11/21 | $0.0679 |
| x64 | `ibp` | 0 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 14/21 | $0.0618 |
| x64 | `ibp` | 2 | `2026-11-13_block1` | 21 | 20 | 100.0% | 95.2% | 15/20 | $0.0772 |
| x64 | `nop` | 0 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 18/21 | $0.0274 |
| x64 | `nop` | 2 | `2026-11-13_block1` | 21 | 21 | 100.0% | 100.0% | 20/21 | $0.0277 |
| x86 | `bcf` | 0 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 18/18 | $0.1029 |
| x86 | `bcf` | 2 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 17/18 | $0.0952 |
| x86 | `eq` | 0 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 11/18 | $0.0556 |
| x86 | `eq` | 2 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 11/18 | $0.0668 |
| x86 | `ibp` | 0 | `2026-11-13_block2` | 18 | 13 | 100.0% | 72.2% | 9/13 | $0.0519 |
| x86 | `ibp` | 2 | `2026-11-13_block2` | 18 | 17 | 100.0% | 94.4% | 12/17 | $0.0707 |
| x86 | `nop` | 0 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 18/18 | $0.0316 |
| x86 | `nop` | 2 | `2026-11-13_block2` | 18 | 18 | 100.0% | 100.0% | 18/18 | $0.0386 |

- x64 (`2026-11-13_block1`): 168 chiamate, 167 build, 167 corrette, 108 output unici, costo $0.5205. Le percentuali restano per cella/tecnica nelle tabelle sopra: x64 e x86 usano versioni diverse e non vengono sommati in un'unica percentuale.
- x86 (`2026-11-13_block2`): 144 chiamate, 138 build, 138 corrette, 99 output unici, costo $0.5132. Le percentuali restano per cella/tecnica nelle tabelle sopra: x64 e x86 usano versioni diverse e non vengono sommati in un'unica percentuale.

Fonte: `bench/results/llm_attempts.jsonl` (x64, block1) e `bench/results/llm_attempts_x86.jsonl` (x86, block2). Una chiamata = una generazione; massimo 3 per cella, retry inclusi.

### 2.4 Classifier sul corpus benigno (3 casi dati)

| Caso | Chiamate | Classificazione esatta | Build | Esecuzione | Costo |
|---|---:|---:|---:|---:|---:|
| x64/`getpc` | 3 | 3/3 | 3 | 3 | $0.0012 |
| x64/`strings` | 3 | 3/3 | 3 | 3 | $0.0011 |
| x86/`strings` | 3 | 3/3 | 3 | 3 | $0.0011 |

### 2.5 Classifier con ground truth indipendente (6 fixture)

| Caso | Arch | Metodo | Run | Esatte | Byte mancati | Byte di codice classificati come dati | Build | Esecuzione | Tempo medio | Costo |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `databait` | x64 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 4.6s | $0.0014 |
| `databait` | x64 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.4s | $0.0000 |
| `multidata` | x64 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 4.2s | $0.0014 |
| `multidata` | x64 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.6s | $0.0000 |
| `multidata` | x86 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 4.4s | $0.0015 |
| `multidata` | x86 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.5s | $0.0000 |
| `nodata` | x64 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 2.1s | $0.0004 |
| `nodata` | x64 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.4s | $0.0000 |
| `nodata` | x86 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 1.9s | $0.0005 |
| `nodata` | x86 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.3s | $0.0000 |
| `table` | x64 | llm | 3 | 3/3 | 0 | 0 | 3 | 3 | 2.6s | $0.0007 |
| `table` | x64 | symbolic | 1 | 1/1 | 0 | 0 | 1 | 1 | 2.4s | $0.0000 |

Concordanza LLM ↔ estrattore simbolico: **18/18** chiamate. È una concordanza tra metodi, distinta dalla correttezza rispetto al ground truth (colonne qui sopra).

Fonti: `bench/results/llm_data_attempts.jsonl` e `bench/results/classifier_compare.jsonl`. Il ground truth è in `bench/fixtures/classifier_cases.json` ed è stato definito prima delle chiamate; il modello non lo ha ricevuto.

## 3. Campagne precedenti (2026, prima di questo consolidamento)

- `prev_2026_wrap`: 260 tentativi, 200 build, 198 corrette, 197 output unici. Include 60 build fallite sui payload `*_winhttps`.
- `prev_2026_llm`: 27 tentativi registrati nei file stats (più 3 della run fallita iniziale, conservata solo come aggregato), 24 accettati, 24 corretti, costo $0.5055.
- `prev_2026_classifier`: 19 tentativi, 15 corretti, costo $0.1049.

Fonte: `mutations_wrap/manifest.jsonl`, `tmp/wrap_report.csv`, `tmp/llm_run/stats/`, `tmp/lldata_run/stats/`. Sono campagne precedenti: non vengono ricalcolate né sostituite dai nuovi run.

## 4. Campagne storiche 2025

- Working rate storico: 15020 righe, 7395 OK, 1518 celle (payload × tecnica). La build non è registrata e gli artefatti non sono stati rieseguiti: è un riepilogo, non una riverifica.
- VirusTotal 2025: 15.021 record, 8.049 verificabili, 6.972 non verificabili (artefatto assente); 102 originali e 102 SGN.

Fonte: `test_report.txt`, `results.json`, `results_original.json`, `results_sgn.json`. Il working rate 2025 è un riepilogo da righe grezze ma **non è verificato sui dati grezzi** (artefatti non rieseguiti, build non registrata).

## 5. VirusTotal storico (solo lettura)

| Dataset | Scansioni | Completate | Zero rilevamenti | Rilevati | Non verificabili |
|---|---:|---:|---:|---:|---:|
| `legacy_2025_vt` | 15021 | 8049 | 6026 | 2023 | 6972 |
| `legacy_2025_vt_originals` | 102 | 102 | 0 | 102 | 0 |
| `legacy_2025_vt_sgn` | 102 | 102 | 38 | 64 | 0 |
| `prev_2026_vt` | 220 | 220 | 208 | 12 | 0 |
| `prev_2026_vt_originals` | 13 | 13 | 0 | 13 | 0 |

Motori 2026: 3.259 `type-unsupported`, 283 timeout, 73 failure su 16.500 risposte. Zero rilevamenti non è una prova di invisibilità; analisi incomplete e risultati mancanti restano visibili sopra.

## 6. Fallimenti osservati

- **IBP x86**: 18 tentativi, 17 build, 0 esecuzioni corrette; un build termina con `IndexError` in `shuffle_blocks`. Resta un fallimento noto del blocco 1; la causa non è attribuita oltre l'eccezione osservata.
- **LLM nuovo benchmark**: 7 chiamate non corrette su 312: 5 rifiuti del validatore (IBP non permutato, x86 branch e x64 branch), 2 errori di rete (`IncompleteRead`, risposta troncata, costo 0), 0 altri. Nessuno è stato sostituito.
- **Wrap precedente**: 60 build fallite (tre payload `*_winhttps`) e 2 esecuzioni fallite sui 200 binari costruiti.

## 7. Copertura e gap

Celle di matrice mancanti: **0**.
- Nessuna cella della matrice attesa risulta incompleta.

Gap dichiarati:
- benign13 / (tutte) / `pii/ip`: tecniche layout-owning fuori matrice per scelta documentata (missing=78).
- classifier6 / (tutte) / `vt`: nessuna sottomissione VT per il corpus benigno (richiesta esplicita: solo report storici in lettura) (missing=0).
- metasploit102 / (tutte) / `vt`: artefatti 2025 assenti: record VT non verificabili (missing=6972).
- metasploit102 / (tutte) / `build`: i report 2025 non registrano build/esito per tentativo: solo working rate (missing=15020).

## 8. Costi

| Campagna | Tentativi/chiamate | Costo | Fonte |
|---|---:|---:|---|
| `bench_block1_llm` | 168 | $0.5205 | campo `cost_usd` dei risultati |
| `bench_block2_llm` | 144 | $0.5132 | campo `cost_usd` dei risultati |
| `bench_block2_classifier` | 9 | $0.0034 | campo `cost_usd` dei risultati |
| `bench_block2_classifier_fixtures` | 24 | $0.0059 | campo `cost_usd` dei risultati |
| `prev_2026_llm` | 27 | $0.5055 | campo `cost_usd` dei risultati |
| `prev_2026_classifier` | 19 | $0.1049 | campo `cost_usd` dei risultati |

Nota: `bench_block2_classifier_fixtures` conta 24 run (18 chiamate LLM + 6 esecuzioni simboliche gratuite); solo le 18 LLM hanno costo. `prev_2026_llm` non include $0,0796 di una run fallita registrata solo come aggregato nel log; il costo delle nuove chiamate è quello dei file di risultato per chiamata. I costi non sono sommati in un unico totale.

## 9. File

- `bench/results/all_test_runs.csv` — una riga per run/chiamata o cella riassuntiva, con fonte.
- `bench/results/coverage_matrix.csv` — matrice aggregata.
- `bench/results/remaining_gaps.csv` — celle e dati mancanti.
- `bench/results/classifier_compare.jsonl` — predizioni e ground truth del classifier.
- `bench/engines/2026-11-13_block1|block2/VERSION.json` — versioni.
- `bench/VT_AUDIT.md`, `bench/INVENTORY.md`, `bench/BUDGET.md`.

## 10. Conclusione

Completati: corpus benigno 13/13, matrice nativa, LLM x64 e x86 con 3 chiamate per cella, classifier su corpus e su 6 fixture con ground truth, audit VT. Fallimenti osservati: IBP x86 (0/18 corrette), 5 rifiuti del validatore LLM e 2 errori di rete LLM, 60 build wrap storiche. Non coperti: `-pii`/`-ip`, payload originali 2025 non rieseguiti, 6.972 record VT 2025 senza artefatto, nessuna scansione VT del corpus benigno.
