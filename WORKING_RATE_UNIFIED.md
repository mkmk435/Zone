# Working rate unificato — tutti i dataset vecchi + nuovo

Generato: 2026-11-10 11:23

Soglia low: **< 50%** sul vecchio originale. Payload selezionati: **49** (x64 13, x86 36).

## Dataset inclusi

| Dataset | File | Copertura |
|---|---|---|
| `old_original` | `test_report.txt` | tutti i 102 payload, 15 tecniche, nessuna flag |
| `old_xd_ebi` | `test_report_x64_low_xd_ebi.txt` | 13 x64 low, `-xd -ebi` (prima versione) |
| `old_xd_ebi_5001` | `test_report_x64_low_xd_ebi_5001.txt` | 13 x64 low, `-xd -ebi`, capstone 5.0.0.post1 |
| `old_xd_ebi_getpc` | `test_report_x64_low_getpc.txt` | 13 x64 low, `-xd -ebi` + fix getpc |
| `new_xd_ebi` | `new_test_report_5run.csv` | 49 low, 15 morph + `xd` + `xd_ebi` |
| `baseline_original` | `tmp/original_baseline.csv` | 49 originali, 3 run ciascuno |

## Riepilogo per dataset

| Dataset / ambito | Payload | OK/test | Working rate |
|---|---:|---:|---:|
| Vecchio originale — tutti i payload | 102 | 7395/15020 | 49.2% |
| Vecchio originale — 49 low | 49 | 795/7136 | 11.1% |
| Vecchio -xd -ebi (prima versione) — 13 x64 low | 13 | 706/1950 | 36.2% |
| Vecchio -xd -ebi (pre-getpc) — 13 x64 low | 13 | 716/1950 | 36.7% |
| Vecchio -xd -ebi + getpc — 13 x64 low | 13 | 1458/1950 | 74.8% |
| Nuovo morph 15 tecniche — 13 x64 low | 13 | 1564/1950 | 80.2% |
| Nuovo morph 15 tecniche — 36 x86 low | 36 | 699/2700 | 25.9% |
| Nuovo morph 15 tecniche — 49 low | 49 | 2263/4650 | 48.7% |
| Nuovo solo -xd/-xd -ebi — 13 x64 low | 13 | 260/260 | 100.0% |
| Nuovo solo -xd/-xd -ebi — 36 x86 low | 36 | 340/360 | 94.4% |
| Nuovo solo -xd/-xd -ebi — 49 low | 49 | 600/620 | 96.8% |
| Nuovo totale (17 config) — 13 x64 low | 13 | 1824/2210 | 82.5% |
| Nuovo totale (17 config) — 36 x86 low | 36 | 1039/3060 | 34.0% |
| Nuovo totale (17 config) — 49 low | 49 | 2863/5270 | 54.3% |
| Baseline originali — 49 low | 49 | 147/147 | 100.0% |

## Payload a basso working rate: vecchi set → nuovo

