# Working rate unificato: payload vecchi vs rigenerati

Generato: 2026-11-09 00:44

Soglia "working rate basso": **< 50%** sul test originale (`test_report.txt`). Payload selezionati: **49** (x64 13, x86 36).

## Metodo

- **Vecchi**: `test_report.txt`, 15 tecniche di morphing x 10 run per payload, nessuna flag `-xd`/`-ebi`.
- **Nuovi**: stessi 15 setup di morphing rigenerati con `-xd -ebi` (fallback `-xd`), piu due configurazioni di sola estrazione: `-xd` e `-xd -ebi`.
- **Test nuovi**: `ploader.exe` (x64) / `ploader86.exe` (x86); reverse con listener 127.0.0.1:1234, bind con connessione a 127.0.0.1:1234, messagebox con `EnumWindows` + `WM_CLOSE`.
- **Baseline**: ogni payload originale e stato eseguito 3 volte con lo stesso harness; tutti i 49 originali hanno funzionato 3/3, quindi le differenze misurano l'obfuscator, non l'harness.
- `new_morph` = 15 tecniche storiche; `new_xd` = solo `-xd` / `-xd -ebi`; `new_all` = tutte le 17 configurazioni.

## 1. Payload a basso working rate (vecchio → nuovo)

| # | Arch | Payload | Vecchio | Baseline orig. | Nuovo `-xd` | Nuovo morph | Δ morph |
|---:|:--:|---|---:|---:|---:|---:|---:|
| 1 | x64 | `windows_x64_custom_reverse_https` | 0.0% (0/149) | 100.0% (3/3) | 100.0% (20/20) | 94.7% (142/150) | +94.7 pp |
| 2 | x64 | `windows_x64_custom_reverse_winhttp` | 0.0% (0/149) | 100.0% (3/3) | 100.0% (20/20) | 89.3% (134/150) | +89.3 pp |
| 3 | x64 | `windows_x64_custom_reverse_winhttps` | 0.0% (0/150) | 100.0% (3/3) | 100.0% (20/20) | 6.7% (10/150) | +6.7 pp |
| 4 | x64 | `windows_x64_meterpreter_reverse_http` | 0.0% (0/149) | 100.0% (3/3) | 100.0% (20/20) | 96.7% (145/150) | +96.7 pp |
| 5 | x64 | `windows_x64_meterpreter_reverse_https` | 0.0% (0/149) | 100.0% (3/3) | 100.0% (20/20) | 91.3% (137/150) | +91.3 pp |
| 6 | x64 | `windows_x64_meterpreter_reverse_winhttp` | 0.0% (0/149) | 100.0% (3/3) | 100.0% (20/20) | 95.3% (143/150) | +95.3 pp |
| 7 | x64 | `windows_x64_vncinject_reverse_http` | 0.0% (0/150) | 100.0% (3/3) | 100.0% (20/20) | 96.7% (145/150) | +96.7 pp |
| 8 | x64 | `windows_x64_vncinject_reverse_winhttp` | 0.0% (0/150) | 100.0% (3/3) | 100.0% (20/20) | 94.0% (141/150) | +94.0 pp |
| 9 | x64 | `windows_x64_vncinject_reverse_winhttps` | 0.0% (0/150) | 100.0% (3/3) | 100.0% (20/20) | 6.7% (10/150) | +6.7 pp |
| 10 | x86 | `windows_custom_reverse_http` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 11 | x86 | `windows_custom_reverse_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 12 | x86 | `windows_messagebox` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 13 | x86 | `windows_meterpreter_bind_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 14 | x86 | `windows_patchupmeterpreter_bind_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 15 | x86 | `windows_shell_bind_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 16 | x86 | `windows_shell_reverse_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 17 | x86 | `windows_vncinject_bind_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 18 | x86 | `windows_vncinject_reverse_http` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 19 | x86 | `windows_vncinject_reverse_nonx_tcp` | 0.0% (0/150) | 100.0% (3/3) | — | — | — |
| 20 | x86 | `windows_custom_bind_nonx_tcp` | 0.7% (1/150) | 100.0% (3/3) | — | 0.0% (0/5) | -0.7 pp |
| 21 | x86 | `windows_meterpreter_reverse_nonx_tcp` | 0.7% (1/150) | 100.0% (3/3) | — | — | — |
| 22 | x86 | `windows_patchupmeterpreter_reverse_nonx_tcp` | 0.7% (1/150) | 100.0% (3/3) | — | — | — |
| 23 | x86 | `windows_vncinject_reverse_winhttp` | 0.7% (1/150) | 100.0% (3/3) | — | — | — |
| 24 | x64 | `windows_x64_meterpreter_reverse_winhttps` | 1.3% (2/150) | 100.0% (3/3) | 100.0% (20/20) | 82.7% (124/150) | +81.3 pp |
| 25 | x86 | `windows_meterpreter_reverse_winhttps` | 1.3% (2/150) | 100.0% (3/3) | — | — | — |
| 26 | x64 | `windows_x64_vncinject_reverse_https` | 1.3% (2/149) | 100.0% (3/3) | 100.0% (20/20) | 93.3% (140/150) | +92.0 pp |
| 27 | x64 | `windows_x64_messagebox` | 2.7% (4/150) | 100.0% (3/3) | 100.0% (20/20) | 100.0% (150/150) | +97.3 pp |
| 28 | x64 | `windows_x64_custom_reverse_http` | 10.2% (15/147) | 100.0% (3/3) | 100.0% (20/20) | 95.3% (143/150) | +85.1 pp |
| 29 | x86 | `windows_meterpreter_reverse_winhttp` | 11.3% (17/150) | 100.0% (3/3) | — | — | — |
| 30 | x86 | `windows_vncinject_reverse_tcp_allports` | 16.3% (20/123) | 100.0% (3/3) | — | — | — |
| 31 | x86 | `windows_custom_reverse_winhttps` | 16.7% (25/150) | 100.0% (3/3) | — | — | — |
| 32 | x86 | `windows_shell_reverse_tcp` | 18.2% (22/121) | 100.0% (3/3) | — | — | — |
| 33 | x86 | `windows_shell_bind_tcp` | 20.0% (25/125) | 100.0% (3/3) | — | — | — |
| 34 | x86 | `windows_custom_reverse_winhttp` | 21.3% (32/150) | 100.0% (3/3) | — | — | — |
| 35 | x86 | `windows_shell_reverse_tcp_allports` | 21.5% (26/121) | 100.0% (3/3) | — | — | — |
| 36 | x86 | `windows_custom_reverse_https` | 22.0% (33/150) | 100.0% (3/3) | — | — | — |
| 37 | x86 | `windows_patchupmeterpreter_reverse_tcp_allports` | 22.9% (27/118) | 100.0% (3/3) | — | — | — |
| 38 | x86 | `windows_custom_reverse_tcp_dns` | 23.3% (35/150) | 100.0% (3/3) | — | — | — |
| 39 | x86 | `windows_custom_reverse_tcp_rc4_dns` | 24.7% (37/150) | 100.0% (3/3) | — | — | — |
| 40 | x86 | `windows_custom_reverse_tcp_allports` | 24.8% (29/117) | 100.0% (3/3) | — | — | — |
| 41 | x86 | `windows_meterpreter_reverse_tcp_allports` | 25.0% (30/120) | 100.0% (3/3) | — | — | — |
| 42 | x86 | `windows_meterpreter_reverse_tcp_rc4_dns` | 28.0% (42/150) | 100.0% (3/3) | — | — | — |
| 43 | x86 | `windows_meterpreter_reverse_tcp_dns` | 30.7% (46/150) | 100.0% (3/3) | — | — | — |
| 44 | x86 | `windows_patchupmeterpreter_reverse_tcp_rc4_dns` | 32.0% (48/150) | 100.0% (3/3) | — | — | — |
| 45 | x86 | `windows_vncinject_reverse_tcp_dns` | 32.7% (49/150) | 100.0% (3/3) | — | — | — |
| 46 | x86 | `windows_shell_reverse_tcp_rc4_dns` | 36.0% (54/150) | 100.0% (3/3) | — | — | — |
| 47 | x86 | `windows_shell_reverse_tcp_dns` | 36.7% (55/150) | 100.0% (3/3) | — | — | — |
| 48 | x86 | `windows_patchupmeterpreter_reverse_tcp_dns` | 37.3% (56/150) | 100.0% (3/3) | — | — | — |
| 49 | x86 | `windows_vncinject_reverse_tcp_rc4_dns` | 38.7% (58/150) | 100.0% (3/3) | — | — | — |

