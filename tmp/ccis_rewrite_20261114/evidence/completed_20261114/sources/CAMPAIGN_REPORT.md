# Campagna completa 2026-11-13 — stato e risultati

Aggiornamento: 2026-11-14 01:20 (Europe/Berlin). **Tutte e tre le campagne
sono completate**, incluse le scansioni VirusTotal dei 549 SHA unici.

## Sintesi per i tre punti richiesti

1. **Nuova tecnica (assembly wrapping)**: valutata su tutti i 102 payload
   `original_pl`, x64 e x86, `-xd -wrap` singolarmente e senza combo, 3 seed
   perché il layout è stocastico. 243/306 build, 170/243 funzionanti;
   207 SHA unici su VirusTotal, **0 rilevati su 75 motori**.
2. **LLM morphing**: 816 celle (102 payload × 4 tecniche × 0/2 shot), una
   generazione per cella. 350 output costruiti, 275 funzionanti; 323 SHA unici
   su VirusTotal, 221 rilevati (68,4%, 3,79 malicious medi). Il limite è la
   copertura dei dati inline e il tetto di output, non il numero di payload
   provati: tutte le 816 celle sono state tentate.
3. **Symbolic+euristiche vs LLM data handling**: sui 19 payload con dati
   mobili, entrambi 19/19 build e 17/19 funzionanti; output finale identico in
   16/19; simbolico 124,0 s mediani, LLM 59,9 s e $0,2218 totali.

Prima di questa campagna i dati disponibili coprivano solo 13 payload x64 per
`-wrap` (e in combinazione), un solo payload per il morphing LLM e cinque
condizioni per il data handling: la matrice richiesta era quindi incompleta.

Corpus: **102 payload `original_pl`** (38 x64, 64 x86), come da baseline del
paper. Motore congelato in `bench/engines/2026-11-13_block3/` (pobf.py
193.789 B, pobf86.py 200.222 B, asm_wrap.py 34.122 B). Harness funzionale:
`tmp/campaign/harness.py` (dialogo `#32770` per MessageBox, connessione TCP
1234 per reverse/bind, uscita pulita per gli altri). Baseline originali:
**102/102 OK** (`tmp/campaign/baseline_originals.csv`).

## 1. Assembly wrapping (`-xd -wrap`, una sola tecnica, 3 seed)

Protocollo: 102 payload × 3 seed = 306 build pianificati; `ZONE_WRAP_SEED` =
101/102/103; `-xd` è preprocessing dati, non una tecnica combinata. Ogni
binario è stato eseguito; i fallimenti della prima passata sono stati
rieseguiti in isolamento con timeout 10 s.

| Arch | Pianificati | Build | Build % | Working (W/B) | Working (W/N) | SHA unici |
|---|---:|---:|---:|---:|---:|---:|
| x64 | 114 | 63 | 55,3% | 63/63 = 100,0% | 55,3% | 63/63 |
| x86 | 192 | 180 | 93,8% | 107/180 = 59,4% | 55,7% | 144/180 |
| **Totale** | **306** | **243** | **79,4%** | **170/243 = 70,0%** | **55,6%** | **207/243** |

- x64: 17 payload non costruibili (51 build fallite). Cause: dati inline non
  riconosciuti da `-xd` (`the bytes at 0x... are not code`) su tutte le
  varianti RC4/UUID e sui tre `*_winhttps`; un caso `RIP target mismatch`
  (`meterpreter_reverse_tcp_uuid`). Tutti i 63 binari costruiti funzionano.
- x86: 4 payload non costruibili (12 build fallite). 73 output su 180 non
  funzionano. I fallimenti sono sistematici e concentrati in famiglie:
  `*_nonx_tcp`, `*_tcp_dns`, `*_tcp_rc4_dns`, `*_https`, `*_winhttp` (e
  `custom_reverse_https`). Queste famiglie contengono dati inline che `-xd`
  x86 non estrae completamente; il wrapping tratta quei byte come codice.
