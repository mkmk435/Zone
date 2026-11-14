# Revisione CCIS di Zone: struttura, contributi ed evidenze

Analisi del 13 novembre 2026 del manoscritto LaTeX incollato, del codice e degli artefatti presenti nel workspace. Non sono stati eseguiti payload, chiamate LLM o nuove scansioni. I numeri sotto sono ricavati dai file esistenti. Il log VirusTotal viene aggiornato da un processo esterno e rappresenta quindi una fotografia temporanea.

## 1. La modifica principale

La bozza descrive quasi esclusivamente la baseline della conferenza e lascia le estensioni come placeholder. Il repository contiene invece un'estensione con un filo scientifico preciso: **identificazione di codice e dati, riscrittura con conservazione dei dati, trasformazioni native e assistite da LLM, valutazione separata di costruibilità, funzionalità e caratteristiche della rappresentazione**.

Questo deve diventare il centro della versione CCIS. Non suggerisco di ripartire dal vecchio `PAPER_EXTENSION_PLAN.md`: contiene molte proposte ancora ipotetiche e alcune indicazioni superate. Non serve aggiungere altri esperimenti estranei alle estensioni già implementate per riempire pagine.

Titolo possibile:

> Zone: Code–Data Identification and LLM-Assisted Binary Transformation for Windows Payloads

Il titolo attuale è utilizzabile, ma comunica poco le estensioni. Eviterei di inserire “novel” riferito ad assembly wrapping o “semantic equivalence” riferito ai controlli disponibili.

## 2. Che cosa risulta effettivamente fatto

| Estensione | Implementazione verificata | Evidenza disponibile | Portata sostenibile nel paper |
|---|---|---|---|
| Identificazione simbolica/euristica code/data | `symbolic_payload_coverage.py`: `static_candidates`, `identify_data`, `find_data_sections`, `explore` | Report JSON su più payload; copertura incompleta esplicitamente registrata | Analisi ibrida basata su CFG, esplorazione simbolica limitata e riconoscimento di candidati dati |
| Estrazione e conservazione dei dati | `pobf.py` e `pobf86.py`: `analyze_data`, `find_data_and_refs`, `extract_data`, `finalize_data_refs` | Campagna funzionale aggiornata, cache e report per campione | Integrazione di un livello di gestione dei dati, con controlli e limitazioni dichiarati |
| Identificazione code/data con LLM | `llm_data.py`: parsing degli intervalli e `run_data` | 15 output su quattro payload distinti, comprendendo cinque condizioni | Studio pilota di classificazione assistita da LLM e compatibilità con l'estrazione |
| Morphing LLM | `llm_technique.py`, `llm_payload.py`, `llm_stats.py` | EQ/NOP/BCF/IBP, 0 e 2 shot, tre repliche per cella: 24 output finali | Studio pilota su un solo payload x64, con validazione e tentativi successivi |
| Assembly wrapping | `asm_wrap.py`, integrazione in `pobf.py` | 260 casi pianificati su 13 payload x64 e due configurazioni; 200 build | Implementazione e integrazione di una tecnica esistente; nessuna rivendicazione di invenzione |
| Valutazione della classificazione | Report di candidati, test software e confronto di output | Concordanza fra metodi e controlli funzionali; non ho trovato un benchmark annotato con precision/recall/F1 | La valutazione quantitativa della qualità del classificatore resta da documentare |
| Nuova detection rate | `vt_manifest.csv`, `tmp/vt_results.jsonl` | Manifest di 239 file e 220 SHA-256; al controllo conclusivo erano iniziate le analisi completate | Campagna ancora parziale; non riportare gli elementi pendenti come zero detection |

### Dettagli che cambiano la descrizione scientifica

- La parte simbolica non è un classificatore basato soltanto su esecuzione simbolica: combina CFGFast, istruzioni osservate, stringhe e altre euristiche. Un indirizzo non osservato non è per questo dato, né codice irraggiungibile dimostrato. Nei sei report `*symbolic_coverage.json` alla radice, lo stato è `incomplete`.
- Identificazione ed estrazione sono operazioni diverse. L'LLM propone intervalli; il codice deterministico verifica i riferimenti e gestisce la riscrittura. Il risultato della pipeline dipende anche da questi filtri.
- I due metodi di classificazione sono percorsi alternativi che riutilizzano parte dell'infrastruttura. Non descriverli come due passaggi obbligatori consecutivi.
- Il morphing LLM implementa quattro famiglie già disponibili nel motore. PII, `-ip` e wrapping non sono delegati al modello nel percorso esaminato.
- Wrapping è disponibile per x64. Non estendere automaticamente i suoi risultati a x86.
- `pii_dispatcher_v2` e `pii_permute_instructions` sono percorsi distinti: una revisione della PII originaria e la permutazione esplicita delle singole istruzioni non devono apparire come la stessa configurazione.

