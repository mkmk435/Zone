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
