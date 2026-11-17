Questa guida spiega gli esperimenti presenti nei file e le modifiche editoriali del 14 novembre 2026. La revisione ricalcola statistiche da risultati già registrati: non rappresenta una nuova esecuzione degli esperimenti.

**1. Il risultato da mettere in evidenza è il recupero del funzionamento.**

Dire «non c'è una dimostrazione formale di equivalenza per ogni possibile esecuzione» non significa dire «il comportamento non viene preservato». I test verificano un comportamento concreto e, quando riescono, documentano che quel comportamento è stato conservato. Nel paper basta definire il criterio una volta e poi parlare normalmente di test superati e working rate.

Il confronto sui payload prima problematici è sostanziale:

| Insieme ritestato | Storico | Pipeline aggiornata |
|---|---:|---:|
| 13 payload originali x64 | 23/1.941 = 1,2% | 1.564/1.950 = 80,2% |
| 36 payload originali x86 | 772/5.195 = 14,9% | 699/2.700 = 25,9% |

La figura nuova confronta gli stessi 49 input nelle quindici configurazioni native. Nel nuovo test ci sono dieci varianti per configurazione/input x64 e cinque per x86. I vecchi conteggi sono quelli disponibili nei registri storici. Il grafico non include i controlli con sola preparazione dei dati.

Questi sono risultati del sistema aggiornato nel suo insieme. Per MessageBox è stato migliorato anche il riconoscimento della finestra da parte del test. Il miglioramento x64 rimane netto anche escludendo MessageBox: da 19/1.791 (1,1%) a 1.414/1.800 (78,6%).

Gli altri 53 input del corpus non fanno parte di questa campagna di recupero. Per questo il confronto prima/dopo affianca la figura storica sull'intero corpus. Sostituire alcuni valori dentro una curva presentata come una nuova esecuzione di tutti i 102 sarebbe ambiguo.

Attenzione al vecchio 14,3% x86: era la media semplice delle quindici percentuali per configurazione. Il 14,9% qui è il totale dei successi diviso per il totale dei test. Non sono due conteggi in conflitto: sono due modi diversi di riassumere dati con denominatori diversi. La nuova figura dichiara quello usato.

**2. I tredici programmi benigni non sono i tredici payload x64 recuperati.**

La coincidenza del numero tredici era una fonte di confusione.

| Gruppo | Cosa contiene | Domanda |
|---|---|---|
| 13 programmi controllati | 7 x64 e 6 x86, creati apposta per il test | Dopo la trasformazione il risultato atteso rimane corretto? |
| 6 programmi annotati | 4 x64 e 2 x86, con posizioni dei dati note | Il classificatore identifica i byte corretti? |
| 102 payload originali | 38 x64 e 64 x86 del corpus del lavoro | Quanto funziona il sistema sui payload reali? |
| 49 payload problematici | 13 x64 e 36 x86, sotto il 50% nello storico | Quanto migliora il working rate dopo gli aggiornamenti? |
| 19 payload con dati estraibili | 13 x64 e 6 x86 | Come si comportano i due classificatori dentro la stessa pipeline? |

Gli ultimi due gruppi sono sottoinsiemi dei 102. I programmi controllati sono invece piccoli input separati.

**3. Che cosa sono esattamente i tredici programmi, e perché sono pochi?**

“Fixture” qui significa programma di prova con risultato atteso dichiarato. Ci sono sei casi per architettura: aritmetica, diramazioni, ciclo, chiamate a una funzione locale, combinazione di ciclo/diramazioni/chiamate, e stringhe incorporate nel codice. Su x64 si aggiunge un caso di accesso ai dati tramite un indirizzo ricavato dal codice. Quindi 6 + 6 + 1 = 13.

