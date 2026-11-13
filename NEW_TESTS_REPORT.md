# Nuovi test: assembly wrapping, LLM morphing e LLM data classifier

Esito dei test lanciati il 2026-11-13 sul motore Zone in `C:\Users\ubu\Desktop\Zone`. Le esecuzioni usano `ploader.exe` / `ploader86.exe` (listener TCP 1234 per reverse/bind, finestra `#32770` per MessageBox).

## 1. Assembly wrapping (`-wrap`, x64)

Metodo: i 13 payload x64 a basso working rate, 10 semi indipendenti per configurazione, due configurazioni. Il motore è stato congelato in `tmp/wrap_snapshot` per non dipendere dalle modifiche concorrenti.

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

Manifest pronto in `vt_manifest.csv` / `vt_manifest.json`: **239 file, 220 SHA-256 unici** (i duplicati sono estrazioni deterministiche e alcune risposte LLM identiche).

| Gruppo | File | Working locale |
|---|---:|---:|
| `-wrap` | 100 | 100 |
| `-wrap` full | 100 | 98 |
| LLM morphing | 24 | 24 |
| LLM data | 15 | 15 |

Invio **non eseguito**: manca `api_keys.txt`. Il submitter è pronto in `tmp/vt_submit.py`; appena disponibili una o più key parte in background con deduplica per SHA-256 e ripresa.

## File prodotti

- `mutations_wrap/x64/` — 200 mutanti `-wrap`
- `mutations_llm/x64/` — 24 mutanti LLM
- `mutations_llm_data/` — 15 mutanti del classifier LLM
- `tmp/wrap_report.csv`, `tmp/llm_morph_report.csv`, `tmp/llm_data_report.csv` — esiti grezzi
- `vt_manifest.csv` / `vt_manifest.json` — manifest per VirusTotal