- Working rate x64 sui costruiti: 100%. Working rate x86 sui costruiti:
  59,4%. Non è lecito estendere i risultati x64 a x86.
- Diversità: 207 SHA-256 distinti su 243 file (36 collisioni x86; i seed non
  cambiano il layout dei payload più piccoli).

Dettaglio per payload: `tmp/campaign/wrap_summary.csv`; fallimenti:
`tmp/campaign/wrap_failures.csv`.

## 2. LLM morphing (`--llm -<tech>`, 0-shot e 2-shot)

Protocollo: 102 payload × 4 tecniche (`eq`, `nop`, `bcf`, `ibp`) × 2
condizioni (`--llm-shots 0/2`) = 816 celle; una generazione per cella
(`--llm-retries 1`, primo tentativo), modello `deepseek-flash`,
`--llm-max-tokens 65536`, validazione statica del motore e verifica
funzionale esterna con l'harness. I fallimenti restano nel denominatore.

| Arch | Celle | Build | Build % | Working (W/B) | Working (W/N) | SHA unici | Costo |
|---|---:|---:|---:|---:|---:|---:|---:|
| x64 | 304 | 53 | 17,4% | 52/53 = 98,1% | 52/304 = 17,1% | 51 | $7,74 |
| x86 | 512 | 297 | 58,0% | 223/297 = 75,1% | 223/512 = 43,6% | 272 | $11,53 |
| **Totale** | **816** | **350** | **42,9%** | **275/350 = 78,6%** | **275/816 = 33,7%** | **323** | **$19,27** |

| Shot | Celle | Build | Working | SHA unici | Costo |
|---|---:|---:|---:|---:|---:|
| 0-shot | 408 | 178 (43,6%) | 139 (34,1%) | 171 | $9,48 |
| 2-shot | 408 | 172 (42,2%) | 136 (33,3%) | 169 | $9,79 |

- Costo medio per cella: $0,0236; tempo mediano per chiamata: 160,3 s;
  similarità media delle risposte accettate: 0,906 (mediana 0,936).
- Fallimenti (466 celle): 245 errori di disassemblaggio (branch su confine
  non valido), 93 “other”, 74 validation, 53 `finish_reason=length` (tetto
  65.536 token, soprattutto `bcf`/`ibp` su payload grandi), 1 rete.
- **x64 è il limite principale**: 17 dei 38 payload hanno dati inline che
  `-xd` non estrae (RC4/UUID, `*_winhttps`); il modello riceve un listing in
  cui quei byte sono decodificati come codice e non può produrre un output
  valido. Inoltre `bcf`/`ibp` superano il tetto di output sui payload grandi.
- 0-shot e 2-shot non mostrano una differenza sostanziale: 2-shot costa
  leggermente di più e produce 6 build in meno. Non sostenere una superiorità
  del 2-shot con questo campione.
- I 350 output costruiti (323 SHA unici) sono stati scansionati su VT; i 466
  fallimenti non hanno un artefatto da scansionare.

Dettaglio per cella: `tmp/campaign/llm_summary.csv`.

## 3. Symbolic + euristiche vs LLM data handling

Protocollo: solo i 19 payload in cui `-xd` trova sezioni dati mobili (13 x64,
6 x86). Braccio simbolico: output `-xd` del prewarm. Braccio LLM:
`--llm-data` (classificazione + stessa pipeline deterministica di estrazione),
1 run per payload. Entrambi eseguiti con lo stesso harness.

| Metrica | Simbolico+euristiche | LLM data |
|---|---:|---:|
| Build | 19/19 (100%) | 19/19 (100%) |
| Funzionanti | 17/19 (89,5%) | 17/19 (89,5%) |
| Sezioni raw = | — | 9/19 (47,4%) |
| Byte raw = | — | 9/19 (47,4%) |
| Output finale identico | — | **16/19 (84,2%)** |
| Tempo mediano | 124,0 s | 59,9 s |
| Costo API | $0 | **$0,2218 totale** (mediana $0,0083) |

