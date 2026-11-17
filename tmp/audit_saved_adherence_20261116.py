"""Retrospective diagnostic audit only; no engine imports, execution or API calls."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'analysis' / 'adherence_diagnostics_20261116'
OUT.mkdir(parents=True, exist_ok=True)
inputs = [ROOT / 'tmp/campaign/llm_summary.csv']
with inputs[0].open(newline='', encoding='utf-8-sig') as handle:
    corpus = list(csv.DictReader(handle))
assert len(corpus) == 816
assert len({(r['arch'], r['payload'], r['tech'], r['shots']) for r in corpus}) == 816
markers = ('did not insert any instruction', 'did not permute blocks',
           'did not change any instruction')
summary = []
for tech in ('eq', 'nop', 'bcf', 'ibp'):
    for shot in ('0', '2'):
        rows = [r for r in corpus if r['tech'] == tech and r['shots'] == shot]
        built = [r for r in rows if r['built'] == '1']
        summary.append(dict(technique=tech, shots=int(shot), planned=len(rows),
                            built=len(built),
                            similarity_one=sum(float(r['similarity'] or -1) == 1 for r in built),
                            explicit_negative_diagnostics=sum(any(m in r['error'] for m in markers) for r in rows)))

benign = []
for path in sorted((ROOT / 'bench/results').glob('llm_attempts*.jsonl')):
    inputs.append(path)
    benign.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
assert len(benign) == 312
assert len({(r['arch'], r['case'], r['technique'], r['shots'], r['call']) for r in benign}) == 312
benign_eq = []
for shot in (0, 2):
    rows = [r for r in benign if r['shots'] == shot and r['technique'] == 'eq']
    unchanged = []
    for row in rows:
        path = ROOT / row['log']
        inputs.append(path)
        if 'eq did not change any instruction' in path.read_text(errors='replace'):
            unchanged.append(dict(arch=row['arch'], case=row['case'], replicate=row['call'],
                                  build_ok=row['build_ok'], functional_match=row['match']))
    benign_eq.append(dict(shots=shot, requests=len(rows), built=sum(r['build_ok'] for r in rows),
                          unchanged_warning_count=len(unchanged), cases=unchanged))

result = dict(scope='Saved diagnostics only, not a complete technique-adherence evaluation',
              corpus=summary, benign_eq=benign_eq,
              source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
(OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
lines = [
    '# Controllo preliminare di aderenza: zero-shot e two-shot', '',
    'Analisi retrospettiva delle diagnostiche salvate. Nessuna nuova generazione, esecuzione o scansione. '
    'Questo controllo non misura la quota totale di trasformazioni applicate correttamente né la loro intensità.', '',
    '## Programmi benigni: controllo EQ', '',
    'Sono disponibili 312 richieste su 13 programmi benigni, 4 tecniche, 2 condizioni e 3 repliche. '
    'Per EQ sono 39 richieste per condizione; tutte hanno prodotto un output. '
    'Il warning esplicito di sequenza di firme delle istruzioni invariata compare in 3/39 casi zero-shot (7,7%) '
    'e 2/39 two-shot (5,1%). Le firme sono una rappresentazione normalizzata: il warning non afferma identità binaria. '
    'Le altre 36/39 e 37/39 richieste non sono automaticamente trasformazioni EQ corrette: assenza del warning '
    'e cambiamento della sequenza non costituiscono una verifica completa della tecnica. '
    'Questi risultati riguardano i programmi benigni, non i 102 payload principali.', '',
    '## Corpus principale: 816 celle', '',
    'Ogni riga comprende 102 input. I casi segnalati possono avere anche altri errori. '
    'Le diagnostiche non coprono necessariamente tutti gli output: disassemblaggio o assemblaggio possono fallire prima dei controlli. '
    'Per questo non si può dividere il numero di warning per 102 e chiamare il complemento tasso di aderenza.', '',
    '| Tecnica | Shot | Costruiti / 102 | Diagnostiche esplicite di mancata applicazione |',
    '|---|---:|---:|---:|',
]
for row in summary:
    lines.append(f"| {row['technique'].upper()} | {row['shots']} | {row['built']} | {row['explicit_negative_diagnostics']} |")
lines += ['',
    'Tutti gli 87 output NOP costruiti hanno similarità 1, perché il confronto esclude le istruzioni riconosciute '
    'come NOP-like. Non significa che siano invariati. Nessuno degli 83 output EQ costruiti ha similarità 1; '
    'anche questo non prova che tutte le sostituzioni richieste siano state effettuate.', '',
    '## Interpretazione', '',
    'I dati disponibili non dimostrano che zero-shot applichi la tecnica meno spesso di two-shot. '
    'Non escludono però una differenza di intensità o qualità della trasformazione. '
    'Il precedente confronto del working rate risponde a una domanda diversa: un output può funzionare '
    'pur applicando poco la tecnica. La frase sul paper deve quindi riferirsi al working rate, non alla qualità '
    'complessiva delle trasformazioni.', '',
    'Una misura completa richiede criteri di aderenza distinti per tecnica e annotazioni degli output rispetto '
    'alla rappresentazione effettivamente inviata al modello, separando applicazione, intensità, validità e casi '
    'non valutabili. Per una verifica controllata su programmi benigni, le annotazioni andrebbero effettuate '
    'senza conoscere la condizione di prompting; i risultati resterebbero limitati a quel campione.', '',
    'Numeri e hash dei file consultati: `results.json`. Il manoscritto non è stato modificato.',
]
(OUT / 'REPORT_IT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(dict(corpus=summary, benign_eq=benign_eq, report=str(OUT / 'REPORT_IT.md')), indent=2))
