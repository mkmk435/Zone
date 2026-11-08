# Working rate tables

Dati: `test_report.txt` (originale, nessun flag), `test_report_x64_low_xd_ebi_5001.txt` (`-xd -ebi` con capstone 5.0.0.post1, prima della fix getpc), `test_report_x64_low_getpc.txt` (`-xd -ebi` + fix getpc, aggiornato).


## x86: working rate per tecnica (dataset originale, tutti i payload)

| Tecnica | OK/test | Working rate |
|---|---:|---:|
| nop | 309/640 | 48.3% |
| eq | 496/640 | 77.5% |
| pii | 221/569 | 38.8% |
| bcf | 337/640 | 52.7% |
| ibp | 331/640 | 51.7% |
| eq_nop_pii | 146/609 | 24.0% |
| eq_nop_bcf | 281/640 | 43.9% |
| eq_nop_ibp | 261/640 | 40.8% |
| nop_eq | 308/640 | 48.1% |
| nop_pii | 169/576 | 29.3% |
| nop_bcf | 293/640 | 45.8% |
| nop_ibp | 259/640 | 40.5% |
| eq_pii | 157/561 | 28.0% |
| eq_bcf | 353/640 | 55.2% |
| eq_ibp | 324/640 | 50.6% |

## x64: working rate per tecnica (dataset originale, tutti i payload)

| Tecnica | OK/test | Working rate |
|---|---:|---:|
| nop | 249/380 | 65.5% |
| eq | 249/380 | 65.5% |
| pii | 229/380 | 60.3% |
| bcf | 250/380 | 65.8% |
| ibp | 250/380 | 65.8% |
| eq_nop_pii | 244/380 | 64.2% |
| eq_nop_bcf | 4/380 | 1.1% |
| eq_nop_ibp | 250/380 | 65.8% |
| nop_eq | 249/377 | 66.0% |
| nop_pii | 212/370 | 57.3% |
| nop_bcf | 1/375 | 0.3% |
| nop_ibp | 250/377 | 66.3% |
| eq_pii | 216/377 | 57.3% |
| eq_bcf | 251/376 | 66.8% |
| eq_ibp | 246/373 | 66.0% |

## x64, 13 payload a basso working rate: per payload

| Payload | Originale | Post `-xd -ebi` | Post `-xd -ebi` + getpc |
|---|---:|---:|---:|
| windows_x64_custom_reverse_https | 0.0% (0/149) | 94.0% (141/150) | 88.0% (132/150) |
| windows_x64_custom_reverse_winhttp | 0.0% (0/149) | 6.7% (10/150) | 93.3% (140/150) |
| windows_x64_custom_reverse_winhttps | 0.0% (0/150) | 6.7% (10/150) | 6.7% (10/150) |
| windows_x64_meterpreter_reverse_http | 0.0% (0/149) | 4.7% (7/150) | 88.7% (133/150) |
| windows_x64_meterpreter_reverse_https | 0.0% (0/149) | 6.7% (10/150) | 88.0% (132/150) |
| windows_x64_meterpreter_reverse_winhttp | 0.0% (0/149) | 82.0% (123/150) | 88.0% (132/150) |
| windows_x64_vncinject_reverse_http | 0.0% (0/150) | 2.7% (4/150) | 89.3% (134/150) |
| windows_x64_vncinject_reverse_winhttp | 0.0% (0/150) | 6.7% (10/150) | 92.7% (139/150) |
| windows_x64_vncinject_reverse_winhttps | 0.0% (0/150) | 6.7% (10/150) | 6.7% (10/150) |
| windows_x64_meterpreter_reverse_winhttps | 1.3% (2/150) | 82.7% (124/150) | 76.7% (115/150) |
| windows_x64_vncinject_reverse_https | 1.3% (2/149) | 6.7% (10/150) | 94.7% (142/150) |
| windows_x64_messagebox | 2.7% (4/150) | 73.3% (110/150) | 72.0% (108/150) |
| windows_x64_custom_reverse_http | 10.2% (15/147) | 98.0% (147/150) | 87.3% (131/150) |
| **Totale (13)** | **1.2%** (23/1941) | **36.7%** (716/1950) | **74.8%** (1458/1950) |

## x64, 13 payload: working rate per tecnica