## 2. Riepilogo

| Set | Payload | Vecchio | Nuovo morph | Nuovo `-xd` | Nuovo totale |
|---|---:|---:|---:|---:|---:|
| x64 | 13 | 1.2% (23/1941) | 80.2% (1564/1950) | 100.0% (260/260) | 82.5% (1824/2210) |
| x86 | 36 | 14.9% (772/5195) | 0.0% (0/5) | — | 0.0% (0/5) |
| **Totale** | 49 | 11.1% (795/7136) | 80.0% (1564/1955) | 100.0% (260/260) | 82.3% (1824/2215) |

Nota: il tasso "Vecchio" del set basso e calcolato sulle 15 tecniche storiche; il tasso "Nuovo totale" include anche le due configurazioni di sola estrazione.

## 3. Working rate per tecnica (solo payload a basso rate)

### x64

| Tecnica | Vecchio | Nuovo | Δ |
|---|---:|---:|---:|
| `nop` | 0.0% (0/130) | 77.7% (101/130) | +77.7 pp |
| `eq` | 0.0% (0/130) | 100.0% (130/130) | +100.0 pp |
| `pii` | 0.0% (0/130) | 84.6% (110/130) | +84.6 pp |
| `bcf` | 0.0% (0/130) | 83.8% (109/130) | +83.8 pp |
| `ibp` | 0.0% (0/130) | 83.1% (108/130) | +83.1 pp |
| `eq_nop_pii` | 0.8% (1/130) | 65.4% (85/130) | +64.6 pp |
| `eq_nop_bcf` | 0.0% (0/130) | 83.1% (108/130) | +83.1 pp |
| `eq_nop_ibp` | 0.0% (0/130) | 74.6% (97/130) | +74.6 pp |
| `nop_eq` | 6.2% (8/128) | 78.5% (102/130) | +72.2 pp |
| `nop_pii` | 0.8% (1/128) | 66.9% (87/130) | +66.1 pp |
| `nop_bcf` | 0.0% (0/129) | 83.1% (108/130) | +83.1 pp |
| `nop_ibp` | 1.6% (2/129) | 70.8% (92/130) | +69.2 pp |
| `eq_pii` | 0.0% (0/130) | 84.6% (110/130) | +84.6 pp |
| `eq_bcf` | 7.0% (9/128) | 83.1% (108/130) | +76.0 pp |
| `eq_ibp` | 1.6% (2/129) | 83.8% (109/130) | +82.3 pp |
| `xd` | — | 100.0% (130/130) | — |
| `xd_ebi` | — | 100.0% (130/130) | — |

