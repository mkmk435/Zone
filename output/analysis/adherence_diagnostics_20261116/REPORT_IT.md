# Controllo preliminare di aderenza: zero-shot e two-shot

Analisi retrospettiva delle diagnostiche salvate. Nessuna nuova generazione, esecuzione o scansione. Questo controllo non misura la quota totale di trasformazioni applicate correttamente né la loro intensità.

## Programmi benigni: controllo EQ

Sono disponibili 312 richieste su 13 programmi benigni, 4 tecniche, 2 condizioni e 3 repliche. Per EQ sono 39 richieste per condizione; tutte hanno prodotto un output. Il warning esplicito di sequenza di firme delle istruzioni invariata compare in 3/39 casi zero-shot (7,7%) e 2/39 two-shot (5,1%). Le firme sono una rappresentazione normalizzata: il warning non afferma identità binaria. Le altre 36/39 e 37/39 richieste non sono automaticamente trasformazioni EQ corrette: assenza del warning e cambiamento della sequenza non costituiscono una verifica completa della tecnica. Questi risultati riguardano i programmi benigni, non i 102 payload principali.

## Corpus principale: 816 celle

Ogni riga comprende 102 input. I casi segnalati possono avere anche altri errori. Le diagnostiche non coprono necessariamente tutti gli output: disassemblaggio o assemblaggio possono fallire prima dei controlli. Per questo non si può dividere il numero di warning per 102 e chiamare il complemento tasso di aderenza.

| Tecnica | Shot | Costruiti / 102 | Diagnostiche esplicite di mancata applicazione |
|---|---:|---:|---:|
| EQ | 0 | 41 | 0 |
| EQ | 2 | 42 | 0 |
| NOP | 0 | 46 | 1 |
| NOP | 2 | 41 | 1 |
| BCF | 0 | 46 | 1 |
| BCF | 2 | 42 | 3 |
| IBP | 0 | 45 | 1 |
| IBP | 2 | 47 | 0 |

Tutti gli 87 output NOP costruiti hanno similarità 1, perché il confronto esclude le istruzioni riconosciute come NOP-like. Non significa che siano invariati. Nessuno degli 83 output EQ costruiti ha similarità 1; anche questo non prova che tutte le sostituzioni richieste siano state effettuate.

## Interpretazione

I dati disponibili non dimostrano che zero-shot applichi la tecnica meno spesso di two-shot. Non escludono però una differenza di intensità o qualità della trasformazione. Il precedente confronto del working rate risponde a una domanda diversa: un output può funzionare pur applicando poco la tecnica. La frase sul paper deve quindi riferirsi al working rate, non alla qualità complessiva delle trasformazioni.

Una misura completa richiede criteri di aderenza distinti per tecnica e annotazioni degli output rispetto alla rappresentazione effettivamente inviata al modello, separando applicazione, intensità, validità e casi non valutabili. Per una verifica controllata su programmi benigni, le annotazioni andrebbero effettuate senza conoscere la condizione di prompting; i risultati resterebbero limitati a quel campione.

Numeri e hash dei file consultati: `results.json`. Il manoscritto non è stato modificato.