Sono piccoli: da 19 a 68 byte. Ad esempio il caso del ciclo calcola la somma da 1 a 100, che deve essere 5.050. Il caso delle stringhe deve copiare il testo previsto nel buffer di uscita. Un programma C esegue il codice sulla CPU e restituisce un buffer di 256 byte; il test confronta tutti i byte con quelli attesi, verificando anche che le posizioni da non modificare siano rimaste inalterate.

Tredici non è un numero derivato da un calcolo statistico. È una suite compatta che copre alcuni meccanismi distinti. Dai file non emerge una ragione sperimentale per cui tredici debba essere il numero definitivo. Un campione più ampio aumenterebbe la copertura, ma la valutazione sul materiale reale è già affidata anche ai 102 payload originali.

**4. Che cosa cambia nei sei programmi del classificatore?**

Qui il risultato principale da controllare non è un numero scritto in memoria, ma la risposta alla domanda «dove sono i dati?».

I sei programmi sono: due con più stringhe, uno con una tabella binaria, due senza dati separati e uno in cui byte appartenenti alle istruzioni sembrano testo. Quest'ultimo verifica che il classificatore non estragga come stringa qualcosa che fa parte del codice.

Le posizioni corrette dei dati sono annotate prima del test e non vengono comunicate al modello. Entrambi i metodi vengono confrontati con queste annotazioni. Si verifica inoltre che gli output prodotti continuino a superare il controllo funzionale.

Nei tredici programmi la domanda principale è «il programma trasformato calcola/copia ancora il risultato giusto?». Nei sei aggiuntivi è «la decisione su quali byte siano dati è giusta?». Un programma può funzionare anche se non sono stati identificati tutti i dati: per esempio, alcuni possono essere rimasti correttamente al loro posto. Per questo i due controlli sono distinti.

**5. Perché i risultati sono migliori sui programmi controllati?**

Non perché il sistema riconosca che sono benigni. Sono brevi, costruiti per esercitare pochi meccanismi alla volta, con layout semplici e output facilmente verificabili. Il corpus principale presenta più varietà, dati incorporati più complessi e listing più lunghi. La differenza osservata riguarda queste caratteristiche, non una preferenza del sistema per codice benigno.

Non tutti i risultati controllati sono perfetti: l'implementazione nativa x86 di IBP testata nel benchmark iniziale produce 17 binari su 18 tentativi e nessuno supera il confronto completo del buffer. Anche una suite piccola può quindi individuare un problema.

**6. Che cosa significano “cella”, “shot”, “tentativo”, “seed” e “build”?**

- Una cella è una combinazione da valutare: un input, una tecnica e un'impostazione del prompt. Esempio: programma A, tecnica EQ, prompt con due esempi.
- Uno shot è un esempio dentro il prompt. Zero-shot significa nessun esempio svolto; two-shot significa due esempi. Non significa due tentativi.
- Un tentativo è una richiesta di generare una risposta. Una cella può richiedere più tentativi se il primo viene rifiutato.
- Una ripetizione è una nuova esecuzione della stessa condizione per osservarne la variabilità.
- Un seed è il valore che inizializza le scelte casuali. Cambiarlo può cambiare l'output, senza garantire che ogni risultato sia diverso.
- Una build è un binario effettivamente prodotto e accettato dai controlli di costruzione. Dopo la build viene il test di funzionamento.
- L'harness è semplicemente il programma che avvia il test e registra l'esito.

Se pianifico dieci varianti, riesco a costruirne otto e sei funzionano: build rate 8/10 = 80%; working rate complessivo 6/10 = 60%; working rate sui costruiti 6/8 = 75%. Sono tre domande diverse, tutte utili.

**7. Il classificatore LLM e il trasformatore LLM sono due ruoli diversi.**

Nel primo ruolo il modello propone intervalli di byte da considerare dati. Nel secondo propone un nuovo listing di istruzioni. Gli esempi forniti per insegnare a individuare dati sono indipendenti dagli esempi zero-shot/two-shot del confronto sulle trasformazioni. Cambiare una di queste impostazioni non cambia automaticamente l'altra.