### x86

| Tecnica | Vecchio | Nuovo | Δ |
|---|---:|---:|---:|
| `nop` | 20.8% (75/360) | — | — |
| `eq` | 60.0% (216/360) | — | — |
| `pii` | 0.0% (0/299) | — | — |
| `bcf` | 18.3% (66/360) | 0.0% (0/5) | -18.3 pp |
| `ibp` | 14.2% (51/360) | — | — |
| `eq_nop_pii` | 0.0% (0/339) | — | — |
| `eq_nop_bcf` | 11.9% (43/360) | — | — |
| `eq_nop_ibp` | 7.5% (27/360) | — | — |
| `nop_eq` | 20.3% (73/360) | — | — |
| `nop_pii` | 0.0% (0/306) | — | — |
| `nop_bcf` | 17.2% (62/360) | — | — |
| `nop_ibp` | 9.7% (35/360) | — | — |
| `eq_pii` | 0.0% (0/291) | — | — |
| `eq_bcf` | 22.2% (80/360) | — | — |
| `eq_ibp` | 12.2% (44/360) | — | — |
| `xd` | — | — | — |
| `xd_ebi` | — | — | — |

## 4. Note e limiti

- **messagebox**: il vecchio report trattava il payload come "other" e aspettava l'uscita del processo; il dialog bloccava il test. I nuovi dati usano il rilevamento della finestra, quindi il confronto vecchio/nuovo per questi due payload non e omogeneo.
- **x64 `*_winhttps`**: resta il caso noto: `-eq` funziona, le altre tecniche no; la fix getpc non lo recupera.
- **x86 HTTP/winhttp**: la sola estrazione `-xd`/`-xd -ebi` funziona; `-nop` (e le combinazioni che lo includono) rompe il payload, quindi il tasso delle 15 tecniche storiche resta basso anche dopo la rigenerazione.
- I fallimenti di **generazione** sono contati a parte (`generation_fail` nel CSV/XLSX); il denominatore dei tassi nuovi e il numero di test effettivamente eseguiti.

## 5. File

- `tmp\preview_unified.csv` — dati completi per payload (tutti i 102 payload originali).
- `working_rate_unified.xlsx` — riepilogo, per payload, per tecnica, matrice, dettaglio.
- `new_test_report.csv` — test grezzi dei nuovi payload.
- `mutations_new_xd_ebi/` — payload rigenerati (x64/x86).
- `tmp/original_baseline.csv` — baseline 3 run/payload degli originali.

