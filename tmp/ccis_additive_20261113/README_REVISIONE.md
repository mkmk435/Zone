# Revisione CCIS additiva - 13 novembre 2026

Questa versione estende il manoscritto precedente conservandone il corpo scientifico e tutti i risultati dettagliati. Il PDF principale e `main.pdf`.

## Materiale originale mantenuto

`main.tex` conserva background, tecniche, architettura, PII e relativi listing, algoritmo, protocollo originale, detection rate, working rate, dimensione, entropia assembly/byte, cosine similarity, limiti, confronto SGN e related work. Sono presenti tutte le sette figure, sei tabelle, quattro listing e l'algoritmo della bozza originale, con citazione della fonte. I numeri storici non sono stati sostituiti con quelli dei test nuovi.

Titolo, abstract, contributi introduttivi e conclusioni sono aggiornati per descrivere studio originale ed estensione. Il requisito di evitare grandi blocchi copiati dalla conferenza resta da verificare rispetto al testo effettivamente pubblicato: qui la fonte mantenuta e la bozza CCIS preparatoria, non un confronto certificato con il full text della conferenza.

## Nuove sezioni attive

- `sections/extension_code_data.tex`: identificazione simbolica/euristica e LLM, gestione dei dati.
- `sections/extension_llm.tex`: morphing LLM, 0/2 shot, controlli e feedback.
- `sections/extension_wrapping.tex`: integrazione del metodo esistente e x86 in sviluppo.
- `sections/extension_methodology.tex`: metriche e protocollo aggiuntivi.
- `sections/extension_results.tex`: tabelle da completare e commento dei nuovi risultati.

L'ordine preserva prima lo studio originale e aggiunge poi le estensioni motivate dai suoi limiti. I vecchi moduli numerati 01--10 della revisione riorganizzata non sono piu inclusi da main.tex; la copia di quella revisione resta nel backup. Non usarli per modificare questa versione.

## Completamento

1. Inserire dati e interpretazioni dei nuovi esperimenti in `extension_results.tex` e fissare i metadati in `extension_methodology.tex`.
2. Tenere separati studio originale e nuove campagne, specialmente se campioni, harness o versioni differiscono.
3. Aggiornare insieme abstract, conclusioni e i due paragrafi di `EDITOR_DIFFERENCES.txt`.
4. Completare corresponding author e dichiarazione di interessi.
5. Dopo aver risolto tutte le note, impostare `\workingdraftfalse` in main.tex. Le celle pending vanno completate o dichiarate non disponibili; nascondere le note non le compila.

`BASELINE_CHECKS.md` registra controlli aperti sulle associazioni delle vecchie figure e sulla provenienza della similarita. I risultati non sono stati eliminati per questi controlli. `REVISION_AUDIT.json` documenta la conservazione degli oggetti originali e il nuovo testo indicativo. Il 30% richiede contenuto scientifico sostanziale e non e certificato dal semplice conteggio delle parole; i risultati aggiuntivi sono ancora da completare.

## Compilazione

Eseguire `build.ps1` con PowerShell. Il progetto mantiene la classe LNCS e la bibliografia originale, ampliata con i riferimenti dei nuovi metodi. Gli strumenti e la cache TeX locali sono in `.tools/`.
