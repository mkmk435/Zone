# Piano di estensione — "Zone: a bin2bin Metamorphic Engine"

Obiettivo: **+30% di contenuti nuovi** (≈4 pagine su 13) senza indebolire la parte esistente.
Ipotesi di lavoro: estensione journal / resubmission con peer review seria. Se il venue ha un
limite di pagine rigido, la parte nuova deve *sostituire* quella vecchia (vedi §5).

---

## 0. Cosa dicono davvero i dati (verificato nel workspace)

| Fatto | Valore |
|---|---|
| Scan VirusTotal totali | 15.021 (102 payload originali + 102 SGN + 14.817 mutazioni) |
| Varianti per payload×tecnica | 10 (il dataset completo è in `results.json`) |
| Finestra temporale scan | **2025-04-30 → 2025-05-04** e **2025-09-04 → 2025-09-17** |
| PII (x64+x86) | **0 detection su 950 file** (~72.000 scan engine), limite sup. 95% ≈ 0,3% a livello file |
| EQ | 2,24% (x64), 2,63% (x86) — l'unica tecnica chiaramente rilevata |
| Altre tecniche pesanti | 0,0–1,0% (x64), 0,0–0,3% (x86) |

Due conseguenze:

1. **Tecnica e data di scan sono confondate.** Le tecniche singole (nop, eq, pii, bcf, ibp)
   sono state scansionate ad aprile-maggio; quasi tutte le combinate a settembre. Un engine
   aggiornato a settembre non è comparabile con uno di aprile. La Figure 1 confronta quindi
   tecniche *e* periodi diversi. La conclusione "PII è la migliore" sopravvive (0 vs 0,5–1%),
   ma il ranking fine no.
2. **La scala è 0–1%.** Differenze tipo 0,51% vs 0,80% sono ~0,2 engine per file: dentro il
   rumore. Il paper le presenta come ordinamento, e non regge.

Da qui il reframing consigliato: non "quale tecnica vince di 0,3 punti", ma
**"tutte le trasformazioni pesanti saturano il detector a firme; la scelta si sposta su
working rate × dimensione × esposizione runtime"**.

---

## 1. I sei attacchi che un revisore farebbe (e come neutralizzarli)

1. **"PII vince solo perché gonfia il file di 10×."** → serve l'ablazione (B1). È l'attacco
   più pericoloso perché colpisce il contributo nuovo.
2. **"VirusTotal è solo firme."** → serve un detector addestrato (B2).
3. **"I numeri non hanno incertezza e mescolano periodi."** → B3.
4. **"Varianti virtualmente infinite" mai misurato.** → B4.
5. **"PII è un interprete degenere, non una tecnica nuova."** → B5 (posizionamento vs
   virtualizzazione + fingerprinting).
6. **"Il payload resta mutato in memoria" asserito, non misurato.** → B6 (dump di memoria).

---

## 2. Blocchi di contenuto nuovo

### B1 — Ablazione del meccanismo PII (priorità 1)

**Domanda:** l'evasione di PII viene dallo *shuffle*, dai *wrapper*, dal *dispatcher* o solo
dalla dimensione?

**Varianti da implementare (flag in `pobf.py`/`pobf86.py`):**

| Variante | Cosa tiene | Isola |
|---|---|---|
| `full` | tutto PII | — |
| `no_shuffle` | wrapper + dispatcher + tabella, layout sequenziale | contributo dello shuffle |
| `no_dispatch` | wrapper inline con fall-through, niente tabella/stub | costo e effetto del dispatcher |
| `pad_only` | nessun PII, padding casuale a dimensione pari alla media PII | solo inflazione dimensionale |
| `shuffle_only` | permutazione dei blocchi originali con `jmp` espliciti | permutazione pura, senza wrapper |

**Sweep parametrici** (stessa sessione di scan):
- IBP: block size ∈ {1, 2, 4, 8, 16};
- EQ: densità di sostituzione ∈ {10%, 50%, 100%};
- NOP: densità ∈ {bassa, media, alta}.

**Protocollo:** 10 payload/architettura (5 "puliti" + 5 con dati inline), 5 varianti per
configurazione, tutte scansionate **nello stesso giorno**.

**Output:** tabella detection × variante + Δ rispetto a `full`; figura `detection vs block size`.

**Perché vale 1,5–2 pagine:** trasforma "PII funziona" in "PII funziona *per questo motivo*".
Se `pad_only ≈ full`, il paper deve cambiare tesi — meglio scoprirlo ora che in review.

---

### B2 — Oltre la firma: detector addestrato (priorità 2)

