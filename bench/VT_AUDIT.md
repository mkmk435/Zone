# Audit dei report VirusTotal esistenti

Nessuna nuova sottomissione: solo verifica degli artefatti già presenti. Un record è **verificabile** solo se il file è ancora su disco e il suo SHA-256 è stato ricalcolato.

| Dataset | Record | Verificabili | Non verificabili | Hash unici | Zero rilevamenti | Rilevati |
|---|---:|---:|---:|---:|---:|---:|
| results.json (2025) | 15021 | 8049 | 6972 | 8037 | 6026 | 2023 |
| results_original.json (2025) | 102 | 102 | 0 | 90 | 0 | 102 |
| results_sgn.json (2025) | 102 | 102 | 0 | 90 | 38 | 64 |
| manifest 2026 | 220 | 220 | 0 | 220 | 208 | 12 |
| originali 2026 | 13 | 13 | 0 | 13 | 0 | 13 |

## Controlli di integrità

- Manifest 2026: 239 righe, 220 SHA-256 unici, 19 duplicati nel manifest.
- Hash dei file 2026 ricontrollati: 0 mismatch, 0 file mancanti, 0 record con stats incoerenti.
- Scansioni 2026: 220 completate, 0 incomplete, 0 senza risultato.
- Date 2026: 2026-11-13T12:13:41 .. 2026-11-13T12:50:20.
- Esiti motori 2026 su 16500 risposte: 3259 `type-unsupported` (19.8%), 283 timeout, 73 failure. Il numero di motori che hanno davvero analizzato il formato è quindi inferiore al totale (75..75).
- Ogni file 2026 ha in media 14.8 motori che non supportano il formato: i confronti '0/N' vanno letti su N meno questi.
- 2025 `results.json`: 8049 record verificabili e 6972 non verificabili (artefatto assente dal disco: il risultato non è ricontrollabile). 1 record duplicati, 0 record numerici invalidi, 0 date invalide.
- 2025 originali: 102 record ma solo 90 hash distinti: i campioni non sono indipendenti.
- 2025 date: 2025-04-30T05:50:48 .. 2025-09-17T11:37:00.

## Zero rilevamenti non significa invisibilità

Un record con `malicious = 0` è una scansione completata in cui nessun motore ha classificato il file come malicious in quel momento; non dimostra che il file sia invisibile, né copre esecuzione dinamica, sandbox o motori che non supportano il formato (`type-unsupported`). I conteggi sopra separano zero rilevamenti, analisi incompleta e risultato mancante. Inoltre output identici condividono lo stesso hash e non sono campioni indipendenti.