“Validation feedback” significa che il programma comunica al modello il motivo del rifiuto della risposta. Esempio illustrativo per il classificatore: il file ha 100 byte, ma la risposta indica dati fino al byte 120. Il controllore può segnalare che l'intervallo è fuori dal file e chiedere una nuova proposta. Per il trasformatore il messaggio può riguardare un listing non assemblabile o un'etichetta mancante. È un controllo della risposta prodotta, non un verdetto antivirus.

Nel benchmark controllato LLM si usano tre richieste separate per cella, ognuna con una sola generazione. Nel corpus principale i registri contengono anche retry: due celle riuscite hanno richiesto una seconda generazione. Quindi non si deve descrivere quella campagna come integralmente al primo tentativo.

La cache evita di ripetere l'identificazione per un input già analizzato: si riusa la decisione su quali regioni contengono dati. I riferimenti a quelle regioni vengono invece calcolati nuovamente perché il codice può essere cambiato di posizione. È come sapere che una citazione rimanda al capitolo “Risultati”, ma doverne aggiornare il numero di pagina dopo l'impaginazione.

**8. Il listing “canonico”, spiegato passo per passo.**

1. Si parte dal binario originale.
2. Zone prepara una rappresentazione assembly, conservando separatamente i dati identificati ed estratti.
3. Assegna nomi simbolici alle posizioni rilevanti. Un'etichetta identifica una destinazione senza fissarne subito il numero di byte dall'inizio del file.
4. Il modello riceve questo listing preparato e restituisce il listing proposto.
5. La pipeline converte il testo in istruzioni binarie, ricompone la rappresentazione con i dati preservati e applica i controlli di costruzione.
6. Il programma di test esegue l'output e verifica il comportamento atteso.

La similarità LLM confronta il listing del punto 3 con quello del punto 4. Non è una misura di tutte le differenze fra il binario iniziale e quello finale. Nel testo “listing preparato” è più chiaro di “rappresentazione canonica” se il termine non viene prima spiegato.

**9. Wrapping: il principio da capire.**

Le istruzioni x86/x64 hanno lunghezze variabili. Il punto da cui si inizia a leggere determina come una sequenza di byte viene divisa in istruzioni. Nel wrapping, una stessa regione contiene byte che, letti secondo la struttura esterna, appartengono al valore costante di un'istruzione; letti secondo l'interpretazione interna, rappresentano istruzioni della computazione prevista.

“Container” indica l'istruzione esterna. “Immediate operand” indica un valore costante scritto direttamente nei byte dell'istruzione. “Embedded sequence” indica la sequenza di istruzioni rappresentata dentro quel campo. Le due viste condividono gli stessi byte: non sono una copia cifrata e una copia decifrata.

La figura del paper mostra queste due letture. L'integrazione in Zone parte da una rappresentazione del codice già preparata e gestisce anche regioni che rimangono in forma ordinaria. Per questo la preparazione dei dati continua ad avere importanza. La spiegazione riguarda il principio della rappresentazione; i test successivi misurano separatamente costruzione, funzionamento e risposte degli scanner.

**10. Sezione 11.3: “predicted” e “reference”.**

Predicted significa «i byte che il classificatore dice essere dati». Reference significa «i byte che sappiamo essere dati nell'esempio annotato». Qui reference vuol dire risposta corretta di riferimento; altrove “reference” può significare un collegamento/indirizzo nel codice. Il testo deve distinguere i due significati.

Esempio: una stringa occupa dieci byte, dal 20 al 29. Il classificatore indica dal 20 al 27. Tutti gli otto byte indicati sono corretti: precisione 100%. Ne trova otto sui dieci esistenti: richiamo, o recall, 80%. Una corrispondenza esatta richiede di trovare tutti gli intervalli corretti senza aggiungerne altri.

**11. Sezione 11.4: quattro misure, quattro domande.**