| Tecnica | Originale | Post `-xd -ebi` | Post `-xd -ebi` + getpc |
|---|---:|---:|---:|
| nop | 0.0% (0/130) | 26.2% (34/130) | 77.7% (101/130) |
| eq | 0.0% (0/130) | 93.1% (121/130) | 100.0% (130/130) |
| pii | 0.0% (0/130) | 38.5% (50/130) | 84.6% (110/130) |
| bcf | 0.0% (0/130) | 38.5% (50/130) | 80.8% (105/130) |
| ibp | 0.0% (0/130) | 24.6% (32/130) | 64.6% (84/130) |
| eq_nop_pii | 0.8% (1/130) | 36.9% (48/130) | 63.8% (83/130) |
| eq_nop_bcf | 0.0% (0/130) | 37.7% (49/130) | 80.8% (105/130) |
| eq_nop_ibp | 0.0% (0/130) | 26.9% (35/130) | 53.1% (69/130) |
| nop_eq | 6.2% (8/128) | 27.7% (36/130) | 78.5% (102/130) |
| nop_pii | 0.8% (1/128) | 38.5% (50/130) | 65.4% (85/130) |
| nop_bcf | 0.0% (0/129) | 36.9% (48/130) | 83.1% (108/130) |
| nop_ibp | 1.6% (2/129) | 26.9% (35/130) | 54.6% (71/130) |
| eq_pii | 0.0% (0/130) | 38.5% (50/130) | 84.6% (110/130) |
| eq_bcf | 7.0% (9/128) | 36.9% (48/130) | 84.6% (110/130) |
| eq_ibp | 1.6% (2/129) | 23.1% (30/130) | 65.4% (85/130) |

## x64, matrice payload x tecnica (Post `-xd -ebi` + getpc)

| Payload | nop | eq | pii | bcf | ibp | eq_nop_pii | eq_nop_bcf | eq_nop_ibp | nop_eq | nop_pii | nop_bcf | nop_ibp | eq_pii | eq_bcf | eq_ibp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| windows_x64_custom_reverse_https | 100% | 100% | 100% | 90% | 60% | 50% | 100% | 70% | 100% | 90% | 100% | 80% | 100% | 100% | 80% |
| windows_x64_custom_reverse_winhttp | 100% | 100% | 100% | 90% | 80% | 80% | 100% | 90% | 100% | 80% | 100% | 80% | 100% | 100% | 100% |
| windows_x64_custom_reverse_winhttps | 0% | 100% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| windows_x64_meterpreter_reverse_http | 100% | 100% | 100% | 100% | 100% | 60% | 100% | 50% | 100% | 70% | 100% | 60% | 100% | 100% | 90% |
| windows_x64_meterpreter_reverse_https | 100% | 100% | 100% | 100% | 80% | 70% | 100% | 70% | 100% | 60% | 90% | 70% | 100% | 100% | 80% |
| windows_x64_meterpreter_reverse_winhttp | 100% | 100% | 100% | 100% | 100% | 80% | 100% | 30% | 100% | 60% | 100% | 60% | 100% | 100% | 90% |
| windows_x64_vncinject_reverse_http | 100% | 100% | 100% | 100% | 70% | 80% | 90% | 60% | 100% | 80% | 100% | 60% | 100% | 100% | 100% |
| windows_x64_vncinject_reverse_winhttp | 100% | 100% | 100% | 100% | 100% | 90% | 100% | 80% | 100% | 80% | 100% | 60% | 100% | 100% | 80% |
| windows_x64_vncinject_reverse_winhttps | 0% | 100% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| windows_x64_meterpreter_reverse_winhttps | 10% | 100% | 100% | 80% | 70% | 90% | 70% | 80% | 20% | 100% | 90% | 60% | 100% | 100% | 80% |
| windows_x64_vncinject_reverse_https | 100% | 100% | 100% | 100% | 90% | 90% | 100% | 100% | 100% | 70% | 100% | 90% | 100% | 100% | 80% |
| windows_x64_messagebox | 100% | 100% | 100% | 90% | 0% | 100% | 90% | 0% | 100% | 100% | 100% | 0% | 100% | 100% | 0% |
| windows_x64_custom_reverse_http | 100% | 100% | 100% | 100% | 90% | 40% | 100% | 60% | 100% | 60% | 100% | 90% | 100% | 100% | 70% |