- I due fallimenti funzionali sono gli stessi in entrambi i bracci
  (`x86 custom_reverse_winhttp`, `x86 meterpreter_reverse_winhttp`): il
  problema è nella pipeline deterministica condivisa, non nel classificatore.
- Su 3 payload x64 `*_winhttps` il LLM propone più dati del simbolico (256-348
  B contro 20 B) e produce un output diverso, ma funzionante.
- La concordanza grezza è bassa (9/19), quella dell'output finale è alta
  (16/19): i filtri deterministici assorbono molte differenze.
- Dettaglio: `tmp/campaign/data_compare.csv`.

## 4. VirusTotal

Manifest: `vt_manifest_campaign.json` (612 file, 549 SHA unici; 27 hash
condivisi tra più condizioni). Tre key API, 500 richieste/giorno per key;
upload e report completati per **tutti i 549 SHA unici**. Il detection rate
qui è la frazione di file con almeno un verdetto malicious (`q`); `Malicious
medi` è la media dei verdetti per file. Motori non supportati e timeout restano
fuori dal totale restituito dall'API.

| Gruppo | SHA unici | Analisi completate | Rilevati | q | Malicious medi | Max |
|---|---:|---:|---:|---:|---:|---:|
| `wrap` | 207 | 207 | **0** | **0,0%** | 0,00 | 0 |
| `llm_eq_s0` | 37 | 37 | 26 | 70,3% | 2,49 | 18 |
| `llm_eq_s2` | 40 | 40 | 30 | 75,0% | 2,80 | 9 |
| `llm_nop_s0` | 46 | 46 | 18 | 39,1% | 2,17 | 22 |
| `llm_nop_s2` | 41 | 41 | 15 | 36,6% | 1,78 | 10 |
| `llm_bcf_s0` | 46 | 46 | 36 | 78,3% | 3,76 | 15 |
| `llm_bcf_s2` | 42 | 42 | 29 | 69,0% | 5,24 | 23 |
| `llm_ibp_s0` | 42 | 42 | 37 | 88,1% | 5,48 | 16 |
| `llm_ibp_s2` | 46 | 46 | 40 | 87,0% | 5,80 | 26 |
| `lldata` | 19 | 19 | **19** | **100,0%** | 20,63 | 25 |

Totale LLM: 350 output costruiti → 323 SHA unici, **221 rilevati (68,4%)**,
3,79 malicious medi, massimo 26. I gruppi per tecnica sommano 340 perché 17
hash sono condivisi tra celle diverse.

Lettura:
- **`-wrap` è l'unica tecnica che azzera la detection**: 0/207 file, 0
  malicious e 0 suspicious su 75 motori. È il risultato centrale.
- **LLM morphing riduce molto la detection rispetto agli originali** (26,6
  malicious medi, 13/13 rilevati il 2026-11-13) ma non la azzera: 68,4% dei
  file resta rilevato, con 1,8-5,8 malicious medi a seconda di tecnica e shot.
  `nop` è la più bassa (1,78-2,17), `ibp` la più alta (5,48-5,80).
- **0-shot vs 2-shot non ha un vincitore netto**: `nop` 2-shot è leggermente
  peggiore, `eq`/`bcf`/`ibp` 2-shot leggermente peggiori in detections ma
  comparabili; il campione per cella è piccolo.
- I 60 output LLM **non funzionanti** hanno detection media 1,03 (11/60
  rilevati): sono artefatti più semplici/piccoli e non vanno letti come
  evasione, perché non eseguono.
- **`lldata` non aggiunge evasione**: 19/19 rilevati, 20,63 malicious medi,
  coerente con gli originali, perché il codice resta intatto.

## 5. File prodotti

- `tmp/campaign/` — script, log e CSV/JSONL delle campagne.
- `mutations_all/wrap/{x64,x86}/` — 243 mutanti `-wrap`.
- `mutations_all/llm/{x64,x86}/` — 350 output LLM.
- `mutations_all/lldata/{x64,x86}/` — 19 output LLM-data.
- `vt_manifest_campaign.json`, `tmp/vt_results_campaign.jsonl`.