| # | Arch | Payload | Old orig. | Old getpc | Nuovo `-xd` | Nuovo morph | Δ vs getpc |
|---:|:--:|---|---:|---:|---:|---:|---:|
| 1 | x64 | `windows_x64_custom_reverse_https` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 94.7% (142/150) | +12.0 pp |
| 2 | x64 | `windows_x64_custom_reverse_winhttp` | 0.0% (0/149) | 93.3% (140/150) | 100.0% (20/20) | 89.3% (134/150) | +6.7 pp |
| 3 | x64 | `windows_x64_custom_reverse_winhttps` | 0.0% (0/150) | 6.7% (10/150) | 100.0% (20/20) | 6.7% (10/150) | +93.3 pp |
| 4 | x64 | `windows_x64_meterpreter_reverse_http` | 0.0% (0/149) | 88.7% (133/150) | 100.0% (20/20) | 96.7% (145/150) | +11.3 pp |
| 5 | x64 | `windows_x64_meterpreter_reverse_https` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 91.3% (137/150) | +12.0 pp |
| 6 | x64 | `windows_x64_meterpreter_reverse_winhttp` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 95.3% (143/150) | +12.0 pp |
| 7 | x64 | `windows_x64_vncinject_reverse_http` | 0.0% (0/150) | 89.3% (134/150) | 100.0% (20/20) | 96.7% (145/150) | +10.7 pp |
| 8 | x64 | `windows_x64_vncinject_reverse_winhttp` | 0.0% (0/150) | 92.7% (139/150) | 100.0% (20/20) | 94.0% (141/150) | +7.3 pp |
| 9 | x64 | `windows_x64_vncinject_reverse_winhttps` | 0.0% (0/150) | 6.7% (10/150) | 100.0% (20/20) | 6.7% (10/150) | +93.3 pp |
| 10 | x86 | `windows_custom_reverse_http` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 11 | x86 | `windows_custom_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 12 | x86 | `windows_messagebox` | 0.0% (0/150) | — | 100.0% (10/10) | 90.7% (68/75) | — |
| 13 | x86 | `windows_meterpreter_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 14 | x86 | `windows_patchupmeterpreter_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 15 | x86 | `windows_shell_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 16 | x86 | `windows_shell_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 17 | x86 | `windows_vncinject_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 18 | x86 | `windows_vncinject_reverse_http` | 0.0% (0/150) | — | 100.0% (10/10) | 2.7% (2/75) | — |
| 19 | x86 | `windows_vncinject_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 20 | x86 | `windows_custom_bind_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 21 | x86 | `windows_meterpreter_reverse_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 22 | x86 | `windows_patchupmeterpreter_reverse_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | — |
| 23 | x86 | `windows_vncinject_reverse_winhttp` | 0.7% (1/150) | — | 100.0% (10/10) | 1.3% (1/75) | — |
| 24 | x64 | `windows_x64_meterpreter_reverse_winhttps` | 1.3% (2/150) | 76.7% (115/150) | 100.0% (20/20) | 82.7% (124/150) | +23.3 pp |
| 25 | x86 | `windows_meterpreter_reverse_winhttps` | 1.3% (2/150) | — | 100.0% (10/10) | 1.3% (1/75) | — |
| 26 | x64 | `windows_x64_vncinject_reverse_https` | 1.3% (2/149) | 94.7% (142/150) | 100.0% (20/20) | 93.3% (140/150) | +5.3 pp |
| 27 | x64 | `windows_x64_messagebox` | 2.7% (4/150) | 72.0% (108/150) | 100.0% (20/20) | 100.0% (150/150) | +28.0 pp |
| 28 | x64 | `windows_x64_custom_reverse_http` | 10.2% (15/147) | 87.3% (131/150) | 100.0% (20/20) | 95.3% (143/150) | +12.7 pp |
| 29 | x86 | `windows_meterpreter_reverse_winhttp` | 11.3% (17/150) | — | 0.0% (0/10) | 0.0% (0/75) | — |
| 30 | x86 | `windows_vncinject_reverse_tcp_allports` | 16.3% (20/123) | — | 100.0% (10/10) | 74.7% (56/75) | — |
| 31 | x86 | `windows_custom_reverse_winhttps` | 16.7% (25/150) | — | 100.0% (10/10) | 40.0% (30/75) | — |
| 32 | x86 | `windows_shell_reverse_tcp` | 18.2% (22/121) | — | 100.0% (10/10) | 74.7% (56/75) | — |
| 33 | x86 | `windows_shell_bind_tcp` | 20.0% (25/125) | — | 100.0% (10/10) | 73.3% (55/75) | — |
| 34 | x86 | `windows_custom_reverse_winhttp` | 21.3% (32/150) | — | 0.0% (0/10) | 0.0% (0/75) | — |
| 35 | x86 | `windows_shell_reverse_tcp_allports` | 21.5% (26/121) | — | 100.0% (10/10) | 76.0% (57/75) | — |
| 36 | x86 | `windows_custom_reverse_https` | 22.0% (33/150) | — | 100.0% (10/10) | 29.3% (22/75) | — |
| 37 | x86 | `windows_patchupmeterpreter_reverse_tcp_allports` | 22.9% (27/118) | — | 100.0% (10/10) | 77.3% (58/75) | — |
| 38 | x86 | `windows_custom_reverse_tcp_dns` | 23.3% (35/150) | — | 100.0% (10/10) | 17.3% (13/75) | — |
| 39 | x86 | `windows_custom_reverse_tcp_rc4_dns` | 24.7% (37/150) | — | 100.0% (10/10) | 28.0% (21/75) | — |
| 40 | x86 | `windows_custom_reverse_tcp_allports` | 24.8% (29/117) | — | 100.0% (10/10) | 78.7% (59/75) | — |
| 41 | x86 | `windows_meterpreter_reverse_tcp_allports` | 25.0% (30/120) | — | 100.0% (10/10) | 77.3% (58/75) | — |
| 42 | x86 | `windows_meterpreter_reverse_tcp_rc4_dns` | 28.0% (42/150) | — | 100.0% (10/10) | 24.0% (18/75) | — |
| 43 | x86 | `windows_meterpreter_reverse_tcp_dns` | 30.7% (46/150) | — | 100.0% (10/10) | 25.3% (19/75) | — |
| 44 | x86 | `windows_patchupmeterpreter_reverse_tcp_rc4_dns` | 32.0% (48/150) | — | 100.0% (10/10) | 22.7% (17/75) | — |
| 45 | x86 | `windows_vncinject_reverse_tcp_dns` | 32.7% (49/150) | — | 100.0% (10/10) | 25.3% (19/75) | — |
| 46 | x86 | `windows_shell_reverse_tcp_rc4_dns` | 36.0% (54/150) | — | 100.0% (10/10) | 24.0% (18/75) | — |
| 47 | x86 | `windows_shell_reverse_tcp_dns` | 36.7% (55/150) | — | 100.0% (10/10) | 18.7% (14/75) | — |
| 48 | x86 | `windows_patchupmeterpreter_reverse_tcp_dns` | 37.3% (56/150) | — | 100.0% (10/10) | 21.3% (16/75) | — |
| 49 | x86 | `windows_vncinject_reverse_tcp_rc4_dns` | 38.7% (58/150) | — | 100.0% (10/10) | 28.0% (21/75) | — |