## 3. Indice proposto

Un'unica metodologia sperimentale e un'unica sezione risultati consentono di confrontare le evidenze senza ripetere dataset, metriche e limiti in ogni capitolo.

```latex
\section{Introduction}
\subsection{Motivation and Research Questions}
\subsection{Contributions and Relationship to the Conference Paper}

\section{Background and Related Work}
\subsection{Binary Rewriting and Metamorphic Transformations}
\subsection{Code--Data Identification in Raw Binaries}
\subsection{LLMs for Assembly Analysis and Transformation}
\subsection{Overlapping Instructions and Assembly Wrapping}

\section{Zone Architecture and Conference Baseline}
\subsection{Scope and Binary Representation}
\subsection{Native Transformations and PII}
\subsection{Extended Architecture}

\section{Code--Data Identification and Data-Preserving Rewriting}
\subsection{Problem Definition and Classification Outputs}
\subsection{Symbolic and Heuristic Identification}
\subsection{LLM-Based Identification}
\subsection{Shared Data Handling and Validation}
\subsection{Uncertainty and Unsupported Cases}

\section{Extended Transformation Methods}
\subsection{LLM-Assisted Transformation}
\subsection{Zero-Shot and Two-Shot Conditions}
\subsection{Validation and Retry Policy}
\subsection{Assembly Wrapping: Integration of an Existing Technique}

\section{Experimental Design}
\subsection{Research Questions, Corpora, and Software Versions}
\subsection{Code--Data Reference Annotations}
\subsection{Build and Functional Evaluation}
\subsection{Static-Scan Measurements}
\subsection{Similarity, Diversity, Size, Time, and Cost}
\subsection{Aggregation and Uncertainty}

\section{Results}
\subsection{Published Baseline}
\subsection{Code--Data Identification and Agreement}
\subsection{Functional Assessment of the Updated Engine}
\subsection{Assembly Wrapping}
\subsection{LLM Transformation: Zero-Shot versus Two-Shot}

\section{Discussion and Threats to Validity}
\subsection{Classification Errors and Functional Failures}
\subsection{Selection, Validation, and Measurement Bias}
\subsection{Generalizability and Defensive Interpretation}
\subsection{Reproducibility}

\section{Conclusions}
```

Le sottosezioni della metodologia possono essere `\paragraph` se risultano troppo brevi. Non serve che ogni voce occupi una pagina.

Domande di ricerca coerenti con questa struttura:

1. Quali regioni sono identificate come dati dai due approcci e con quale qualità rispetto ad annotazioni di riferimento?
2. Quali esiti funzionali sono osservati dopo la gestione dei dati e le trasformazioni, distinguendo architetture e popolazioni di test?
3. Che cosa mostrano gli esperimenti sull'integrazione di assembly wrapping, inclusi build non riusciti e casi non supportati?
4. Quali differenze si osservano tra 0 e 2 shot nel pilota LLM, considerando accettazione, funzionalità, similarità, diversità e costo?

## 4. Modifiche alla bozza attuale, punto per punto

