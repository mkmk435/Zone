# Benchmark Zone — copertura funzionale, LLM e audit VirusTotal

Blocco 1 (nativo e LLM): motore congelato `bench/engines/2026-11-13_block1` (git `89affeaa`, congelato 2026-11-13T13:07:27+0100). Blocco 2 (classifier e `-wrap` x86): `bench/engines/2026-11-13_block2`, congelato dopo la conferma.

## Sintesi

- Corpus benigno nuovo: **13 fixture** (7 x64, 6 x86), 13/13 originali verificati contro il risultato atteso dichiarato.
- Matrice nativa: **177 tentativi**, 176 build riuscite (99.4%), 159 esecuzioni corrette (89.8% sui tentativi, 90.3% sulle build).
- LLM morphing: **96 chiamate** (4 casi x 4 tecniche x 0/2 shot x 3 chiamate), 95 build e 95 esecuzioni corrette; costo $0.2947.
- Estensione blocco 2 (motore successivo, dopo la conferma): `-wrap` x86 su 6 casi, 18 tentativi, 18 corrette, 18 output unici.
- Il classifier LLM (blocco 2, motore congelato dopo la conferma esplicita) è stato eseguito: 9 chiamate, 9/9 classificazioni esatte rispetto al ground truth, 9 esecuzioni corrette, costo $0.0034.
- Audit VT: nessuna nuova sottomissione; 6.972 record 2025 non verificabili per artefatto assente, 220/220 scansioni 2026 completate.

## Metodo

Ogni caso dichiara prima del test: sorgente assembly, byte attesi nel buffer di 256 byte, criterio di successo (uguaglianza esatta, resto `0xCC`), e per i casi dati l'intervallo ground truth. Il runner C (`bench/harness/runner.c`, compilato MSVC x64 e x86) mappa il payload RWX, lo esegue sulla CPU reale e scrive il buffer; un crash del processo è un fallimento, non un risultato.

| Dimensione | Valori |
|---|---|
| Architetture | x64, x86 |
| Tecniche native | `eq`, `nop`, `bcf`, `ibp` (entrambe); `wrap` x64 (blocco 1) e x86 (blocco 2) |
| Run per cella nativa | 3 |
| Preprocessing dati | `-xd` dichiarato per `strings`/`getpc` |
| LLM | 4 casi x64 x 4 tecniche x {0,2} shot x 3 chiamate |
| Metriche | build/tentativi, corrette/build, corrette/tentativi, unici/prodotti |

## Copertura

| Caso | Tipo | x64 | x86 | Dati inline | Comportamento atteso |
|---|:--:|:--:|:--:|:--:|---|
| `arith` | calcolo | sì | sì | no | buffer esatto sui byte dichiarati |
| `branch` | diramazioni | sì | sì | no | buffer esatto sui byte dichiarati |
| `loop` | cicli | sì | sì | no | buffer esatto sui byte dichiarati |
| `call` | chiamate_locali | sì | sì | no | buffer esatto sui byte dichiarati |
| `mixed` | misto | sì | sì | no | buffer esatto sui byte dichiarati |
| `strings` | stringhe_dati_inline | sì | sì | sì | buffer esatto sui byte dichiarati |
| `getpc` | dati_inline_getpc | sì | — | sì | buffer esatto sui byte dichiarati |

Ground truth dati: `strings` x64 offset 25 len 13, `getpc` x64 offset 5 len 12, `strings` x86 offset 9 len 12 (stringa + NUL).

## Risultati nativi

| Arch | Tecnica | Tentativi | Build | Build rate | Corrette/build | Corrette/tentativi | Unici/prodotti |
|---|:--:|---:|---:|---:|---:|---:|---:|
| x64 | `eq` | 21 | 21 | 100.0% | 100.0% | 100.0% | 16/21 |
| x64 | `nop` | 21 | 21 | 100.0% | 100.0% | 100.0% | 21/21 |
| x64 | `bcf` | 21 | 21 | 100.0% | 100.0% | 100.0% | 21/21 |
| x64 | `ibp` | 21 | 21 | 100.0% | 100.0% | 100.0% | 17/21 |
| x64 | `wrap` | 21 | 21 | 100.0% | 100.0% | 100.0% | 21/21 |
| x86 | `eq` | 18 | 18 | 100.0% | 100.0% | 100.0% | 14/18 |
| x86 | `nop` | 18 | 18 | 100.0% | 100.0% | 100.0% | 18/18 |
| x86 | `bcf` | 18 | 18 | 100.0% | 100.0% | 100.0% | 18/18 |
| x86 | `ibp` | 18 | 17 | 94.4% | 0.0% | 0.0% | 16/17 |