## x64 low: per tecnica, tutti i set vecchi + nuovo

| Tecnica | Old orig. | Old 5001 | Old getpc | Nuovo morph |
|---|---:|---:|---:|---:|
| `nop` | 0.0% (0/130) | 26.2% (34/130) | 77.7% (101/130) | 77.7% (101/130) |
| `eq` | 0.0% (0/130) | 93.1% (121/130) | 100.0% (130/130) | 100.0% (130/130) |
| `pii` | 0.0% (0/130) | 38.5% (50/130) | 84.6% (110/130) | 84.6% (110/130) |
| `bcf` | 0.0% (0/130) | 38.5% (50/130) | 80.8% (105/130) | 83.8% (109/130) |
| `ibp` | 0.0% (0/130) | 24.6% (32/130) | 64.6% (84/130) | 83.1% (108/130) |
| `eq_nop_pii` | 0.8% (1/130) | 36.9% (48/130) | 63.8% (83/130) | 65.4% (85/130) |
| `eq_nop_bcf` | 0.0% (0/130) | 37.7% (49/130) | 80.8% (105/130) | 83.1% (108/130) |
| `eq_nop_ibp` | 0.0% (0/130) | 26.9% (35/130) | 53.1% (69/130) | 74.6% (97/130) |
| `nop_eq` | 6.2% (8/128) | 27.7% (36/130) | 78.5% (102/130) | 78.5% (102/130) |
| `nop_pii` | 0.8% (1/128) | 38.5% (50/130) | 65.4% (85/130) | 66.9% (87/130) |
| `nop_bcf` | 0.0% (0/129) | 36.9% (48/130) | 83.1% (108/130) | 83.1% (108/130) |
| `nop_ibp` | 1.6% (2/129) | 26.9% (35/130) | 54.6% (71/130) | 70.8% (92/130) |
| `eq_pii` | 0.0% (0/130) | 38.5% (50/130) | 84.6% (110/130) | 84.6% (110/130) |
| `eq_bcf` | 7.0% (9/128) | 36.9% (48/130) | 84.6% (110/130) | 83.1% (108/130) |
| `eq_ibp` | 1.6% (2/129) | 23.1% (30/130) | 65.4% (85/130) | 83.8% (109/130) |
| `xd` | — | — | — | 100.0% (130/130) |
| `xd_ebi` | — | — | — | 100.0% (130/130) |

