# Valutazione per revisione dei supervisor - 15 novembre 2026

## Giudizio

La bozza ha contenuto sufficiente e una motivazione scientifica comprensibile per una revisione dei supervisor. Il contributo più convincente è il collegamento tra il problema dei dati incorporati, la preparazione del codice e il recupero funzionale osservato. Le due funzioni dell'LLM sono ora distinte; i programmi controllati e il corpus originale forniscono evidenze complementari. Le campagne concluse rendono l'estensione sostanziale.

La versione attuale va presentata come bozza per commenti. Restano una riduzione di lunghezza, una migliore integrazione narrativa e una riconciliazione dei grafici storici. Questi punti non richiedono nuovi esperimenti per poter chiedere una prima revisione ai supervisor.

## Controlli sull'invito

| Requisito | Esito della verifica |
|---|---|
| Citare il paper conferenza e includerlo nei riferimenti | Soddisfatto: citazione nell'introduzione e riferimento bibliografico n. 4. Titolo, autori, anno, pagine e DOI coincidono con la scheda pubblica SCITEPRESS. |
| Almeno 30% di materiale nuovo | Sostanzialmente sostenibile: identificazione dati, gestione dei riferimenti, due ruoli LLM, integrazione wrapping e nuove valutazioni occupano all'incirca metà del corpo. Questa è una valutazione del contributo, non una certificazione ottenuta dal conteggio delle pagine. |
| Citazione nelle figure e tabelle riutilizzate | Tutte le 7 figure e le 6 tabelle del blocco storico contengono la citazione della conferenza; anche i 4 listing e l'algoritmo hanno attribuzione. L'attribuzione non certifica la corrispondenza dei dati rappresentati. |
| Nessun grande blocco copiato letteralmente | Verifica finale ancora aperta. Il PDF pubblicato non è stato recuperato integralmente dal sito dell'editore; la bozza preparatoria locale è già una rielaborazione e non è un sostituto del documento pubblicato per questo controllo. |
| Titolo, abstract e conclusioni diversi | Titolo e abstract sono diversi da quelli pubblicati verificabili sulla scheda SCITEPRESS. Le conclusioni attuali sono incentrate sulle estensioni; il confronto letterale con le conclusioni pubblicate rientra nel controllo ancora aperto. |
| Due paragrafi sulle differenze | Preparata una proposta aggiornata in `EDITOR_DIFFERENCES_REVIEW_20261115.txt`, centrata sui contributi rispetto alla conferenza. |

Fonte editoriale verificata: https://www.scitepress.org/PublishedPapers/2026/151706/

Il testo dell'invito qui fornito non specifica il limite di pagine. Ai fini di questa revisione si assume il vincolo indicato dall'autore: massimo 30 pagine. La data del 12 settembre 2026 riguarda la scelta dell'opzione di post-publication, non la consegna del manoscritto esteso.

## Riscontri concreti da segnalare ai supervisor

1. Il PDF ha 34 pagine; la bibliografia comincia a pagina 32. Il limite di 30 non è ancora rispettato.
2. La prima sezione dedicata ai metodi aggiunti (sezione 8) inizia a pagina 17. Il lettore incontra quasi tutto il lavoro storico prima della spiegazione delle novità.
3. La Fig. 3 a pagina 11 e la colonna Historical della Tabella 12 a pagina 30 non coincidono. Per esempio, EQ+PII x64 compare come 66,8% nella figura e 57,3% nella tabella. Occorre distinguere un'eventuale correzione del grafico dalla rianalisi dei dati, senza cambiare silenziosamente il riferimento storico.
4. La nota blu a pagina 10 segnala già verifiche aperte su associazioni categoria/valore e provenienza della similarità. La nota può essere utile nella bozza per i supervisor; non deve essere soltanto nascosta nella versione finale, lasciando il problema irrisolto.
5. La dichiarazione degli interessi a pagina 32 è ancora un campo da completare da parte degli autori.

## Struttura suggerita

1. Introduction: problema, relazione con la conferenza e contributi aggiunti.
2. Background and Related Work: concetti necessari e posizionamento.
3. Zone Overview: architettura di base e spiegazione compatta di PII.
4. Extended Methods: identificazione e conservazione dati, trasformazione LLM, wrapping.
5. Experimental Design: popolazioni, versioni, condizioni e definizioni comuni; distinguere i protocolli quando differiscono.
6. Results: baseline storica sintetica, identificazione dati, test controllati, risultati sul corpus, recupero funzionale e detection.
7. Discussion and Limitations: interpretazione unitaria, con limiti del vecchio e del nuovo studio attribuiti alle rispettive evidenze.
8. Conclusions.

La struttura attuale è utilizzabile per una revisione interna e rende esplicita la provenienza. Per la versione finale, la struttura integrata mette prima la domanda di ricerca e permette di confrontare i risultati senza ripercorrere un intero articolo precedente. I risultati storici devono comunque conservare attribuzione, periodo e denominatori propri.

## Riduzione proposta

| Intervento | Risparmio stimato |
|---|---:|
| Accorciare il background e consolidare gli esempi di trasformazioni già pubblicati | 1-1,5 pagine |
| Conservare lo schema e la spiegazione di PII, rinviando al paper originale per listing e algoritmo completi | 1-1,5 pagine |
| Riassumere le misure storiche di dimensione, entropia e similarità e ridurre le figure ripetute | 1-1,5 pagine |
| Unificare ripetizioni fra limiti, confronto SGN, discussione e conclusioni | 0,5-1 pagina |

L'obiettivo ragionevole è 29-30 pagine comprese bibliografia e dichiarazioni. Le stime vanno confermate dopo ricompilazione: non sono il conteggio di una versione già ridotta. Non occorre ridurre font o margini né tagliare le tabelle che sostengono i risultati nuovi. L'invito richiede di citare gli oggetti riutilizzati, non di ripubblicarli tutti.

## Portata del controllo

Controllati testo estratto, struttura LaTeX, didascalie, riferimenti e pagine renderizzate dei blocchi storici e del passaggio alle estensioni. Consultata la scheda pubblica del paper conferenza. Nessun nuovo esperimento, nessun cambiamento al motore e nessuna modifica al manoscritto o al PDF in questo turno. I due nuovi documenti sono materiali di revisione.