| Parte attuale | Modifica consigliata |
|---|---|
| Titolo e abstract | Riscrivere attorno alle estensioni. Presentare i 102 payload come baseline storica, distinguendoli dalle popolazioni nuove. Inserire solo risultati nuovi verificati. |
| Introduction | Sostituire i placeholder rossi con contributi concreti. Motivare il problema code/data come collegamento fra il limite della conferenza e il lavoro nuovo. Aggiornare il paragrafo che descrive l'organizzazione. |
| Relationship / Extensions Beyond the Conference Paper | Unire i due paragrafi in una dichiarazione breve di continuità e differenze, seguita dai contributi. Conservare la citazione del lavoro precedente. |
| Background | Ridurre le spiegazioni generali e le tabelle elementari EQ/NOP. Aggiungere il contesto della classificazione code/data e le due diverse applicazioni dell'LLM. |
| Zone Architecture | Conservare una descrizione compatta del motore originale. Aggiungere uno schema dell'architettura estesa e distinguere classificazione, gestione dati, trasformazione e validazione. |
| PII e quattro listing storici | Riassumere, mantenendo un solo schema/listing rappresentativo; spostare i dettagli ripetuti nel supplemento, se consentito. La PII originaria è contributo della conferenza. |
| Algorithm 1 / Transformation Pipeline | Identificare il workflow come storico, oppure aggiungere uno schema concettuale aggiornato. Il solo percorso Capstone–morph–patch non descrive più le modalità nuove. |
| Published Experimental Baseline | Conservare come sottosezione dei risultati; non farne l'intero capitolo sperimentale. Specificare dati mancanti, duplicati e periodo delle scansioni. |
| Size and Statistical Measurements | Spostare le definizioni nella metodologia e i grafici nei risultati. Verificare la corrispondenza fra definizione testuale e implementazione effettiva. |
| Limitations | Portare il caso `calc.exe` all'inizio della nuova sezione code/data. Nella discussione distinguere limiti affrontati, parzialmente affrontati e residui. |
| Mitigations and Countermeasures | Mantenere breve e chiaramente distinto dalle osservazioni sperimentali. |
| Comparison with SGN | Ridurre a confronto storico nella baseline o nel related work. Le nuove estensioni non sono valutate da quel confronto. |
| Related Work | Integrare nel background oppure mantenere un capitolo unico organizzato per i nuovi temi. Attribuire correttamente assembly wrapping. |
| Conclusions | Riscrivere con le risposte alle domande di ricerca e i limiti dei nuovi studi pilota. |
| Credits | Completare corresponding author, dichiarazione di interessi e gli altri placeholder autoriali. |

Il paragrafo sulla conferenza serve a rendere trasparente la provenienza del materiale. Il commento rosso ha però ragione a chiedere subito che cosa sia nuovo: oggi i due paragrafi sono sbilanciati verso la baseline. Basta una frase iniziale sulla provenienza; lo spazio successivo va ai contributi verificati.

## 5. Risultati utilizzabili e formulazioni corrette

### 5.1 Campagna funzionale aggiornata

`working_rate_unified_tests.csv` e `new_test_report_5run.csv` confermano:

| Popolazione selezionata | Solo estrazione, due configurazioni | Quindici configurazioni di morphing |
|---|---:|---:|
| 13 payload x64 con basso working rate storico | 260/260 | 1564/1950 = 80,2% |
| 36 payload x86 con basso working rate storico | 340/360 = 94,4% | 699/2700 = 25,9% |
| Totale dei 49 selezionati | 600/620 = 96,8% | 2263/4650 = 48,7% |

Questi non sono risultati nuovi sull'intero corpus di 102 payload. Inoltre i protocolli non sono uniformi in tutte le campagne: x64 ha dieci varianti per configurazione, x86 cinque nella campagna nuova. Per MessageBox il criterio storico attendeva l'uscita del processo, mentre i nuovi controlli osservano il dialogo. Non attribuire tutta la differenza alla gestione dei dati: cambiano anche implementazione, dipendenze e misurazione.

### 5.2 Assembly wrapping

Deduplicando il manifest per caso pianificato risultano 260 casi: 200 binari costruiti e 60 fallimenti di generazione. Il CSV di esecuzione contiene 198 successi e due fallimenti.

| Condizione | Build | Successi funzionali / casi pianificati | Successi / build |
|---|---:|---:|---:|
| Wrapping | 100/130 | 100/130 = 76,9% | 100/100 |
| Wrapping con le altre trasformazioni della condizione full | 100/130 | 98/130 = 75,4% | 98/100 |
| Totale | 200/260 = 76,9% | 198/260 = 76,2% | 198/200 = 99,0% |

Scrivere soltanto “working rate 99%” nasconderebbe i casi non costruiti. La distinzione fra disponibilità dell'output e comportamento dell'output è un risultato centrale, non un dettaglio da eliminare.

Inoltre i 200 file costruiti hanno **197 SHA-256 distinti** nella fotografia esaminata. Semi diversi non garantiscono output diversi.

### 5.3 Morphing LLM: 0 e 2 shot

Sono presenti 24 output finali: quattro tecniche × due condizioni di prompting × tre repliche, tutti sul solo `windows_x64_messagebox`. Il CSV registra 24 dialoghi osservati su 24 output. I file rappresentano **19 SHA-256 distinti** complessivi.

Questo è un pilota, non una validazione generalizzata su x64/x86. Inoltre:

- I 24 record statistici finali comprendono 27 tentativi/chiamate API.
- Il log conserva anche una precedente esecuzione IBP 0-shot fallita dopo tre tentativi, poi ripetuta. Le 24 uscite finali non sono il totale delle esecuzioni avviate: escludendo i semplici record di ripresa, risultano 25 esecuzioni avviate e 30 chiamate API.
- Il verificatore del dialogo partecipa già alla selezione degli output accettati. Il successivo 24/24 va presentato come esito degli output selezionati dalla pipeline; non dimostra il successo al primo tentativo né una verifica semantica indipendente.
- “0-shot” indica la richiesta iniziale senza esempi. Nei tentativi successivi il modello riceve l'errore e la risposta precedente: indicare il feedback anche nella descrizione della condizione 0-shot.
- Il batch usa repliche numerate e non passa un seed al servizio LLM. Non chiamarle “semi indipendenti” del modello.
- L'identificatore registrato è `deepseek-flash`. Il campo `model_version` è ottenuto da una tabella locale in `llm_stats.py`, non costituisce da solo una conferma della versione effettiva restituita dal provider.
- I costi nei JSON sono stime basate sulle tariffe codificate. Il costo dei 24 record finali è circa $0,506; includendo l'esecuzione fallita conservata nel log, circa $0,585. Dichiarare il criterio contabile.

Con tre repliche per cella e un solo input non sostenere una superiorità generale del 2-shot. Riportare differenze osservate, tentativi, tempi, output unici e limiti del campione.

### 5.4 Classificazione LLM dei dati

Il CSV contiene 15 output funzionanti su quattro payload distinti: MessageBox e custom reverse HTTP, ciascuno x64/x86. La quinta condizione aggiunge EQ al MessageBox x64. Il batch non imposta 0 e 2 shot per questa campagna: usa il default del percorso esaminato, pari a un esempio.

Le tre ripetizioni per condizione non sono quindici payload indipendenti; i 15 file corrispondono a cinque SHA-256. La concordanza degli output con l'estrazione simbolica riportata in `NEW_TESTS_REPORT.md` sostiene l'accordo della pipeline nei casi esaminati. Non dimostra l'accuratezza del classificatore, né che tutti gli intervalli grezzi proposti dai due metodi coincidano: i filtri successivi possono eliminare differenze.

### 5.5 Detection rate: stato e definizione

All'inizio della lettura `tmp/vt_results.jsonl` registrava upload in avanzamento e nessun record di analisi completata. Al controllo conclusivo tutti i 220 hash avevano un record di upload e tre avevano anche un record di analisi completata: la campagna era ancora parziale. `NEW_TESTS_REPORT.md`, che afferma che l'invio non è partito, è già superato da questo log. Il manifest associa 239 file a 220 hash unici. Queste quantità descrivono la fotografia osservata, non lo stato definitivo del processo esterno.

C'è anche un'incompatibilità di definizione:

- Il manoscritto definisce detection rate come frazione di motori con verdetto malicious per file, poi aggregata.
- `tmp/build_vt_report.py` chiama detection rate la frazione di file con almeno un verdetto malicious.

Sono due quantità diverse. Dare nomi distinti, esplicitare denominatori, motori che non supportano il formato, errori e analisi pendenti. Lo script assegna uno zero numerico quando non esistono completamenti: nelle tabelle del paper quel caso deve comparire come **non disponibile / pending**, non come 0% misurato.

La deduplicazione del report attuale è globale e attribuisce un hash soltanto al primo gruppo incontrato. Per gruppi con output identici questo può eliminare osservazioni da condizioni successive. Nella rendicontazione distinguere la scansione unica per hash dall'appartenenza dello stesso output a più condizioni sperimentali.

## 6. Le due valutazioni da non confondere

### Qualità code/data

La correttezza della classificazione richiede annotazioni di riferimento indipendenti dal metodo valutato. Nel workspace non ho trovato una valutazione sistematica annotata con confusion matrix, precision, recall e F1. I test con risposte mock verificano il software, non le prestazioni del modello.

Per una sezione quantitativa presentare almeno:

- Unità di classificazione: byte o intervallo; definire “positivo” come dato.
- Precision, recall e F1 dei dati, con errori codice→dato esplicitati.
- Accordo degli intervalli con il riferimento e copertura delle parti lasciate incerte.
- Distinzione fra candidati grezzi, candidati accettati dai controlli e dati effettivamente estratti.
- Casi con analisi incompleta, tempo, cache e motivi di arresto.