Nota: `xd` e `xd_ebi` non esistevano nei vecchi set; la colonna `Nuovo morph` per queste righe mostra le configurazioni di sola estrazione.

## x86 low: per tecnica, vecchio + nuovo

| Tecnica | Old orig. | Nuovo morph |
|---|---:|---:|
| `nop` | 20.8% (75/360) | 22.2% (40/180) |
| `eq` | 60.0% (216/360) | 57.8% (104/180) |
| `pii` | 0.0% (0/299) | 25.0% (45/180) |
| `bcf` | 18.3% (66/360) | 42.2% (76/180) |
| `ibp` | 14.2% (51/360) | 23.9% (43/180) |
| `eq_nop_pii` | 0.0% (0/339) | 5.0% (9/180) |
| `eq_nop_bcf` | 11.9% (43/360) | 31.1% (56/180) |
| `eq_nop_ibp` | 7.5% (27/360) | 11.1% (20/180) |
| `nop_eq` | 20.3% (73/360) | 22.2% (40/180) |
| `nop_pii` | 0.0% (0/306) | 5.0% (9/180) |
| `nop_bcf` | 17.2% (62/360) | 30.6% (55/180) |
| `nop_ibp` | 9.7% (35/360) | 17.2% (31/180) |
| `eq_pii` | 0.0% (0/291) | 25.0% (45/180) |
| `eq_bcf` | 22.2% (80/360) | 43.9% (79/180) |
| `eq_ibp` | 12.2% (44/360) | 26.1% (47/180) |
| `xd` | — | 94.4% (170/180) |
| `xd_ebi` | — | 94.4% (170/180) |

## Note

- **messagebox**: il vecchio report trattava il payload come "other" e aspettava l'uscita del processo; il dialog bloccava il test. I nuovi dati usano il rilevamento della finestra, quindi il confronto vecchio/nuovo per questi due payload non e omogeneo.
- **x64 `*_winhttps`**: old getpc 6.7%; il nuovo `-xd`/`-xd -ebi` da solo e 10/10. Il morphing e il limite, non l'estrazione.
- **x86 winhttp** (`custom`, `meterpreter`): regressione. La call getpc salta il primo blocco dati ma il consumer e dopo un secondo blocco; l'estrattore sposta il primo blocco senza riscrivere la call. Old getpc = —, nuovo `-xd` = 0/10.
- **x86 nonx**: `-xd` 10/10, morph 0/75: e il morphing a rompere, non l'estrazione.
- **x86**: 5 run per configurazione (sui 10 generati) per contenere il runtime; x64 10 run. I totali per payload/arch restano su centinaia di test.

## Appendice: tutti i 102 payload vecchi

