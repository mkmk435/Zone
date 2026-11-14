# Bozza CCIS estesa - 13 novembre 2026

Aprire `main.pdf` per la lettura. Il sorgente principale e `main.tex`; i capitoli sono separati in `sections/`. `figures/` contiene la figura PII ripresa dalla conferenza con attribuzione.

## Stato della bozza

- Titolo, abstract, introduzione e conclusioni riscritti.
- Aggiunte sezioni complete su identificazione code/data, gestione dei dati, morphing LLM, assembly wrapping e metodologia.
- Il wrapping x86 e dichiarato in sviluppo: completare e validare le righe x86 solo quando la campagna e fissata.
- Le celle `pending` non sono risultati. Nessun numero nuovo dei test in corso e stato congelato nel paper.
- Il testo storico e sintetizzato; le vecchie serie grafiche con associazioni dubbie sono conservate nel backup, ma escluse da questa bozza.
- `EDITOR_DIFFERENCES.txt` contiene i due paragrafi in inglese richiesti dagli editor; aggiornarne l'ultima frase prima dell'invio.

## Dove aggiungere i risultati

1. `sections/07_methodology.tex`: fissare campioni, repliche, versioni, parametri, modello, oracolo funzionale, definizione dei denominatori VT e aggregazione.
2. `sections/08_results.tex`: riempire le tabelle e aggiungere il commento supportato dai risultati. Le tabelle sono un modello modificabile, non vincolano il disegno finale.
3. `sections/09_discussion.tex`: collegare i limiti alle osservazioni effettive.
4. `sections/10_conclusions.tex` e abstract in `main.tex`: inserire insieme i risultati principali.
5. Dopo il controllo finale usare `\workingdraftfalse` in `main.tex` per nascondere le note blu. Prima verificare che non rimangano celle pending o in development non volute.

La metrica SequenceMatcher non e cosine similarity; entrambe hanno una definizione distinta nel testo. La classificazione code/data richiede annotazioni indipendenti per precision/recall/F1; in loro assenza riportare concordanza e casi di studio. Per working rate mantenere sia W/N sia W/B. Non considerare pending scans come zero detection.

## Requisiti dell'invito

La conferenza e citata e presente in bibliografia; il materiale visivo storico mantenuto ha citazione; i testi sono riscritti e il nuovo materiale metodologico e separato. La soglia del 30% riguarda nuovo contenuto sostanziale: `REVISION_AUDIT.json` documenta i conteggi editoriali indicativi, che non costituiscono una certificazione del requisito. Il contributo sperimentale va completato prima della submission. Mancano ancora corresponding author e dichiarazione degli interessi degli autori.

## Compilazione

Eseguire `build.ps1` con PowerShell. Il progetto rimane LaTeX LNCS standard: in un ambiente TeX Live/MiKTeX si puo usare anche latexmk oppure pdflatex, bibtex, pdflatex, pdflatex. Il build.ps1 usa Tectonic se disponibile o scarica la release ufficiale fissata in `.tools/` quando manca un altro compilatore. Il primo avvio Tectonic richiede rete per i pacchetti TeX.

La copia dei sorgenti prima della revisione e nel backup con data all'interno del progetto. Non cancellarla finche il confronto editoriale non e concluso.
