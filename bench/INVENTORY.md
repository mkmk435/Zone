# Inventario e riproducibilità — benchmark Zone

Data: 2026-11-13 (fuso Europe/Berlin). Stato al momento del congelamento.

## 1. Codice e ambiente

| Voce | Valore |
|---|---|
| Repository | `C:\Users\ubu\Desktop\Zone` |
| Branch / HEAD | `main` / `89affeaa3c76aab0403f4da0498d7a45c04173e8` ("Major commit", 2026-11-13 12:08) |
| Working tree | sporco; l'altra sessione sta ancora modificando `pobf.py`, `pobf86.py`, `asm_wrap.py`, `zone_utils.py`, `README.md` e i test x86 |
| Motore congelato (blocco 1) | `bench/engines/2026-11-13_block1/` — congelato 2026-11-13 13:07, hash in `VERSION.json` |
| `pobf.py` congelato (block1) | 192.929 B, `9af4589e2ca402a5...` |
| `pobf86.py` congelato (block1) | 199.010 B, `cc7f184db15d5e0c...` |
| `asm_wrap.py` congelato (block1) | 32.707 B, `5902cce09e923ff2...` |
| Motore congelato (blocco 2) | `bench/engines/2026-11-13_block2/` — congelato 2026-11-13 14:05 dopo la conferma di fine |
| `pobf.py` congelato (block2) | 193.789 B, `a93684dae13e66c1...` |
| `pobf86.py` congelato (block2) | 200.222 B, `28aa960551f4dfc4...` |
| `asm_wrap.py` congelato (block2) | 34.122 B, `aeeb0095a7d0b8a3...` |
| Python | 3.12.3, 64-bit |
| Capstone | 5.0.0 (il README raccomanda `5.0.0.post1`) |
| Keystone | 0.9.2 |
| Compilatore harness | MSVC 14.51 (VS 18 Community) |
| Runner x64 | `bench/harness/bin/runner_x64.exe`, SHA-256 `1B1209E7...` |
| Runner x86 | `bench/harness/bin/runner_x86.exe`, SHA-256 `6474F3F8...` |
| Sorgente runner | `bench/harness/runner.c`, SHA-256 `6BA71EDF...` |

Dopo il congelamento del blocco 1 l'altra sessione ha continuato a lavorare;
ha poi confermato di aver finito ed è stato congelato il blocco 2
(`pobf.py` 193.789 B, `pobf86.py` 200.222 B, `asm_wrap.py` 34.122 B). Tutti i
numeri del blocco 1 si riferiscono **solo** alla copia `2026-11-13_block1`;
classifier e `-wrap` x86 usano `2026-11-13_block2`.

## 2. Corpus già disponibile prima di questa sessione

| Dataset | x64 | x86 | Totale | Note |
|---|---:|---:|---:|---|
| `original_pl/` | 38 | 64 | 102 | shellcode Metasploit (rete + MessageBox) |
| `new_pl/new_pl/output/` | 52 | 100 | 152 | seconda generazione di payload |
| `tmp/low_payloads.json` | 13 | 36 | 49 | sottoinsieme a working rate storico < 50% |
| artefatti mutati 2025 | — | — | 8.048 | su 15.021 record VT del 2025 |
| mutanti 2026 (blocco precedente) | 200 wrap + 24 LLM + 15 data | — | 239 | 220 SHA-256 unici |

## 3. Risultati già disponibili

### VirusTotal

| Dataset | Record | Verificabili | Non verificabili | Zero rilevamenti | Rilevati | Periodo |
|---|---:|---:|---:|---:|---:|---|
| `results.json` (2025) | 15.021 | 8.049 | 6.972 | 6.026 | 2.023 | 2025-04-30 .. 2025-09-17 |
| `results_original.json` (2025) | 102 | 102 | 0 | 0 | 102 | 2025-05-06 |
| `results_sgn.json` (2025) | 102 | 102 | 0 | 38 | 64 | 2025-05-06 |
| `vt_manifest.json` (2026) | 239 righe → 220 hash | 220 | 0 | 208 | 12 | 2026-11-13 |
| `vt_originals.json` (2026) | 13 | 13 | 0 | 0 | 13 | 2026-11-13 |

Dettaglio e controlli: `bench/VT_AUDIT.md` e `bench/results/vt_audit.json`.
I 6.972 record 2025 non verificabili hanno l'artefatto assente dal disco:
non sono ricontrollabili e non vanno contati come campioni validi.
I 102 originali 2025 corrispondono a 90 hash distinti; anche i 239 file 2026
corrispondono a 220 hash: ci sono duplicati, quindi non sono campioni
indipendenti.

### Working rate

| Fonte | Righe / esito |
|---|---|
| `test_report.txt` (2025) | 15.020 righe, 102 payload × 15 tecniche |
| `test_report_x64_low_*.txt` | 1.950 righe ciascuno (13 x64 × 15 × 10) |
| `new_test_report_5run.csv` | 5.270 righe (49 payload) |
| `tmp/wrap_report.csv` (2026) | 200 test, 198 OK |
| `tmp/llm_morph_report.csv` (2026) | 24 test, 24 OK |
| `tmp/llm_data_report.csv` (2026) | 15 test, 15 OK |
| `bench/results/native_attempts.jsonl` (blocco 1) | 177 tentativi, 159 corretti |
| `bench/results/native_wrap86.jsonl` (blocco 2) | 18 tentativi, 18 corretti |
| `bench/results/llm_attempts.jsonl` (blocco 1) | 96 chiamate, 95 corrette |
| `bench/results/llm_data_attempts.jsonl` (blocco 2) | 9 chiamate, 9 esatte e 9 corrette |

