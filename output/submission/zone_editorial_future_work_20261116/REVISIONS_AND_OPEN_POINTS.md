# Revisione del 16 novembre 2026

## Correzioni applicate

- Related Work ampliato e articolato per confronto con metodi tradizionali,
  sistemi basati su compilatore, studi LLM e analisi difensiva.
- Discussion assorbita nelle Conclusions: interpretazione dei risultati e
  limiti mantenuti, con meno ripetizioni. Ora sono le sezioni 13 e 14.
- Testo storico abbreviato di circa 600 parole; dati delle 13 tabelle,
  sette figure, quattro listati e algoritmo conservati. La sola figura
  modificata è il diagramma concettuale, con uscite Stop esplicite.
- Introduzione: "In this article, we extend our SECRYPT 2026 paper [4]",
  riferimenti alle sezioni nella lista dei contributi e definizione anticipata
  di working. Eliminata la nota ridondante con il DOI in prima pagina.
- Perimetro dello studio raccolto nell'introduzione e richiamato nelle
  sezioni successive. Conservate le precisazioni specifiche sui denominatori.
- Conflitti: "The authors have no competing interests to declare", sulla
  base della conferma dell'autore ricevuta il 16 novembre.
- Verificate tutte le 16 righe della Tabella 11 contro le 816 celle salvate.
- Aggiunto confronto appaiato zero/two-shot: 118 coppie con entrambi gli
  esiti positivi, 21 solo zero-shot, 18 solo two-shot, 251 nessuno. McNemar
  esatto bilaterale p=0.749259; controllo per input p=0.752178. Il secondo
  mantiene insieme le quattro tecniche dello stesso input. Analisi esplorative,
  con assunzioni esplicite e senza affermare equivalenza.

## Osservazioni della valutazione da precisare

Il DOI è confermato nella scheda pubblicata da SCITEPRESS. Il nome del
dipartimento e l'indirizzo coincidono già con le pagine ufficiali UniPG;
non occorre correggerli. Le fonti sono elencate in VERIFIED_SOURCES.json.

La presenza di oggetti storici citati non dimostra da sola una quota nuova
insufficiente: l'invito fornito richiede almeno il 30% di materiale nuovo e
attribuzione degli oggetti ripresi. La distinzione dei contributi è ora
esplicita. Il precedente confronto del testo con l'originale aveva già
rilevato una riscrittura della prosa. La stima per estensione in pagine è
indicativa e non sostituisce il giudizio editoriale sulla novità.

Sul seed è pronta una risposta fattuale. Il supporto del provider non va
presunto e non è stata inventata una motivazione retrospettiva. Restano
distinti impostazioni richieste al client e comportamento effettivo del server.

## Future Work inserito dopo la conferma dell'autore

La sezione 14.1 ora presenta le due direzioni concordate: supporto ai file
PE e ampliamento della validazione funzionale. Il supporto PE è collegato
esplicitamente all'aumento della varietà di programmi testabili, a condizioni
di esecuzione più rappresentative e alla valutazione dell'utilità pratica
del tool su applicazioni complete. Le direzioni sono presentate come lavoro
futuro, senza attribuire alla versione attuale risultati non misurati.

Il PDF comprende 30 pagine, bibliografia inclusa. Dati, figure e risultati
sperimentali sono invariati rispetto alla precedente versione da 29 pagine.

Resta da verificare la copertura del riuso nell'accordo originale o ottenere
conferma dal publisher. La richiesta predisposta non è stata inviata.
Non sono stati eseguiti nuovi payload, chiamate LLM o scansioni: l'aggiunta
statistica usa esclusivamente i risultati già registrati.