| Arch | Payload | Old orig. | Old getpc | Nuovo `-xd` | Nuovo morph | Nuovo totale |
|:--:|---|---:|---:|---:|---:|---:|
| x64 | `windows_x64_custom_bind_tcp` | 82.8% (120/145) | — | — | — | — |
| x64 | `windows_x64_custom_bind_tcp_rc4` | 85.2% (127/149) | — | — | — | — |
| x64 | `windows_x64_custom_bind_tcp_uuid` | 84.6% (126/149) | — | — | — | — |
| x64 | `windows_x64_custom_reverse_http` | 10.2% (15/147) | 87.3% (131/150) | 100.0% (20/20) | 95.3% (143/150) | 95.9% (163/170) |
| x64 | `windows_x64_custom_reverse_https` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 94.7% (142/150) | 95.3% (162/170) |
| x64 | `windows_x64_custom_reverse_tcp` | 85.6% (125/146) | — | — | — | — |
| x64 | `windows_x64_custom_reverse_tcp_rc4` | 86.0% (129/150) | — | — | — | — |
| x64 | `windows_x64_custom_reverse_tcp_uuid` | 83.0% (122/147) | — | — | — | — |
| x64 | `windows_x64_custom_reverse_winhttp` | 0.0% (0/149) | 93.3% (140/150) | 100.0% (20/20) | 89.3% (134/150) | 90.6% (154/170) |
| x64 | `windows_x64_custom_reverse_winhttps` | 0.0% (0/150) | 6.7% (10/150) | 100.0% (20/20) | 6.7% (10/150) | 17.6% (30/170) |
| x64 | `windows_x64_messagebox` | 2.7% (4/150) | 72.0% (108/150) | 100.0% (20/20) | 100.0% (150/150) | 100.0% (170/170) |
| x64 | `windows_x64_meterpreter_bind_tcp` | 85.7% (126/147) | — | — | — | — |
| x64 | `windows_x64_meterpreter_bind_tcp_rc4` | 84.7% (127/150) | — | — | — | — |
| x64 | `windows_x64_meterpreter_bind_tcp_uuid` | 82.0% (123/150) | — | — | — | — |
| x64 | `windows_x64_meterpreter_reverse_http` | 0.0% (0/149) | 88.7% (133/150) | 100.0% (20/20) | 96.7% (145/150) | 97.1% (165/170) |
| x64 | `windows_x64_meterpreter_reverse_https` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 91.3% (137/150) | 92.4% (157/170) |
| x64 | `windows_x64_meterpreter_reverse_tcp` | 85.9% (128/149) | — | — | — | — |
| x64 | `windows_x64_meterpreter_reverse_tcp_rc4` | 85.3% (128/150) | — | — | — | — |
| x64 | `windows_x64_meterpreter_reverse_tcp_uuid` | 84.0% (126/150) | — | — | — | — |
| x64 | `windows_x64_meterpreter_reverse_winhttp` | 0.0% (0/149) | 88.0% (132/150) | 100.0% (20/20) | 95.3% (143/150) | 95.9% (163/170) |
| x64 | `windows_x64_meterpreter_reverse_winhttps` | 1.3% (2/150) | 76.7% (115/150) | 100.0% (20/20) | 82.7% (124/150) | 84.7% (144/170) |
| x64 | `windows_x64_pingback_reverse_tcp` | 84.5% (125/148) | — | — | — | — |
| x64 | `windows_x64_shell_bind_tcp` | 87.2% (130/149) | — | — | — | — |
| x64 | `windows_x64_shell_bind_tcp_rc4` | 86.0% (129/150) | — | — | — | — |
| x64 | `windows_x64_shell_bind_tcp_uuid` | 71.3% (107/150) | — | — | — | — |
| x64 | `windows_x64_shell_reverse_tcp` | 85.3% (128/150) | — | — | — | — |
| x64 | `windows_x64_shell_reverse_tcp_rc4` | 86.0% (129/150) | — | — | — | — |
| x64 | `windows_x64_shell_reverse_tcp_uuid` | 83.8% (124/148) | — | — | — | — |
| x64 | `windows_x64_vncinject_bind_tcp` | 84.7% (127/150) | — | — | — | — |
| x64 | `windows_x64_vncinject_bind_tcp_rc4` | 86.6% (129/149) | — | — | — | — |
| x64 | `windows_x64_vncinject_bind_tcp_uuid` | 85.3% (128/150) | — | — | — | — |
| x64 | `windows_x64_vncinject_reverse_http` | 0.0% (0/150) | 89.3% (134/150) | 100.0% (20/20) | 96.7% (145/150) | 97.1% (165/170) |
| x64 | `windows_x64_vncinject_reverse_https` | 1.3% (2/149) | 94.7% (142/150) | 100.0% (20/20) | 93.3% (140/150) | 94.1% (160/170) |
| x64 | `windows_x64_vncinject_reverse_tcp` | 83.9% (125/149) | — | — | — | — |
| x64 | `windows_x64_vncinject_reverse_tcp_rc4` | 86.7% (130/150) | — | — | — | — |
| x64 | `windows_x64_vncinject_reverse_tcp_uuid` | 73.2% (109/149) | — | — | — | — |
| x64 | `windows_x64_vncinject_reverse_winhttp` | 0.0% (0/150) | 92.7% (139/150) | 100.0% (20/20) | 94.0% (141/150) | 94.7% (161/170) |
| x64 | `windows_x64_vncinject_reverse_winhttps` | 0.0% (0/150) | 6.7% (10/150) | 100.0% (20/20) | 6.7% (10/150) | 17.6% (30/170) |
| x86 | `windows_custom_bind_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_custom_bind_tcp` | 82.0% (123/150) | — | — | — | — |
| x86 | `windows_custom_bind_tcp_rc4` | 84.0% (126/150) | — | — | — | — |
| x86 | `windows_custom_bind_tcp_uuid` | 83.3% (125/150) | — | — | — | — |
| x86 | `windows_custom_reverse_http` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_custom_reverse_https` | 22.0% (33/150) | — | 100.0% (10/10) | 29.3% (22/75) | 37.6% (32/85) |
| x86 | `windows_custom_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_custom_reverse_tcp` | 87.3% (131/150) | — | — | — | — |
| x86 | `windows_custom_reverse_tcp_allports` | 24.8% (29/117) | — | 100.0% (10/10) | 78.7% (59/75) | 81.2% (69/85) |
| x86 | `windows_custom_reverse_tcp_dns` | 23.3% (35/150) | — | 100.0% (10/10) | 17.3% (13/75) | 27.1% (23/85) |
| x86 | `windows_custom_reverse_tcp_rc4` | 90.0% (135/150) | — | — | — | — |
| x86 | `windows_custom_reverse_tcp_rc4_dns` | 24.7% (37/150) | — | 100.0% (10/10) | 28.0% (21/75) | 36.5% (31/85) |
| x86 | `windows_custom_reverse_tcp_uuid` | 84.0% (126/150) | — | — | — | — |
| x86 | `windows_custom_reverse_winhttp` | 21.3% (32/150) | — | 0.0% (0/10) | 0.0% (0/75) | 0.0% (0/85) |
| x86 | `windows_custom_reverse_winhttps` | 16.7% (25/150) | — | 100.0% (10/10) | 40.0% (30/75) | 47.1% (40/85) |
| x86 | `windows_messagebox` | 0.0% (0/150) | — | 100.0% (10/10) | 90.7% (68/75) | 91.8% (78/85) |
| x86 | `windows_meterpreter_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_meterpreter_bind_tcp_rc4` | 84.7% (127/150) | — | — | — | — |
| x86 | `windows_meterpreter_bind_tcp_uuid` | 92.7% (102/110) | — | — | — | — |
| x86 | `windows_meterpreter_reverse_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_meterpreter_reverse_tcp_allports` | 25.0% (30/120) | — | 100.0% (10/10) | 77.3% (58/75) | 80.0% (68/85) |
| x86 | `windows_meterpreter_reverse_tcp_dns` | 30.7% (46/150) | — | 100.0% (10/10) | 25.3% (19/75) | 34.1% (29/85) |
| x86 | `windows_meterpreter_reverse_tcp_rc4` | 85.3% (128/150) | — | — | — | — |
| x86 | `windows_meterpreter_reverse_tcp_rc4_dns` | 28.0% (42/150) | — | 100.0% (10/10) | 24.0% (18/75) | 32.9% (28/85) |
| x86 | `windows_meterpreter_reverse_tcp_uuid` | 76.0% (114/150) | — | — | — | — |
| x86 | `windows_meterpreter_reverse_winhttp` | 11.3% (17/150) | — | 0.0% (0/10) | 0.0% (0/75) | 0.0% (0/85) |
| x86 | `windows_meterpreter_reverse_winhttps` | 1.3% (2/150) | — | 100.0% (10/10) | 1.3% (1/75) | 12.9% (11/85) |
| x86 | `windows_patchupmeterpreter_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_patchupmeterpreter_bind_tcp` | 75.3% (113/150) | — | — | — | — |
| x86 | `windows_patchupmeterpreter_bind_tcp_rc4` | 82.7% (124/150) | — | — | — | — |
| x86 | `windows_patchupmeterpreter_bind_tcp_uuid` | 88.7% (133/150) | — | — | — | — |
| x86 | `windows_patchupmeterpreter_reverse_nonx_tcp` | 0.7% (1/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_patchupmeterpreter_reverse_tcp` | 84.0% (126/150) | — | — | — | — |
| x86 | `windows_patchupmeterpreter_reverse_tcp_allports` | 22.9% (27/118) | — | 100.0% (10/10) | 77.3% (58/75) | 80.0% (68/85) |
| x86 | `windows_patchupmeterpreter_reverse_tcp_dns` | 37.3% (56/150) | — | 100.0% (10/10) | 21.3% (16/75) | 30.6% (26/85) |
| x86 | `windows_patchupmeterpreter_reverse_tcp_rc4` | 88.7% (133/150) | — | — | — | — |
| x86 | `windows_patchupmeterpreter_reverse_tcp_rc4_dns` | 32.0% (48/150) | — | 100.0% (10/10) | 22.7% (17/75) | 31.8% (27/85) |
| x86 | `windows_patchupmeterpreter_reverse_tcp_uuid` | 74.7% (112/150) | — | — | — | — |
| x86 | `windows_pingback_bind_tcp` | 88.0% (132/150) | — | — | — | — |
| x86 | `windows_pingback_reverse_tcp` | 82.0% (123/150) | — | — | — | — |
| x86 | `windows_shell_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_shell_bind_tcp` | 20.0% (25/125) | — | 100.0% (10/10) | 73.3% (55/75) | 76.5% (65/85) |
| x86 | `windows_shell_bind_tcp_rc4` | 78.7% (118/150) | — | — | — | — |
| x86 | `windows_shell_bind_tcp_uuid` | 87.3% (131/150) | — | — | — | — |
| x86 | `windows_shell_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_shell_reverse_tcp` | 18.2% (22/121) | — | 100.0% (10/10) | 74.7% (56/75) | 77.6% (66/85) |
| x86 | `windows_shell_reverse_tcp_allports` | 21.5% (26/121) | — | 100.0% (10/10) | 76.0% (57/75) | 78.8% (67/85) |
| x86 | `windows_shell_reverse_tcp_dns` | 36.7% (55/150) | — | 100.0% (10/10) | 18.7% (14/75) | 28.2% (24/85) |
| x86 | `windows_shell_reverse_tcp_rc4` | 86.7% (130/150) | — | — | — | — |
| x86 | `windows_shell_reverse_tcp_rc4_dns` | 36.0% (54/150) | — | 100.0% (10/10) | 24.0% (18/75) | 32.9% (28/85) |
| x86 | `windows_shell_reverse_tcp_uuid` | 72.7% (109/150) | — | — | — | — |
| x86 | `windows_vncinject_bind_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_vncinject_bind_tcp` | 77.3% (116/150) | — | — | — | — |
| x86 | `windows_vncinject_bind_tcp_rc4` | 77.3% (116/150) | — | — | — | — |
| x86 | `windows_vncinject_bind_tcp_uuid` | 89.3% (134/150) | — | — | — | — |
| x86 | `windows_vncinject_reverse_http` | 0.0% (0/150) | — | 100.0% (10/10) | 2.7% (2/75) | 14.1% (12/85) |
| x86 | `windows_vncinject_reverse_nonx_tcp` | 0.0% (0/150) | — | 100.0% (10/10) | 0.0% (0/75) | 11.8% (10/85) |
| x86 | `windows_vncinject_reverse_tcp` | 84.0% (126/150) | — | — | — | — |
| x86 | `windows_vncinject_reverse_tcp_allports` | 16.3% (20/123) | — | 100.0% (10/10) | 74.7% (56/75) | 77.6% (66/85) |
| x86 | `windows_vncinject_reverse_tcp_dns` | 32.7% (49/150) | — | 100.0% (10/10) | 25.3% (19/75) | 34.1% (29/85) |
| x86 | `windows_vncinject_reverse_tcp_rc4` | 86.7% (130/150) | — | — | — | — |
| x86 | `windows_vncinject_reverse_tcp_rc4_dns` | 38.7% (58/150) | — | 100.0% (10/10) | 28.0% (21/75) | 36.5% (31/85) |
| x86 | `windows_vncinject_reverse_tcp_uuid` | 86.7% (130/150) | — | — | — | — |
| x86 | `windows_vncinject_reverse_winhttp` | 0.7% (1/150) | — | 100.0% (10/10) | 1.3% (1/75) | 12.9% (11/85) |

## File

- `working_rate_unified.csv` — tabella wide, tutti i 102 payload e tutti i dataset.
- `working_rate_unified_tests.csv` — dati grezzi aggregabili: una riga per test (vecchi + nuovi).
- `working_rate_unified.xlsx` — workbook con riepilogo, confronto, per tecnica, matrice, dati completi.
- `low_working_rate_payloads.csv` — lista dei 49 payload sotto soglia.
- `mutations_new_xd_ebi/` — payload rigenerati (x64/x86).

