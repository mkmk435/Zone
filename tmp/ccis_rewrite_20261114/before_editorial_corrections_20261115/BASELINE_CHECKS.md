# Controlli della baseline conservata

Tutti i risultati storici sono ripristinati dalla bozza preparatoria. Questa revisione additiva non cambia silenziosamente dati o percentuali pubblicati.

Prima della submission riconciliare con il PDF della conferenza e gli archivi originali:

- Nei grafici detection/working rate alcune associazioni categoria-valore nella coda delle configurazioni richiedono controllo. Esempio verificato: il LaTeX preparatorio assegna 66,8% a eq_pii x64, mentre test_report.txt da 216/377 = 57,3%; assegna 0,3% a nop_pii, mentre l'archivio da 212/370 = 57,3%. Il valore 1/375 = 0,3% appartiene a nop_bcf. Non trattare il disegno del grafico come verifica del dato.
- results.json contiene 15.021 record e 15.020 percorsi unici: una ripetizione e presente. Dichiarare deduplicazione e denominatore in un'eventuale rianalisi.
- La cosine similarity descritta come distribuzione di opcode va confrontata con lo script effettivamente usato: lo script create_var.py oggi presente tratta anche operandi e aggregazioni di corpus. SequenceMatcher nei test LLM e una metrica separata.
- Se si correggono le figure, identificare esplicitamente correzioni e rianalisi; conservare la distinzione dai test nuovi. Il codice storico e le sorgenti precedenti restano nei backup.

Questi controlli sono indicati anche da una nota blu nel PDF di lavoro. La conservazione dei risultati risponde alla natura di estensione del manoscritto; non ne certifica la correttezza numerica finale.
