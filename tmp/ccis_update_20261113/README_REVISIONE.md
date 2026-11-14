# Aggiornamento sperimentale - 13 novembre 2026, ore 21:20 CET

La revisione mantiene la struttura additiva e tutti i risultati della conferenza. I dati nuovi sono estratti dai file grezzi congelati in `evidence/sources/`, con hash in `evidence/SOURCES.json` e tabelle derivate CSV. Non sono state eseguite nuove chiamate LLM, scansioni o esecuzioni di payload per questa revisione.

## Che cosa e cambiato

- Il wrapping x86 e ora implementato e valutato: 18/18 run delle fixture benigne superano il buffer oracle; la campagna sui payload originali ha risultati separati, piu limitati.
- Benchmark benigno: 13 fixture, baseline 13/13; matrici native per versione; LLM x64 167/168 e x86 138/144. Ogni invocazione ammette una generazione, con tre invocazioni per cella e nessuna sostituzione dei fallimenti. Le tabelle includono similarita SequenceMatcher, unicita, tempo e costo.
- Classifier: sei fixture indipendenti, 18/18 chiamate LLM e 6/6 analisi simboliche esatte. Tre casi sono data-positive, tre senza dati. Questa evidenza non si estende automaticamente ai payload reali.
- Wrapping sul corpus originale: 306 tentativi; 243 build; 170 test funzionali superati. I 73 retest falliti non sono nuove varianti.
- Classificazione su 19 payload selezionati: entrambe le pipeline 17/19 test; 9/19 accordi degli intervalli confrontati, 16/19 identita finali. Non e una misura di accuratezza senza ground truth.
- VT precedente: 220 hash completati; la nuova tabella corregge il conteggio per appartenenza ai gruppi, conservando gli hash condivisi in ciascun gruppo. Le somme delle righe non sono il totale dell'unione.
- DeepSeek sul corpus originale e attivo separatamente: fotografia 30 celle completate su 816 pianificate, 11 build accettati e 19 fallimenti. Nessuna percentuale finale viene ricavata da questo parziale. Le 208 sottomissioni VT correnti non avevano verdetti completati alla fotografia.

## Dove continuare

`main.tex` conserva lo studio originale e include i moduli `sections/extension_*.tex`. Aggiornare `extension_results.tex` solo usando una nuova fotografia coerente e distinguendo versioni e campagne. Aggiornare contestualmente abstract, conclusioni e nota editor. Creare una nuova fotografia con SOURCES.json, conservando immutabile la precedente evidenza. I vecchi risultati non vanno sostituiti dai nuovi.

Il modello e identificato dal nome richiesto `deepseek-flash`; model_version nei client e una mappatura locale, non una conferma del provider. I costi sono stime tariffarie locali. I record di errori di rete possono non avere usage completo. Non sommare come repliche indipendenti le varianti uguali, i retest e le riprese di una cella.

Per compilare eseguire `build.ps1`. Le note blu di lavoro si nascondono con `\workingdraftfalse` solo dopo la loro risoluzione. Restano da completare corresponding author, disclosure degli interessi e controlli storici descritti in BASELINE_CHECKS.md. L'invito richiede almeno 30% di nuovo materiale sostanziale: i conteggi testuali non ne sono una certificazione.