### Costi già sostenuti (blocco precedente)

| Blocco | Costo API |
|---|---:|
| LLM morphing (24 run, inclusa una cella fallita e ripetuta) | ~$0,585 |
| LLM data classifier (15 run) | ~$0,105 |
| LLM morphing benigno (96 chiamate, blocco 1) | ~$0,295 |
| LLM data classifier benigno (9 chiamate, blocco 2) | ~$0,003 |

## 4. Cosa era già stato testato (e cosa mancava)

I casi precedenti sono tutti shellcode Metasploit con comportamento di rete
(reverse/bind) o MessageBox. Non esistevano fixture innocue con un risultato
verificabile byte per byte: calcolo, stringhe, diramazioni, cicli, dati inline
e chiamate locali non erano coperti. Ripetere MessageBox non aggiunge
copertura funzionale, quindi questa sessione introduce un corpus separato.

## 5. Nuovo corpus benigno (blocco 1)

13 fixture assemblate con Keystone a base 0, eseguite su CPU reale dal runner
C (buffer di 256 byte, sentinella `0xCC`):

| Caso | x64 | x86 | Comportamento atteso |
|---|:--:|:--:|---|
| `arith` | sì | sì | `(0x12345678 + 0x1111 - 0x2222) * 3`, poi somma 1..5 |
| `branch` | sì | sì | due if/else, valori `0xAAAA` e `0x1111` |
| `loop` | sì | sì | somma 1..100 = 5050 |
| `call` | sì | sì | subroutine locale ×4 = 28 |
| `mixed` | sì | sì | ciclo + branch + call = 121 |
| `strings` | sì | sì | stringa inline copiata nel buffer (`-xd`) |
| `getpc` | sì | — | `call`/`pop` con dati tra call e consumer (`-xd`) |

Ogni caso dichiara in `bench/fixtures/cases.json` i byte attesi, il criterio
(uguaglianza esatta del buffer, resto a `0xCC`) e, per i casi dati, l'intervallo
di dati ground truth (offset/lunghezza). Gli originali sono stati eseguiti e
verificati **prima** di qualsiasi trasformazione: 13/13 OK.

## 6. Matrice del blocco 1

| Dimensione | Valori |
|---|---|
| Architetture | x64, x86 |
| Casi | 13 fixture (7 x64, 6 x86) |
| Tecniche native | `eq`, `nop`, `bcf`, `ibp` su entrambe; `wrap` x64 (blocco 1) e x86 (blocco 2) |
| Run per cella | 3 |
| Casi dati | `-xd` come preprocessing dichiarato |
| LLM morphing | 4 casi x64 (`arith`, `branch`, `call`, `getpc`) × 4 tecniche × {0,2} shot × 3 chiamate |
| LLM data classifier | 3 casi dati × 3 chiamate (blocco 2, dopo conferma esplicita) |

Metriche separate: build riuscite/tentativi, esecuzioni corrette/build
riuscite, esecuzioni corrette/tentativi, output unici/output prodotti.
Per ogni tentativo: seed (solo `wrap`), hash, flag, log, esito.

## 7. Limiti di riproducibilità dichiarati

- Solo `-wrap` accetta un seed (`ZONE_WRAP_SEED`). `eq`, `nop`, `bcf`, `ibp`
  usano il RNG interno senza interfaccia di seed: la riproducibilità è
  garantita dall'artefatto salvato e dal suo hash, non dal seed.
- Il motore live è cambiato durante la sessione: il blocco 1 usa la copia
  `2026-11-13_block1`, classifier e `-wrap` x86 usano `2026-11-13_block2`.
- Il 46% dei record VT 2025 non ha più l'artefatto: non è verificabile.
- `malicious = 0` su VirusTotal non è una prova di invisibilità: 19,8% delle
  risposte 2026 sono `type-unsupported`, più 283 timeout e 73 failure.
- Tre file `-wrap` del blocco precedente sono byte-identici per collisione di
  seed; non vanno contati come campioni indipendenti.

## 8. Attività di questa sessione e stato

| Attività | Stato |
|---|---|
| Inventario e congelamento | completato (blocchi 1 e 2) |
| Corpus benigno + runner | completato (13/13 originali OK) |
| Matrice nativa | completata: 177 tentativi blocco 1 + 18 `-wrap` x86 blocco 2 |
| Matrice LLM 0/2-shot | completata: 96 chiamate |
| Classifier LLM | completato: 9 chiamate, 9/9 esatte sul ground truth |
| Audit VT | completato |
| Report sintetico | completato (`bench/BENCH_REPORT.md`) |

## 9. Aggiornamento 2026-11-13 (fase di completamento)

- LLM morphing: 168 chiamate x64 (block1) e 144 x86 (block2), 3 per cella;
  305 corrette, 5 rifiuti del validatore, 2 errori di rete; costo aggiuntivo
  $0,7457 (vedi `bench/BUDGET.md`).
- Classifier: 6 fixture nuove con ground truth indipendente (senza dati,
  due intervalli, tabella binaria, finto dato ASCII); 18 chiamate LLM e 6
  esecuzioni simboliche, tutte esatte.
- Consolidamento: `bench/ALL_TESTS_REPORT.md`,
  `bench/results/all_test_runs.csv`, `bench/results/coverage_matrix.csv`,
  `bench/results/remaining_gaps.csv`. Celle di matrice mancanti: 0.
- I file di questo inventario descrivono il blocco precedente; il
  consolidamento aggiornato è in `bench/ALL_TESTS_REPORT.md`.
