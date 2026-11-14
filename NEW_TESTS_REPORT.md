# Nuovi test: assembly wrapping, LLM morphing e LLM data classifier

Esito dei test lanciati il 2026-11-13 sul motore Zone in `C:\Users\ubu\Desktop\Zone`. Le esecuzioni usano `ploader.exe` / `ploader86.exe` (listener TCP 1234 per reverse/bind, finestra `#32770` per MessageBox).

## 1. Assembly wrapping (`-wrap`, x64)

Metodo: i 13 payload x64 a basso working rate, 10 run indipendenti per configurazione, due configurazioni. Il motore è stato congelato in `tmp/wrap_snapshot` per non dipendere dalle modifiche concorrenti.

| Configurazione | Build riusciti | Test eseguiti | Working rate |
|---|---:|---:|---:|
| `-xd -wrap` | 100/130 | 100/130 | 76.9% |
| `-xd -wrap -eq -nop -bcf -ibp` | 100/130 | 98/130 | 75.4% |

Complessivo: **198/260 = 76.2%** sui tentativi; sui soli binari costruiti **198/200 = 99.0%**.

| Payload | Build wrap | Wrap OK | Build full | Full OK |
|---|---:|---:|---:|---:|
| `windows_x64_custom_reverse_https` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_custom_reverse_winhttp` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_custom_reverse_winhttps` | 0/10 | 0/0 | 0/10 | 0/0 |
| `windows_x64_meterpreter_reverse_http` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_meterpreter_reverse_https` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_meterpreter_reverse_winhttp` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_vncinject_reverse_http` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_vncinject_reverse_winhttp` | 10/10 | 10/10 | 10/10 | 9/10 |
| `windows_x64_vncinject_reverse_winhttps` | 0/10 | 0/0 | 0/10 | 0/0 |
| `windows_x64_meterpreter_reverse_winhttps` | 0/10 | 0/0 | 0/10 | 0/0 |
| `windows_x64_vncinject_reverse_https` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_messagebox` | 10/10 | 10/10 | 10/10 | 10/10 |
| `windows_x64_custom_reverse_http` | 10/10 | 10/10 | 10/10 | 9/10 |

I 60 build falliti sono i tre payload `*_winhttps` (10 semi x 2 configurazioni): `-xd` non sposta un blocco inline a `0x169`, quindi `-wrap` non può ricoprire tutto lo stream. È un limite dell'estrazione dati, non del wrapper.

Tre output `-wrap` sono byte-identici tra run diverse (97/100 SHA-256 unici); il generatore assegnava il seed dalla stessa variabile d'ambiente condivisa tra thread, quindi alcune run hanno riusato lo stesso seed. Non cambia il working rate, ma riduce di poco la diversità del campione inviato a VirusTotal.

Nota tecnica: durante i test è emerso un bug reale in `asm_wrap.py`. Le istruzioni con `data_fixup` (getpc `call` riscritta in `jmp` verso lo stub nel blob) venivano ricollocate e verificate come se fossero ancora `call`, quindi il build falliva con `expected call, got jmp`. La correzione tratta queste istruzioni come opache (nessuna relocation, verifica del mnemonico saltata); senza la fix `custom_reverse_https` e `meterpreter_reverse_http` non si costruivano affatto.

MessageBox x64, 7 combinazioni x 5 semi, esecuzione reale:

| Combinazione | Dialoghi | Dimensione media |
|---|---:|---:|
| `-xd -wrap` | 5/5 | 1037 B |
| `-xd -wrap -eq` | 5/5 | 1047 B |
| `-xd -wrap -nop` | 5/5 | 1649 B |
| `-xd -wrap -bcf` | 5/5 | 3869 B |
| `-xd -wrap -eq -nop -bcf` | 5/5 | 5917 B |
| `-xd -wrap -ibp` | 5/5 | 1316 B |
| `-xd -wrap -eq -nop -bcf -ibp` | 5/5 | 6970 B |

## 2. LLM morphing (DeepSeek, una tecnica per run)

Payload: `windows_x64_messagebox` (313 B). 4 tecniche x 2 configurazioni di shot x 3 mutazioni = 24 run, ognuna verificata eseguendo il payload e attendendo il dialogo.

| Tecnica / shot | Accettati | Working | Tentativi medi | Similarità | Costo | Mutanti unici |
|---|---:|---:|---:|---:|---:|---:|
| `bcf` 0-shot | 3/3 | 3/3 | 1.3 | 0.884 | $0.097 | 3/3 |
| `bcf` 2-shot | 3/3 | 3/3 | 1.0 | 0.866 | $0.058 | 3/3 |
| `eq` 0-shot | 3/3 | 3/3 | 1.3 | 0.916 | $0.061 | 2/3 |
| `eq` 2-shot | 3/3 | 3/3 | 1.0 | 0.928 | $0.051 | 2/3 |
| `ibp` 0-shot | 3/3 | 3/3 | 1.3 | 0.711 | $0.071 | 2/3 |
| `ibp` 2-shot | 3/3 | 3/3 | 1.0 | 0.848 | $0.061 | 3/3 |
| `nop` 0-shot | 3/3 | 3/3 | 1.0 | 1.000 | $0.054 | 3/3 |
| `nop` 2-shot | 3/3 | 3/3 | 1.0 | 1.000 | $0.054 | 3/3 |

Costo API del blocco morphing: **$0.585** (24 run finali $0.506 + $0.080 della cella `ibp` 0-shot fallita al primo giro e poi ripetuta con successo). Tutte le 24 mutazioni finali superano la verifica di esecuzione (24/24 dialoghi). Le risposte `eq` e `ibp` sono spesso byte-identiche tra semi diversi: la diversità effettiva è inferiore al numero di run.

## 3. LLM data classifier (`--llm-data`)

Confronto con l'estrazione simbolica `-xd`. Per ogni caso 3 run; l'esecuzione è verificata con il dialogo (MessageBox) o il listener (reverse).

| Caso | Classificazioni OK | Working | Sezioni medie | Byte dati | Tentativi medi | Costo |
|---|---:|---:|---:|---:|---:|---:|
| x64 messagebox | 3/3 | 3/3 | 3.0 | 39 | 1.0 | $0.004 |
| x64 messagebox + -eq | 3/3 | 3/3 | 3.0 | 39 | 2.0 | $0.035 |
| x86 messagebox | 3/3 | 3/3 | 3.0 | 54 | 1.0 | $0.007 |
| x64 reverse_http | 3/3 | 3/3 | 3.7 | 262 | 1.3 | $0.041 |
| x86 reverse_http | 3/3 | 3/3 | 3.0 | 123 | 1.0 | $0.018 |

Su tutti e quattro i payload di confronto l'output del classifier LLM è **byte-identico** a quello di `-xd` simbolico (stesso SHA-256): x64/x86 MessageBox, x64/x86 `custom_reverse_http`. Il classificatore ha quindi riprodotto esattamente le sezioni estratte a mano dal motore simbolico, a costi trascurabili.

Costo API del blocco data: $0.105; mutanti unici: 5/15 (l'estrazione è deterministica, i 3 run per caso coincidono).

## 4. VirusTotal

Manifest in `vt_manifest.csv` / `vt_manifest.json`: **239 file, 220 SHA-256 unici** (i duplicati sono estrazioni deterministiche e alcune risposte LLM identiche).

| Gruppo | File | Working locale |
|---|---:|---:|
| `-wrap` | 100 | 100 |
| `-wrap` full | 100 | 98 |
| LLM morphing | 24 | 24 |
| LLM data | 15 | 15 |

| Tecnica | File | Analizzati | Rilevati (>0) | Detection rate | Malicious medi | Max |
|---|---:|---:|---:|---:|---:|---:|
| `lldata` | 4 | 4 | 4 | 100.0% | 17.50 | 20 |
| `llm_bcf_s0` | 3 | 3 | 1 | 33.3% | 1.00 | 3 |
| `llm_bcf_s2` | 3 | 3 | 3 | 100.0% | 5.00 | 5 |
| `llm_eq_s0` | 2 | 2 | 0 | 0.0% | 0.00 | 0 |
| `llm_eq_s2` | 1 | 1 | 0 | 0.0% | 0.00 | 0 |
| `llm_ibp_s0` | 2 | 2 | 1 | 50.0% | 2.50 | 5 |
| `llm_ibp_s2` | 2 | 2 | 2 | 100.0% | 1.00 | 1 |
| `llm_nop_s0` | 3 | 3 | 0 | 0.0% | 0.00 | 0 |
| `llm_nop_s2` | 3 | 3 | 1 | 33.3% | 1.67 | 5 |
| `wrap` | 97 | 97 | 0 | 0.0% | 0.00 | 0 |
| `wrap_full` | 100 | 100 | 0 | 0.0% | 0.00 | 0 |

Totale: **12/220 rilevati (5.5%)** su 220 file unici inviati.

Nota: la colonna File conta gli SHA-256 unici. Le estrazioni `--llm-data` sono deterministiche e alcune risposte LLM `eq`/`ibp` sono byte-identiche, quindi le celle con meno di 3 file sono duplicati deduplicati. `lldata` è la sola estrazione dati (codice intatto): viene rilevata come gli originali, perché non offusca il codice; non è una tecnica di evasione ma un preprocessing.

Lettura dei risultati: `-wrap` e `-wrap` combinato non vengono rilevati da nessun motore (0/197, massimo 0), mentre gli stessi payload originali inviati oggi sono 13/13 rilevati con 20-29 motori. Le tecniche LLM sono funzionalmente corrette ma la copertura anti-VT è irregolare e dipende dalla tecnica e dagli shot: `eq` 0/3, `bcf` 4/6, `ibp` 3/4, `nop` 1/6 (file unici).

Confronto omogeneo con gli originali, inviati oggi con la stessa key: **13/13 rilevati (100.0%)**, malicious medi 26.6/75. Gli stessi payload senza wrapping sono quindi ancora ampiamente rilevati, mentre le mutazioni `-wrap` no.


## Conclusioni

1. **Assembly wrapping**: è la tecnica più solida del lotto. Il 77% dei tentativi produce un binario (200/260) e su questi il working rate è del 99% (198/200); i 197 file unici "-wrap" non sono rilevati da nessun motore VT (0/197), contro 13/13 originali rilevati oggi. Il limite è a monte: i tre `*_winhttps` non sono costruibili perché `-xd` lascia un blocco dati inline.
2. **LLM morphing**: 24/24 mutazioni accettate e funzionanti, costo ~$0.59. La qualità strutturale è buona (similarità 0.71-1.00), ma la diversità è limitata dalle risposte identiche e la copertura VT è irregolare (12/220 globali, quasi tutti `bcf`/`ibp`).
3. **LLM data classifier**: 15/15 run funzionanti e output byte-identico a `-xd` sui quattro payload di confronto; costo ~$0.10. È un'alternativa valida all'estrazione simbolica, ma non aggiunge evasione: il codice resta quello originale e VT lo rileva (16-20/75).

## File prodotti

- `mutations_wrap/x64/` — 200 mutanti `-wrap`
- `mutations_llm/x64/` — 24 mutanti LLM
- `mutations_llm_data/` — 15 mutanti del classifier LLM
- `tmp/wrap_report.csv`, `tmp/llm_morph_report.csv`, `tmp/llm_data_report.csv` — esiti grezzi
- `vt_manifest.csv` / `vt_manifest.json` — manifest per VirusTotal