Se queste annotazioni non sono disponibili alla submission, intitolare il risultato **case study / agreement and downstream functionality** e dichiarare che la valutazione della classificazione resta preliminare. Non riempire una tabella di accuratezza usando il metodo simbolico come verità di riferimento per l'LLM.

### Similarità della rappresentazione

`llm_payload.py`, righe 776–789 nella versione esaminata, calcola `difflib.SequenceMatcher` su sequenze di firme con mnemonico e operandi normalizzati. Non è la cosine similarity della bozza. Per NOP elimina preventivamente le istruzioni riconosciute come no-op: il valore 1,000 del report è quindi coerente con la definizione e non indica identità dei binari.

Anche la metrica storica richiede una verifica di provenienza: il `create_var.py` attuale calcola la cosine similarity su token di mnemonici **e operandi**, aggregando l'assembly del corpus per architettura/configurazione. La bozza descrive invece profili di opcode di un file e della sua variante. Non assumere che script attuale e grafico storico abbiano la stessa origine senza controllare gli artefatti.

Nel paper definire per ogni metrica rappresentazione, normalizzazione, coppia confrontata e aggregazione. Chiarire se il riferimento LLM è il payload originale oppure la rappresentazione dopo estrazione e canonicalizzazione. Similarità, unicità hash e successo funzionale rispondono a domande diverse; nessuna delle prime due dimostra equivalenza semantica.

## 7. Errori storici da correggere prima di riutilizzare i grafici

Ho ricontrollato il LaTeX incollato contro `test_report.txt` e `results.json`. Ci sono associazioni etichetta/valore incoerenti, particolarmente nella coda delle configurazioni.

Esempi del working rate x64:

| Configurazione | Valore nella figura incollata | Valore aggregato da `test_report.txt` |
|---|---:|---:|
| `eq_pii` | 66,8% | 216/377 = 57,3% |
| `eq_bcf` | 66,0% | 251/376 = 66,8% |
| `nop_pii` | 0,3% | 212/370 = 57,3% |
| `nop_bcf` | 66,3% | 1/375 = 0,3% |

Un esempio della detection x64: la figura assegna 0,80% a `eq_pii` e 0,00% a `eq_ibp`; le righe grezze associate a quelle tecniche danno rispettivamente zero e circa 0,50% usando il denominatore `total_scans` di ciascuna riga. Per la pubblicazione occorre fissare deduplicazione e regola di aggregazione prima di finalizzare i valori.

Altre verifiche necessarie:

- `results.json` contiene 15.021 record di mutazioni ma **15.020 percorsi file unici**. Il duplicato riguarda `windows_x64_custom_reverse_tcp_uuid_pii_6.bin`. I 102 originali e i 102 SGN sono in JSON separati; il vecchio piano li conteggia erroneamente dentro quei 15.021.
- Dieci varianti per cella è il disegno pianificato, non la disponibilità effettiva di tutte le celle: vari gruppi hanno output mancanti.
- Le scansioni delle mutazioni vanno da aprile a settembre 2025; originali e SGN hanno record del 6 maggio 2025. Le campagne nuove sono del novembre 2026. Non attribuire automaticamente differenze fra periodi alla trasformazione.
- `create_image.py` usa un denominatore globale anziché leggere `total_scans` per ciascun record: ricostruire la provenienza della figura prima di copiarne la percentuale.
- Tenere la baseline pubblicata riconoscibile, presentando le eventuali correzioni in modo esplicito. Non sostituire silenziosamente valori storici con risultati di un motore nuovo e di una popolazione selezionata.

## 8. Tabelle e figure per la versione estesa

Suggerisco poche figure e tabelle con una funzione precisa:

1. Figura dell'architettura estesa, che mostri i due percorsi di identificazione e il livello condiviso di gestione dati.
2. Tabella dei corpus: numero di input distinti, architettura, criterio di selezione, condizioni, repliche e versione del codice.
3. Tabella code/data: risultati rispetto alle annotazioni, oppure casi e concordanza se resta uno studio pilota.
4. Tabella funzionale del motore aggiornato, separando x64/x86 e sola estrazione/morphing.
5. Tabella wrapping con tentativi pianificati, build, test superati e scansioni completate.
6. Tabella LLM 4×2: esiti iniziali/finali, tentativi, controllo funzionale, similarità definita, output unici, tempo e costo.
7. Tabella delle misure statiche, quando disponibili, con definizione uniforme e numero di hash completati.