**Setup:**
- Feature: byte n-gram (1–3) TF-IDF; opcode n-gram via Capstone; statistiche di sezione.
- Modelli: Logistic Regression (interpretabile) + HistGradientBoosting.
- Split: **leave-one-payload-out** (generalizza a payload nuovi) e
  **leave-one-technique-out** (generalizza a trasformazioni mai viste).
- Metriche: AUC, TPR@1% FPR, macro-F1; baseline maggioritaria.

**Tre task distinti (tutti interessanti):**
1. `original vs morphed` → il modello "vede" la trasformazione? (proxy di rilevabilità)
2. `attribuzione della tecnica` (15 classi) → quanto è fingerprintabile l'engine?
3. `famiglia del payload` dopo il morphing → quanta semantica "trapela"?

**Output:** tabella AUC per tecnica, curva ROC, discussione su quali trasformazioni sono
strutturalmente riconoscibili (ipotesi: EQ e IBP lasciano segnale distribuzionale, PII no).

**Perché vale 2–2,5 pagine:** è l'esperimento che i revisori chiedono quando vedono solo VT.
Costo: zero API, tutto offline sui ~15k file già presenti.

---

### B3 — Rigore statistico e validità temporale (priorità 1, economico)

- Unità di analisi = **payload** (cluster), non engine. Le detection sono correlate dentro
  il file: il CI engine-level è troppo stretto.
- Cluster bootstrap (10k repliche, resampling dei payload) per i CI delle medie per tecnica.
- Wilcoxon signed-rank appaiato per payload (tecnica vs originale), Cliff's delta come effect
  size, correzione Holm su 15 confronti.
- Modello misto: `detection ~ tecnica + (1|payload) + (1|data_scan)`.
- **Temporal drift:** re-scan bilanciato in un'unica giornata di un sottoinsieme
  (5 payload × 15 tecniche × 2 varianti × 2 arch = 300 file), confronto con lo storico via
  McNemar → quantifica quanto il ranking è stabile.

**Output:** 2 tabelle + 1 figura `detection vs data di scan`.

**Perché vale 1,5 pagine:** trasforma il punto debole in un risultato metodologico
("le misure VT-based di evasione hanno una scadenza").

---

### B4 — Diversità dell'output e costo (priorità 3, economico)

- **Diversità intra-tecnica:** unicità SHA-256 (attesa 100%), Jaccard su 4-gram di byte,
  NCD (zlib), JSD delle distribuzioni di opcode; per payload e per tecnica.
- **Costo:** Δsize% (già), overhead PII = (|wrapper| + |stub|) per istruzione originale,
  frontiera di Pareto `detection vs Δsize`, metrica "byte spesi per punto di detection".

**Output:** 1 tabella + 1 figura Pareto.

**Perché vale 1 pagina:** sostiene il claim "varianti virtualmente illimitate" con un numero
e dà al praticante una regola di scelta (PII costa 10× per X punti).

---

### B5 — Posizionamento e robustezza dell'engine (priorità 4, quasi solo prosa)

- **PII come VM degenere:** handler = wrapper di 5 istruzioni, dispatcher = loop di
  interpretazione, tabella = bytecode. Confronto con virtualizzazione (VMProtect, Themida,
  Tigress): overhead tipici 2–10× vs PII 8–18×, ma PII non ha diversità di handler né
  context mixing → protezione più debole. Tabella comparativa.
- **Fingerprinting di Zone:** euristica/classificatore per riconoscere l'output (wrapper
  ripetuto, `jmp` verso un dispatcher unico, tabella di offset). Misura AUC. Poi contromisure
  (N copie del dispatcher, stub polimorfico via EQ, tabella codificata) e rimisura.
- **Threat model** esplicito (firma, ML statico, sandbox dinamica, memory scanner),
  **ethics/dual-use**, **reproducibility** (seed, hash, comandi).

**Perché vale 1,5 pagine:** anticipa la critica "è un interprete noto" e mostra che sapete
attaccare il vostro stesso strumento. È raro nei paper offensivi e colpisce i revisori.

---

### B6 — Opzionali ad alto impatto (solo se c'è tempo)

- **Memoria:** dump post-esecuzione + scan VT per varianti Zone (riusa l'harness SGN già
  usato per il confronto). Verifica diretta del claim centrale.
- **Iterated morphing** k = 1..5: curva di saturazione di detection e working rate.
- **Wild shellcode** (shell-storm, exploit-db): test out-of-distribution, fuori Metasploit.
- **Failure taxonomy** strumentata: causa del fallimento (abort di estrazione, crash, timeout,
  dato inline) invece del solo OK/FAIL.

---