Similarità: quanto si somigliano i listing prima e dopo la risposta LLM? Se è 0,906 c'è molta corrispondenza nella sequenza misurata; non è una percentuale di funzionamento. Nel caso NOP si ignorano le operazioni di quel tipo durante il confronto, quindi si può ottenere 1 anche se il binario contiene byte aggiunti.

Detection rate dei motori: quanti motori segnalano malicious per un file? Se sono 3 su 75, il valore è 4%. Nel riepilogo si fa la media dei valori per file. È la metrica ripristinata nella tabella principale.

Percentuale di file rilevati: quanti file ricevono almeno una segnalazione malicious? Se 80 file su 100 vengono segnalati da almeno un motore, il valore è 80%, anche se per ogni file si esprime negativamente un solo motore. Questa è la quantità chiamata q. Le due percentuali non sono intercambiabili e sono entrambe utili.

Diversità: quanti binari hanno byte diversi? Si conta il numero di hash distinti. Tempo e costo rispondono invece a quanto lavoro e denaro richiede la campagna. Nel testo ora questi argomenti hanno paragrafi distinti.

**12. Perché ci sono hash uguali?**

In questo contesto hash uguale indica lo stesso contenuto binario; non è evidenza di una collisione crittografica. Un generatore può ottenere lo stesso risultato in esecuzioni diverse, il modello può riproporre lo stesso listing, e diverse condizioni possono convergere allo stesso binario. Anche gli input possono essere duplicati: i 102 file originali hanno 90 hash distinti.

Nel wrapping i 243 file prodotti contengono 207 hash distinti: ci sono 36 occorrenze oltre il numero di contenuti unici. Nel LLM i 350 file contengono 323 hash: 27 occorrenze aggiuntive. Questi conteggi non dimostrano da soli la causa di ogni duplicato. Un output duplicato può comunque funzionare; riduce la diversità misurata, non automaticamente il working rate.

Nel confronto dei classificatori, “16/19 output identici” significa invece che, per sedici input, il braccio simbolico e il braccio LLM producono lo stesso binario finale. L'identità fra i due metodi è coerente con la pipeline condivisa e non è una mancata classificazione.

**13. Gli esperimenti e i risultati, nell'ordine delle domande.**

Primo: verificare gli input non modificati. I tredici programmi controllati producono i buffer attesi; i 102 originali superano il rispettivo test funzionale. Serve un punto di partenza funzionante per interpretare gli esiti dopo trasformazione.

Secondo: confrontare l'identificazione con risposte note, usando i sei programmi annotati. Ogni programma viene analizzato una volta con il simbolico e tre con il LLM: 6 analisi simboliche e 18 risposte LLM. Tutte corrispondono alle annotazioni. Deduzione: entrambi gestiscono correttamente questi casi, inclusi quelli che non contengono dati separati.

Terzo: confrontare i due metodi sui diciannove payload originali selezionati. Entrambi costruiscono 19 output e ne fanno funzionare 17. Le regioni confrontate coincidono in 9 casi; i binari finali in 16. Deduzione: differenze nella proposta iniziale possono essere assorbite dalla gestione comune dei dati. I tempi mediani registrati sono 124,0 e 59,9 secondi; il costo LLM è $0,2218. I tempi misurano il lavoro effettivamente registrato nei due bracci, con preparazione e caching differenti.

Quarto: trasformare i tredici programmi controllati. Per ogni tecnica nativa ci sono tre esecuzioni per input: 21 x64 e 18 x86. Su x64 tutte le famiglie testate passano; su x86 passano EQ, NOP, BCF e wrapping, mentre il native IBP dell'implementazione iniziale fallisce. Nel confronto LLM si aggiungono quattro tecniche e due condizioni del prompt: 168 richieste x64 e 144 x86. Passano 167/168 e 138/144; tutti i 305 output accettati hanno il buffer corretto. I sette casi rimanenti sono cinque rifiuti di validazione e due problemi di trasporto.