Le tabelle di encodings elementari e i quattro listing PII occupano spazio che ora serve ai metodi e ai risultati nuovi. Le serie storiche possono essere consolidate e i dettagli ripetitivi spostati negli artefatti supplementari consentiti.

Budget orientativo: introduzione 2 pagine; background/related work 2; architettura 2; code/data 3; trasformazioni estese 3; metodologia 3; risultati 5; discussione 2; conclusioni 0,5; riferimenti circa 2. Totale circa 24,5 pagine, con margine per impaginazione e figure. È una previsione, non un conteggio: qui non sono presenti PDF compilato e progetto bibliografico completo.

## 9. Testo di partenza per i contributi

Questo testo è utilizzabile come base e rispecchia la portata attualmente documentata:

> This article extends our conference study of Zone with a data-handling layer for raw Windows payloads and an assessment of additional analysis and transformation methods. The extension integrates bounded symbolic exploration and heuristic code–data identification, introduces an alternative LLM-based identification path using shared deterministic data-handling routines, and adds LLM-assisted implementations of four transformation families. We study zero-shot and two-shot prompting in a controlled pilot and integrate assembly wrapping as an existing technique newly supported by Zone. The evaluation distinguishes build success, empirical functional checks, representation similarity, output diversity, and generation cost. Results on code–data identification are reported as preliminary case studies where independent reference annotations are unavailable.

Non aggiungerei qui una promessa di risultati di detection nuovi finché non ci sono analisi completate. Quando disponibili, inserirli con protocollo e denominatori espliciti.

Per la nota agli editor preparare due paragrafi: il primo elenca cosa deriva dalla conferenza; il secondo descrive metodi, implementazioni e risultati effettivamente aggiunti, indicando le sezioni. È utile come documento di accompagnamento, ma la mail incollata non contiene una richiesta esplicita di questa nota.

## 10. Vincoli editoriali e priorità

La mail ricevuta indica scadenza **18 novembre 2026**, nuova revisione non automaticamente accettata, uso del template Springer e compilazione della Licence to Publish. “Under 30” è una raccomandazione, non un limite rigido nella mail. CCIS è una serie di proceedings: evitare di chiamarla genericamente journal.

Il **30%** è indicato nella bozza e nel vecchio piano; la mail incollata rinvia ai requisiti dell'invito precedente ma non specifica quella percentuale. Serve la prima invitation email per confermare la soglia e il suo criterio. Non si può certificare il 30% contando pagine o paragrafi: vanno identificati i contributi sostanziali e confrontati con la versione pubblicata, che qui non è allegata separatamente.

Priorità consigliata per la revisione:

1. Fissare indice, contributi e provenienza dei dati; riscrivere abstract e introduzione.
2. Scrivere le sezioni dei metodi nuovi a partire dal codice, distinguendo identificazione, estrazione, trasformazione e validazione.
3. Inserire i risultati funzionali esistenti con denominatori, popolazioni e versioni corretti.
4. Correggere associazioni dei grafici e definizioni delle metriche; documentare i tentativi LLM falliti e la selezione degli output.
5. Decidere se la classificazione è una valutazione annotata o uno studio pilota; mantenere la descrizione coerente con le evidenze disponibili.
6. Completare le tabelle di scansione soltanto sui verdetti effettivamente disponibili, lasciando visibili i dati mancanti.
7. Finalizzare conclusioni, nota delle differenze e adempimenti autoriali; compilare e controllare il PDF nel progetto LaTeX completo.

Per la riproducibilità conservare hash degli input/output e della snapshot del motore, prompt effettivi, esempi, impostazioni, tentativi e versioni delle dipendenze. Il batch LLM usa `tmp/wrap_snapshot`, mentre il batch di classificazione richiama i file alla radice: la versione sperimentale non è automaticamente la versione corrente del repository.

## Fonti esterne verificate

- [Springer: Information for authors and editors](https://link.springer.com/series/558/information-for-authors-and-editors): pagina ufficiale applicabile anche a CCIS, con istruzioni e template.
- [Assembly wrapping: a technique for anti-disassembly, 8 giugno 2020](https://0x4ndr3.github.io/posts/assembly-wrapping-a-new-technique-for-anti-disassembly/): fonte dell'autore utile per attribuire il metodo; contiene anche una rettifica che ne riconosce antecedenti nel lavoro sulle overlapping instructions. L'integrazione in Zone è nuova rispetto alla baseline descritta; l'idea generale non va rivendicata come invenzione del paper esteso.