## 3. Budget pagine

| Blocco | Pagine | Tipo |
|---|---:|---|
| B1 ablazione | 1,5–2 | esperimento + 2 figure |
| B2 detector ML | 2–2,5 | esperimento + 2 figure |
| B3 rigore | 1,5 | tabelle + metodo |
| B4 diversità/costo | 1 | tabella + figura |
| B5 posizionamento | 1,5 | prosa + 1 tabella |
| **Totale** | **7,5–8,5** | |

30% ≈ 4 pagine. Il set minimo consigliato è **B1 + B3 + B4** (≈4–4,5 pagine): prende il
contributo nuovo (meccanismo), lo difende (statistica) e lo quantifica (costo).
**B2 è il moltiplicatore**: da solo vale il salto di qualità verso un venue serio.

---

## 4. Correzioni da fare subito (prima di aggiungere contenuto)

1. **Figura 3 e Figura 5: etichette sbagliate.** I dati sono nell'ordine
   `…, eq_nop, eq_pii, eq_bcf, eq_ibp, nop_pii, nop_bcf, nop_ibp` (ordine della Fig. 4), ma le
   `xticklabels` sono nell'ordine `…, eq_nop, eq_bcf, eq_ibp, eq_pii, nop_bcf, nop_ibp, nop_pii`.
   Risultato: `eq_bcf` mostra −24,5% (che è `eq_pii`) e la Fig. 5 mostra `eq_bcf = 0,44`
   (che è `eq_pii`). Il testo dice "BCF ha entropia stabile" mentre il grafico gli attribuisce
   il valore di PII: un revisore lo nota subito.
2. **Figura 2:** il punto x86 di `nop_bcf` è a 28,0 con etichetta "0,3%" (valore copiato da
   x64). Dalla tabella è 45,8%.
3. **Working rate contaminato dal bug del label-table.** In Fig. 2 `eq_nop_bcf` x64 = 1,1% e
   `nop_bcf` x64 = 0,3%: non è una proprietà delle tecniche, è il bug del `je` di `-bcf`
   (fixato: 10/10 su ploader). Il testo dice "PII è la meno stabile", ma la figura mostra
   due combinazioni BCF a ~0–1%. Va rigenerata con i dati post-fix (in `mutations_fixed` /
   `mutations_getpc`), e il bug va raccontato come contributo ingegneristico.
4. **Ordine canonico unico** delle 15 tecniche in tutte le figure.
5. **`Table 6` hardcoded** → `\ref{tab:functional-payload}`.
6. **Entropia:** il testo parla di asm, la Fig. `shan_entropy_bytes` mostra byte (tutti
   negativi). O si spiega la differenza o si toglie la figura.
7. **`0%` senza n:** ovunque "0%" va accompagnato da "0/950" e dal limite superiore.

---

## 5. Se c'è un limite di pagine

Tagliare, non comprimere:
- Fig. `shan_entropy_bytes` (ridondante, poco discussa) → −0,5 pagina;
- etichette numeriche su ogni punto delle figure → −0,4 pagina (e figure più leggibili);
- fusione di `length` + `cosine` in una figura multi-pannello → −0,4 pagina;
- background: accorciare la parte su polymorphic/metamorphic, già nota ai revisori → −0,5.

Recupero ≈ 1,8 pagine, quasi metà del Budget.

---

## 6. Ordine di esecuzione consigliato

| Fase | Contenuto | Dipendenze |
|---|---|---|
| 0 | Fix figure + ordine canonico + numeri post-fix | nessuna |
| 1 | B3 (statistica offline) + B4 (diversità offline) | dati esistenti |
| 2 | B2 (detector ML) | dati esistenti, `numpy`/`sklearn` |
| 3 | B1 (flag + generazione + re-scan) | modifiche a `pobf*.py`, chiavi VT |
| 4 | B5 (prosa + fingerprinting) | B2 opzionale |
| 5 | B6 (memoria, iterazioni) | VM Windows |

---

## 7. Cosa posso fare io, subito e senza il tuo intervento

- Analisi statistica completa da `results.json` (bootstrap cluster, Wilson, Wilcoxon,
  Cliff's delta, tabella per payload/famiglia) → LaTeX pronto.
- Analisi di diversità sui `.bin` (unicità, Jaccard, NCD, JSD) → tabella + figura.
- Rigenerazione di tutte le figure con ordine canonico e valori corretti, da un unico
  file di dati (basta un `techniques.csv`).
- Bozza LaTeX delle sezioni B3/B4/B5.
- Detector ML (B2) end-to-end, se installiamo `scikit-learn` o uso il Python bundled.