Per caso (tutte le tecniche native insieme):

| Arch | Caso | Tentativi | Build | Corrette | Unici |
|---|:--:|---:|---:|---:|---:|
| x64 | `arith` | 15 | 15 | 15 | 14 |
| x64 | `branch` | 15 | 15 | 15 | 13 |
| x64 | `call` | 15 | 15 | 15 | 13 |
| x64 | `getpc` | 15 | 15 | 15 | 13 |
| x64 | `loop` | 15 | 15 | 15 | 11 |
| x64 | `mixed` | 15 | 15 | 15 | 15 |
| x64 | `strings` | 15 | 15 | 15 | 14 |
| x86 | `arith` | 12 | 12 | 9 | 12 |
| x86 | `branch` | 12 | 12 | 9 | 9 |
| x86 | `call` | 12 | 12 | 9 | 11 |
| x86 | `loop` | 12 | 11 | 9 | 10 |
| x86 | `mixed` | 12 | 12 | 9 | 12 |
| x86 | `strings` | 12 | 12 | 9 | 11 |

### Estensione blocco 2: `-wrap` x86

Il wrapping x86 era in sviluppo durante il blocco 1; dopo la conferma di fine è stato congelato come blocco 2 e testato sugli stessi 6 casi x86.

| Caso | Tentativi | Build | Corrette | Unici |
|---|:--:|:--:|:--:|:--:|
| `arith` | 3 | 3 | 3 | 3 |
| `branch` | 3 | 3 | 3 | 3 |
| `call` | 3 | 3 | 3 | 3 |
| `loop` | 3 | 3 | 3 | 3 |
| `mixed` | 3 | 3 | 3 | 3 |
| `strings` | 3 | 3 | 3 | 3 |

Totale: 18 tentativi, 18 build, 18 corrette.

Baseline `-xd`: 3 estrazioni, 3 corrette.

### Fallimenti nativi

18 tentativi non corretti, tutti `x86` + `-ibp`:

- `x86/arith` run 1: build=True, esito=payload crashed or produced no output
- `x86/arith` run 3: build=True, esito=payload crashed or produced no output
- `x86/arith` run 2: build=True, esito=payload crashed or produced no output
- `x86/branch` run 3: build=True, esito=payload crashed or produced no output
- `x86/branch` run 1: build=True, esito=payload crashed or produced no output
- `x86/branch` run 2: build=True, esito=payload crashed or produced no output
- `x86/loop` run 2: build=False, esito=   self.instr_blocks = [self.instr_blocks[0]] + blocks
                         ~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

- `x86/call` run 1: build=True, esito=payload crashed or produced no output
- `x86/call` run 2: build=True, esito=payload crashed or produced no output
- `x86/loop` run 1: build=True, esito=payload crashed or produced no output
- `x86/loop` run 3: build=True, esito=payload crashed or produced no output
- `x86/strings` run 2: build=True, esito=payload crashed or produced no output
- `x86/strings` run 1: build=True, esito=payload crashed or produced no output
- `x86/strings` run 3: build=True, esito=payload crashed or produced no output
- `x86/call` run 3: build=True, esito=payload crashed or produced no output
- `x86/mixed` run 2: build=True, esito=payload crashed or produced no output
- `x86/mixed` run 3: build=True, esito=payload crashed or produced no output
- `x86/mixed` run 1: build=True, esito=payload crashed or produced no output

Il pattern è sistematico: su 18 tentativi x86 `-ibp`, 17 costruiscono e nessuno esegue; 1 build fallisce con `IndexError`. x64 `-ibp` è 21/21. Non è un problema del runner: gli originali e `eq`/`nop`/`bcf` sugli stessi casi passano.

## LLM morphing

| Tecnica | Shot | Chiamate | Build | Corrette | Unici | Costo |
|---|:--:|---:|---:|---:|---:|---:|
| `bcf` | 0 | 12 | 12 | 12 | 12 | $0.0658 |
| `bcf` | 2 | 12 | 12 | 12 | 11 | $0.0501 |
| `eq` | 0 | 12 | 12 | 12 | 8 | $0.0418 |
| `eq` | 2 | 12 | 12 | 12 | 7 | $0.0442 |
| `ibp` | 0 | 12 | 12 | 12 | 8 | $0.0310 |
| `ibp` | 2 | 12 | 11 | 11 | 8 | $0.0292 |
| `nop` | 0 | 12 | 12 | 12 | 11 | $0.0170 |
| `nop` | 2 | 12 | 12 | 12 | 12 | $0.0156 |