Quinto: wrapping sui 102 originali, la sezione 12.3. Tre seed per input danno 306 varianti pianificate. Se ne costruiscono 243 e 170 superano il test. Su x64: 63 costruite su 114, tutte e 63 funzionanti. Su x86: 180 costruite su 192, di cui 107 funzionanti. Deduzione: nei casi x64 costruiti il comportamento atteso è conservato; i limiti di copertura iniziano prima della build. Su x86 rimangono anche insuccessi dopo la costruzione.

Sesto: LLM sui 102 originali, la sezione 12.4. Ogni input viene combinato con EQ, NOP, BCF, IBP e con zero o due esempi: 102 x 4 x 2 = 816 celle. La campagna produce 350 binari, 275 funzionanti. Su x64 passano 52 dei 53 costruiti; su x86 223 dei 297. Zero-shot ha 139 successi su 408 celle e two-shot 136 su 408. Deduzione: in questa campagna aggiungere due esempi non dà un vantaggio consistente. Le 466 celle senza build sono parte del risultato, non output eseguiti male.

Settimo: il recupero dei 49 payload problematici è una campagna nativa distinta da wrapping e LLM. È quella che sostiene la nuova figura 1,2% -> 80,2% x64 e 14,9% -> 25,9% x86. Un successo in questa campagna non modifica retroattivamente il conteggio di un'altra tecnica o di un altro esperimento.

Ottavo: scansioni dei file prodotti. Il manifest contiene 612 file ma 549 hash distinti. Ci sono 548 report con risposte e uno vuoto. Nessuno dei 207 hash wrapping riceve una segnalazione malicious; fra i 322 hash LLM con report utilizzabile, 221 ricevono almeno una segnalazione. Per il LLM il detection rate medio dei motori è 5,06%, mentre la percentuale di file rilevati è 68,6%. I diciannove output del solo data handling risultano tutti rilevati. Sono risultati statici separati dagli esiti di funzionamento.

**14. B1/B2/B3, costi delle riprese e orari: che cosa serve al lettore?**

B1/B2/B3 erano nomi interni delle copie del motore usate negli esperimenti. Il lettore non ha bisogno di incontrarli continuamente. Sono stati spostati nelle note dell'artefatto. Rimane una breve indicazione quando il cambio di versione conta, come per il native IBP x86 rispetto ai test successivi.

I costi dei tentativi falliti vanno inclusi: sono richieste che possono avere consumato token. Il costo dei record rappresentativi delle 816 celle è $19,27; includendo i quattordici riavvii falliti registrati diventa $19,63. La differenza appartiene alla contabilità dell'esperimento, non deve occupare l'apertura della spiegazione tecnica.

“Run duration is not pure API latency” significa che il cronometro comprende anche lavoro locale, come preparazione e controlli. Quindi 160,3 secondi è il tempo mediano del record di esecuzione considerato, non necessariamente il tempo impiegato solo dal servizio remoto.

“Frozen evidence” significa che è stata conservata una copia fissa dei dati usati per il paper, in modo che nuove esecuzioni non cambino silenziosamente le tabelle. Hash dei sorgenti, orari precisi e inventario dei file sono utili per riprodurre il lavoro; sono stati spostati nelle note tecniche. Nel testo principale resta una frase che indica la disponibilità di versioni e registri.

**15. Che cosa è stato cambiato nel manoscritto.**

Sono stati aggiornati abstract, motivazione, metodologia, risultati, discussione e conclusioni per dare evidenza al miglioramento. È stata aggiunta la figura prima/dopo sui 49 payload con una tabella dei conteggi per input e tecnica nell'artefatto. Sono stati chiariti i due gruppi di programmi controllati, gli esempi del prompt, i retry, il listing preparato, predicted/reference, similarity e detection rate. Le ripetute avvertenze sull'equivalenza formale sono state concentrate in un solo paragrafo di discussione. La versione precedente è conservata in before_clarity_revision/.
