# Versione corrente - 16 novembre 2026

Il manoscritto corrente è `main.pdf`, distribuito come
`../../output/pdf/zone_revisione_20261116.pdf`: 29 pagine, bibliografia inclusa.
Related Work e Conclusions sono ampliati; la Discussion separata è assorbita
nelle Conclusions. L'introduzione dichiara esplicitamente l'estensione e
rimanda alle sezioni dei singoli contributi. La nota in prima pagina è rimossa.
La dichiarazione di assenza di conflitti è confermata dall'autore e compilata.

Le 13 tabelle restano numericamente invariate. La figura concettuale include
ora uscite Stop. La sezione 12.4 aggiunge test appaiati sui risultati salvati,
documentati nel supplemento. Nessun nuovo esperimento è stato eseguito.
Future Work da discutere: l'autore ha esplicitamente chiesto di non inserirlo
ancora. Resta margine entro il limite di 30 pagine.

Verifiche in `qa_structure_20261116/` e `STRUCTURE_REVISION_20261116.json`.
Versione precedente in `before_structure_revision_20261116/`.
Materiali e sorgenti di consegna in
`../../output/submission/zone_editorial_20261116/`.

---

# Revisione editoriale corrente - 15 novembre 2026

Il PDF corrente è `main.pdf`, distribuito anche come
`../../output/pdf/zone_revisione_30_pagine_editoriale.pdf`: 30 pagine,
bibliografia inclusa. La precedente consegna da 30 pagine resta conservata.

Sono state aggiunte la nota di extended version in prima pagina e la
dichiarazione di disponibilità dei materiali, chiarite le due aggregazioni
della Tabella 12 e precisati alias del modello e versione del test IBP.
Il grafico storico di detection è stato ricalcolato dai record salvati con
etichette corrette; la similarità è descritta come confronto fra vettori
di frequenze dei mnemonici aggregati per corpus. La nota di lavoro è rimossa.
I corpi delle 13 tabelle sono invariati. Tabella 12: pagina 26; Tabella 13:
pagina 27. Le sezioni nuove iniziano a pagina 14. Font e margini sono invariati.

Restano da confermare da parte degli autori la dichiarazione degli interessi
e la copertura del riuso. I materiali pronti per queste verifiche, i due
paragrafi per l'editor, la risposta IBP e il supplemento numerico S1 sono in
`../../output/submission/zone_editorial_20261115/` e nel pacchetto ZIP di consegna.
Non sono stati inviati messaggi, eseguiti nuovi esperimenti o modificati motori.

Verifiche: `qa_editorial_20261115/qa_report.json` e
`evidence/editorial_20261115/EDITORIAL_AUDIT.json`. La copia precedente dei
sorgenti è in `before_editorial_corrections_20261115/`.

---

# Versione corrente da 30 pagine - 15 novembre 2026

Il manoscritto corrente è `main.pdf`, distribuito anche come
`../../output/pdf/zone_revisione_30_pagine.pdf`: 30 pagine, bibliografia
compresa, con font e margini invariati. La versione precedente da 34 pagine
è conservata in `before_30page_revision_20261115/` e nel precedente PDF
di consegna.

La riduzione interessa introduzione e blocco storico, identificazione dati,
trasformazione LLM, metodologia, risultati e discussione. Sono conservati
gli esempi necessari a spiegare intervalli, feedback e integrità, la
temperatura richiesta, i protocolli e tutti i dati delle 13 tabelle. La
spiegazione del wrapping rimane quella appena chiarita con l'autore.

I working rate sono consolidati nella Tabella 12 a pagina 25: il grafico
storico duplicato con associazioni incoerenti è archiviato nel supplemento
di revisione. Il testo e la didascalia dichiarano che i valori storici della
tabella sono ricavati dai registri conservati. La Tabella 13 è a pagina 26.
La sezione 8 ora inizia a pagina 14; la numerazione delle sezioni è invariata.

Verifiche e hash sono in `COMPACT_REVISION_AUDIT_20261115.json`; conteggi
comparativi e grafico archiviato sono in `evidence/compact_20261115/`.
Restano le verifiche storiche esplicitate nella nota di lavoro e la
dichiarazione degli interessi da completare dagli autori. Nessun nuovo
esperimento o intervento sui motori è stato eseguito.

# Revisione precedente del 15 novembre 2026

Il PDF di quella revisione contiene 34 pagine, distribuito come
`../../output/pdf/zone_revisione_20261115.pdf`. Le risposte in italiano alle
ultime osservazioni sono in `RISPOSTE_20261115.md`.

La nuova Tabella 12 (pagina 30) riporta i working rate storici e aggiornati
per le 15 configurazioni, con la media finale. L'aggiornamento combina i
risultati nuovi sui 49 input ritestati con quelli storici sugli altri,
conservando i pesi originali: non rappresenta una nuova esecuzione completa.
La figura prima/dopo della revisione precedente non compare più nel testo;
la figura storica rimane, con un rimando alla tabella nuova.