0-shot: 48/48 corrette, 39 output unici, costo $0.1556. 2-shot: 47/48 corrette, 38 unici, costo $0.1391. La differenza è dentro il rumore di 3 chiamate per cella.

Output unici totali: 66/95. Le risposte identiche non sono campioni indipendenti.

Fallimenti LLM: 1.
- `branch/ibp/s2/chiamata 1`: build=False, IBP did not permute blocks: the original instruction order is unchanged (the tool requires at least two non-entry blocks to be reordered)

## LLM data classifier

Eseguito dopo conferma esplicita che l'altra sessione aveva finito, sul **blocco 2** (`bench/engines/2026-11-13_block2`, congelato 2026-11-13T14:05, hash in `VERSION.json`). I 5 test offline di `test_llm_data.py` passano sulla copia congelata.

| Caso | Chiamate | Classificazione esatta | Build | Esecuzione corretta | Costo |
|---|:--:|:--:|:--:|:--:|---:|
| x64/`getpc` | 3 | 3/3 | 3/3 | 3/3 | $0.0012 |
| x64/`strings` | 3 | 3/3 | 3/3 | 3/3 | $0.0011 |
| x86/`strings` | 3 | 3/3 | 3/3 | 3/3 | $0.0011 |

Il confronto `exact` è contro il **ground truth indipendente** registrato in `cases.json` (offset e lunghezza della stringa), non contro l'estrattore simbolico. Su tutti e tre i casi l'output è anche byte-identico a `-xd` (stesso SHA-256): è una concordanza, non una prova indipendente di correttezza. Il costo totale è $0.0034.

## Audit VirusTotal

- 2025 `results.json`: 15021 record, 8049 verificabili, 6972 non verificabili (artefatto assente).
- 2025 originali: 102 record, 90 hash distinti.
- 2026: 220 hash unici, 220 scansioni completate, 208 zero rilevamenti, 12 rilevati.
- Motori 2026: 3259 `type-unsupported`, 283 timeout, 73 failure.
- Dettaglio: `bench/VT_AUDIT.md`. Zero rilevamenti non è una prova di invisibilità.

## Casi non supportati o esclusi

- `-wrap` x86: **coperto nel blocco 2** (18/18 corrette, 18 output unici); non era incluso nel blocco 1 perché il codice era in sviluppo.
- `-pii` e `-ip`: fuori matrice in questo blocco (riscrivono il layout e sono marcati sperimentali su payload con dati).
- `strings`/`getpc` senza `-xd`: non supportati dal flusso previsto; tutti i test dati usano l'estrazione.
- LLM su x86: non coperto in questo blocco (limite di budget, non limite tecnico dichiarato).

## Limiti

- Solo `-wrap` ha un seed; le altre tecniche native sono stocastiche senza interfaccia di seed. La riproducibilità è garantita dall'artefatto e dal suo SHA-256, non dal seed.
- 3 run per cella nativa e 3 chiamate per cella LLM: i numeri sono conteggi, non stime generalizzabili.
- Il corpus è di 13 programmi piccoli; non copre API Windows, strutture dati grandi o jump table.
- Il motore live è in movimento; tutti i risultati valgono per la copia congelata.

## Consegna

| Categoria | File |
|---|---|
| Matrice casi | `bench/results/case_matrix_native.csv`, `bench/results/case_matrix_llm.csv` |
| Risultati grezzi | `bench/results/native_attempts.jsonl`, `bench/results/llm_attempts.jsonl`, `bench/results/vt_audit.json` |
| Report | `bench/BENCH_REPORT.md`, `bench/VT_AUDIT.md`, `bench/INVENTORY.md` |
| Congelamento | `bench/engines/2026-11-13_block1/VERSION.json` |
| Log | `bench/logs/`, un file per tentativo |
| Fixture | `bench/fixtures/`, `bench/fixtures/cases.json` |

Separazione: i dati 2025 e i test wrap/LLM del 2026 precedente sono **risultati precedenti**; la matrice nativa, le 96 chiamate LLM, le 9 chiamate del classifier e il `-wrap` x86 sono **nuove verifiche**; LLM su x86 resta **non coperto in questo blocco**.
