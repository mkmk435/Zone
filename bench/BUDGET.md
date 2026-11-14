# Budget della fase di completamento

Budget operativo della sessione: **1,00 USD** di chiamate API, oltre al costo
già sostenuto e rendicontato (`bench/INVENTORY.md`). Il vincolo di progetto
resta **massimo 3 chiamate di generazione per cella** (caso × tecnica × shot),
retry inclusi; nessuna cella viene sostituita se fallisce.

Spesa già registrata prima di questa fase: $0,2947 + $0,0034 = **$0,2981**.
Budget **aggiuntivo** per il completamento: **$1,00** (spesa totale di
sessione ammessa: $1,2981). I guard dei due job sono stati impostati a
`--max-cost 0.30` (x64) e `--max-cost 0.55` (x86), per una somma massima di
$0,85 più il classifier.

## Preventivo calcolato prima delle chiamate

| Gruppo | Celle | Chiamate | Costo stimato |
|---|---:|---:|---:|
| x64 LLM mancanti (`strings`, `loop`, `mixed`) | 24 | 72 | 72 × $0,00307 = **$0,221** |
| x86 LLM (6 casi × 4 tecniche × 2 shot) | 48 | 144 | 144 × $0,00200 = **$0,288** |
| Classifier nuove fixture (6 casi) | 6 | 18 | 18 × $0,00038 = **$0,007** |
| **Totale stimato** | | **234** | **$0,516** |

## Consumi registrati (fonte: file di risultato, non stime)

| Blocco | Chiamate | Costo registrato | Fonte |
|---|---:|---:|---|
| LLM morphing benigno blocco 1 | 96 | $0,2947 | `bench/results/llm_attempts.jsonl` |
| LLM data classifier blocco 2 | 9 | $0,0034 | `bench/results/llm_data_attempts.jsonl` |

Costo medio per chiamata LLM morphing: $0,2947 / 96 = **$0,00307**.
Costo medio per chiamata classifier: $0,0034 / 9 = **$0,00038**.
Pilota x86 fuori corpus (verifica di supporto): $0,00077
(`bench/run/llm86_pilot/stats.json`), non conteggiato come cella.

## Consuntivo (dopo il completamento)

| Voce | Chiamate | Costo |
|---|---:|---:|
| x64 LLM mancanti (`strings`, `loop`, `mixed`) | 72 | $0,2258 |
| x86 LLM (6 casi × 4 tecniche × 2 shot) | 144 | $0,5132 |
| Classifier nuove fixture (6 casi) | 18 LLM + 6 simboliche | $0,0059 |
| Pilota LLM x86 fuori corpus | 1 | $0,0008 |
| **Spesa aggiuntiva effettiva** | | **$0,7457** |
| Budget aggiuntivo | | $1,0000 |
| **Residuo** | | **$0,2543** |

Il preventivo era $0,516; l'effettivo è $0,746 (+45%) perché il costo medio
x86 è risultato $0,00356/chiamata invece dei $0,002 stimati e due chiamate
hanno avuto un errore di rete con costo 0. La spesa resta sotto il budget
aggiuntivo di $1,00 (spesa totale di sessione: $0,2981 già rendicontati +
$0,7457 = $1,0438). Nessuna ulteriore chiamata è stata effettuata dopo il
consuntivo.