La Tabella 13 (pagina 31) usa il detection rate storico e comprende la
campagna LLM sui 102 input, oltre al sottoinsieme degli output funzionanti.
Il report vuoto è conservato come dato mancante nelle note supplementari.
Non sono state eseguite nuove scansioni. Il benchmark controllato è stato
semplificato; i dettagli precedenti e la vecchia sezione 12.7 sono conservati
in `evidence/followup_20261115/`.

Il testo chiarisce regole di riconoscimento, richieste di correzione,
controlli di integrità, limiti implementativi e separazione fra codice e dati.
Riporta la temperatura richiesta di 0,2 e mantiene distinte le misure di
similarità. I motori non sono stati modificati; il risultato IBP x86 rimane
quello della versione testata.

Le verifiche di questa revisione sono in `FOLLOWUP_REVISION_AUDIT_20261115.json`;
la versione precedente è in `before_followup_20261115/`. I paragrafi seguenti
descrivono le revisioni precedenti e i relativi artefatti.

# Revisione del 14 novembre 2026

Le sezioni nuove sono state riscritte integralmente per spiegare il problema,
la tecnica, gli ingressi/uscite e poi la valutazione. La baseline storica e i
suoi oggetti LaTeX sono conservati. Sono aggiornati anche titolo, abstract,
contributi, organizzazione del paper e conclusioni.

## Contenuti

- Identificazione codice/dati: definizioni, esempio benigno, due classificatori
  alternativi, distinzione fra proposta, accettazione e gestione dei riferimenti.
- Trasformazione LLM: ruolo del modello distinto dalla classificazione; listing
  preparato, zero/two-shot, validazione e test esterno.
- Wrapping: spiegazione del meccanismo e delle due interpretazioni degli stessi
  byte, figura concettuale, integrazione x64/x86 e limiti.
- Metodologia, risultati e discussione riscritti; nuovo schema del flusso.
- Risultati completi: 816 celle LLM, 350 build, 275 test superati;
  wrapping 243/306 build e 170 test superati; scansioni correnti completate.

## Correzioni rispetto al riepilogo della campagna

L'audit diretto dei log trova 830 record di esecuzione per 816 celle, con
14 riprese di celle fallite (ancora fallite), 4 record con generazioni multiple,
835 chiamate API registrate e un record privo di usage. Due build accettati
hanno richiesto una seconda generazione. Non e quindi un esperimento uniforme
al primo tentativo. Il costo registrato completo e $19.6258; $19.2700 e il
sottoinsieme di un record rappresentativo per cella.

Il manifest VT ha 612 file e 549 hash con record completed, ma un report LLM
BCF/0 ha tutte le statistiche a zero. Le scansioni valutabili sono 548, di cui
322 LLM: 221/322 rilevati (68.6%), non 221/323 negativizzando il report vuoto.
Il wrapping ha 0/207 hash con risposte malicious. Le risposte unsupported,
timeout e failure rimangono esplicite. I 75 file LLM non funzionanti
corrispondono a 60 hash distinti (59 con report valutabile).

## Provenienza e riproducibilita

L'evidenza precedente rimane in evidence/. La nuova fotografia immutabile e
in evidence/completed_20261114/, con SOURCES.json, SUMMARY.json, CSV derivati
e copie dei log e dei sorgenti pertinenti. Le statistiche si ricavano da file
esistenti: nessuna generazione, esecuzione di payload o scansione e stata
avviata per questa revisione. La verifica di compilazione e impaginazione e
registrata in REVISION_AUDIT.json.

Per ricompilare: eseguire build.ps1 nella cartella CCIS.

Restano le verifiche storiche documentate in BASELINE_CHECKS.md e i campi
autoriali da completare prima della submission, inclusa la disclosure degli
interessi. Non sono stati inventati dati o dichiarazioni degli autori.

Aggiornamento di chiarezza richiesto dall'autore

La revisione del 14 novembre integra una figura prima/dopo sui 49 payload originali
prima problematici, ricavata dai due report di esecuzione e verificata contro
il CSV consolidato. Conteggi e descrizione in evidence/clarity_revision/.
Il testo distingue i 13 programmi controllati dai 13 payload x64 selezionati,
spiega celle, shot, feedback, listing preparato, predicted/reference e le due
misure di detection. Le sigle delle versioni e la contabilità dettagliata sono
spostate nelle note dell'artefatto; la differenza di versione rilevante resta
segnalata nella metodologia. I limiti di equivalenza formale sono concentrati
nella discussione, mentre abstract e conclusioni evidenziano il recupero.

SPIEGAZIONE_ITALIANA.md risponde punto per punto alle domande dell'autore.
Quel PDF contiene 36 pagine; la figura è Fig. 10 a pagina 30.
Le sezioni 12.3 (wrapping) e 12.4 (LLM originale) mantengono la numerazione;
il confronto prima/dopo è in 12.5. La versione precedente è conservata in
before_clarity_revision/. Questa revisione usa solo risultati già registrati.
