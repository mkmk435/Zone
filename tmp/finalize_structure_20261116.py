from pathlib import Path
import json, zipfile, hashlib, shutil, re

base=Path(r'C:\Users\ubu\Desktop\Zone')
paper=base/'tmp/ccis_rewrite_20261114'
qa=json.loads((paper/'qa_structure_20261116/qa_report.json').read_text())
assert qa['pages']<=30 and qa['table_bodies']['all_identical']
support=base/'output/submission/zone_editorial_20261116'
support.mkdir(exist_ok=True)
prior=base/'output/submission/zone_editorial_20261115'
for name in ('PERMISSION_REQUEST.txt','REUSE_INVENTORY.csv','REVIEWER_RESPONSE_IBP.txt'):
    shutil.copy2(prior/name,support/name)

sources={
 'conference_doi':'https://www.scitepress.org/PublishedPapers/2026/151706/',
 'affiliation':'https://dmi.unipg.it/dipartimento/organizzazione',
 'affiliation_address':'https://dmi.unipg.it/contatti',
 'chat_completions_reference':'https://api-docs.deepseek.com/api/create-chat-completion/',
 'special_feature_ignored_parameters':'https://api-docs.deepseek.com/guides/build_a_chatbot/',
 'llm_benchmark':'https://ojs.aaai.org/index.php/AAAI/article/view/34672',
 'llm_mutation_study':'https://arxiv.org/abs/2410.23894',
 'compiler_comparison':'https://crypto.junod.info/spro15.pdf',
 'semantic_detection':'https://www.acsac.org/2007/papers/81.pdf',
 'memory_extraction':'https://mason.gmu.edu/~rfarley3/2014-ISC-CodeXt.pdf'
}
(paper/'evidence/structure_20261116/VERIFIED_SOURCES.json').write_text(json.dumps({'checked_date':'2026-11-16','sources':sources},indent=2)+'\n',encoding='utf-8')

(support/'REVIEWER_RESPONSE_SEED.txt').write_text('''Proposed response on LLM sampling and reproducibility

The archived client requests used temperature 0.2 and did not transmit a
sampling seed or an explicit top-p value. We do not claim deterministic
reproduction of individual model outputs or control of matched random
streams across prompting conditions. The comparison describes the recorded
campaign under the stated client settings. The revision adds exploratory
paired analyses of the observed functional outcomes and documents their
assumptions in Supplementary Material S1.

Author note: the Chat Completions reference inspected on 16 November 2026 does
not document a seed field. A separate guide mentions seed among parameters
ignored when certain application features are enabled; that does not establish
an effective seed control for the requests used here. These current pages
cannot retrospectively prove provider behavior during every experimental call.
Do not invent an original design rationale such as "realistic API use" unless
the authors can confirm it. Recheck the provider alias mapping at camera-ready,
while preserving the experiment's recorded alias and historical access date.
''',encoding='utf-8')

(support/'REVISIONS_AND_OPEN_POINTS.md').write_text('''# Revisione del 16 novembre 2026

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

## Da discutere

Il Future Work non è inserito: l'autore ha chiesto di discuterlo prima.
La proposta è una breve sottosezione finale, con supporto PE come prima
direzione e possibile ampliamento della validazione funzionale come seconda.
Per i PE, il tema scientifico è l'estensione dai payload a programmi completi
e la valutazione della loro correttezza. Per la validazione, si possono
considerare programmi più vari, annotazioni indipendenti e confronti omogenei
fra versioni. La scelta della seconda direzione resta aperta.

Resta da verificare la copertura del riuso nell'accordo originale o ottenere
conferma dal publisher. La richiesta predisposta non è stata inviata.
Non sono stati eseguiti nuovi payload, chiamate LLM o scansioni: l'aggiunta
statistica usa esclusivamente i risultati già registrati.
''',encoding='utf-8')

(support/'EDITOR_DIFFERENCES.txt').write_text('''This manuscript is an extended and revised version of our SECRYPT 2026 paper, "On Automating the Obfuscation of Malware Payloads: Zone, a bin2bin Metamorphic Engine" (DOI: 10.5220/0015170600004103). The conference paper introduced the Zone architecture and Position-Independent Instruction design and evaluated native transformations on 102 Windows payloads. The extension explicitly identifies its relationship to that work in the introduction and in the comparison with related research. It cites all reused or adapted objects, rewrites the title, abstract, conclusions, and explanatory prose, and compresses the historical presentation. The historical detection plot is identified as a reanalysis of retained scan records with corrected configuration labels.

The new research adds code-data identification and shared data handling, separate LLM classification and transformation paths, and integration and evaluation of assembly wrapping. New experiments include six annotated classification programs, 13 controlled functional programs, data-handling comparisons on 19 original payloads, wrapping and LLM campaigns covering the 102-input corpus, and a recovery comparison on 49 previously problematic inputs. The evaluation distinguishes construction, functionality, detection, diversity, and resource use; it also reports an exploratory paired comparison of prompting conditions. The new methods and evaluation in Sections 8-12 occupy roughly 40% of the current manuscript by page extent, in addition to the expanded synthesis in Sections 13-14. This is an approximate space-based estimate; the substantive additions are documented individually rather than inferred from text similarity alone.
''',encoding='utf-8')

sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(prior/'Supplementary_Material_S1.zip') as z:
    records={n:z.read(n) for n in z.namelist() if n!='CHECKSUMS.json'}
for path in sorted((paper/'evidence/structure_20261116').iterdir()):
    if path.is_file():records[path.relative_to(paper).as_posix()]=path.read_bytes()
records['analysis/paired_prompt_analysis_20261116.py']=(base/'tmp/paired_prompt_analysis_20261116.py').read_bytes()
records['README.md']+=b'\nRevision of 16 November 2026: evidence/structure_20261116/ contains the complete paired prompting records, exact-test calculations, assumptions, Table 11 row recheck, and source verification. The analysis script reads llm_cells.csv and generates statistical records only; it does not execute payloads or call model services.\n'
manifest={n:{'sha256':sha(v),'bytes':len(v)} for n,v in records.items()}
records['CHECKSUMS.json']=(json.dumps(manifest,indent=2)+'\n').encode('utf-8')
with zipfile.ZipFile(support/'Supplementary_Material_S1.zip','w',zipfile.ZIP_DEFLATED) as z:
    for n,v in records.items():z.writestr(n,v)
with zipfile.ZipFile(support/'Supplementary_Material_S1.zip') as z:
    assert z.testzip() is None
    for n,info in manifest.items():assert sha(z.read(n))==info['sha256']

outpdf=base/'output/pdf/zone_revisione_20261116.pdf'
shutil.copy2(paper/'main.pdf',outpdf)
assert sha(outpdf.read_bytes())==qa['pdf_sha256']
audit=json.loads((paper/'STRUCTURE_REVISION_20261116.json').read_text())
audit.update({'pages':qa['pages'],'pdf_sha256':qa['pdf_sha256'],'visual_review_completed':True,'future_work':'Not inserted; author explicitly requested discussion first','paired_analysis':json.loads((paper/'evidence/structure_20261116/prompt_paired_tests.json').read_text()),'qa':qa,'source_checks':sources,'no_conflicts_confirmed':True,'reuse_permission_confirmed':False,'supplement_members':len(records)})
(paper/'STRUCTURE_REVISION_20261116.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
(support/'STRUCTURE_REVISION_20261116.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
shutil.copy2(paper/'evidence/structure_20261116/VERIFIED_SOURCES.json',support/'VERIFIED_SOURCES.json')

readme=paper/'README_REVISIONE.md'
previous=readme.read_text(encoding='utf-8')
intro='''# Versione corrente - 16 novembre 2026

Il manoscritto corrente è `main.pdf`, distribuito come
`../../output/pdf/zone_revisione_20261116.pdf`: 29 pagine, bibliografia inclusa.
Related Work e Conclusions sono ampliati; la Discussion separata è assorbita
nelle Conclusions. L'introduzione dichiara esplicitamente l'estensione e
rimanda alle sezioni dei singoli contributi. La nota in prima pagina è rimossa.
La dichiarazione di assenza di conflitti è confermata dall'autore e compilata.

Le 13 tabelle restano numericamente invariate. La figura concettuale include
ora uscite Stop. La sezione 12.4 aggiunge test appaiati sui risultati salvati,
documentati nel supplemento. Nessun nuovo esperimento è stato eseguito.
Future Work da discutere: l'autore ha esplicitamente chiesto di non inserirlo
ancora. Resta margine entro il limite di 30 pagine.

Verifiche in `qa_structure_20261116/` e `STRUCTURE_REVISION_20261116.json`.
Versione precedente in `before_structure_revision_20261116/`.
Materiali e sorgenti di consegna in
`../../output/submission/zone_editorial_20261116/`.

---

'''
if not previous.startswith('# Versione corrente - 16 novembre 2026'):
    readme.write_text(intro+previous,encoding='utf-8')

# A compact LaTeX source package with only the active manuscript sources.
files={'main.tex','bibliography.bib','llncs.cls','splncs04.bst','build.ps1'}
def include_sources(name):
    for inc in re.findall(r'\\input\{([^}]+)\}',(paper/name).read_text(encoding='utf-8')):
        inc=inc if inc.endswith('.tex') else inc+'.tex'
        if inc not in files:files.add(inc);include_sources(inc)
include_sources('main.tex')
with zipfile.ZipFile(support/'Manuscript_LaTeX.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(files):z.write(paper/name,name)
    z.writestr('README.txt','Current revision: 16 November 2026. Main file: main.tex. Compile with a standard TeX distribution using LaTeX and BibTeX, or build.ps1 on Windows. Figures are drawn in LaTeX. Future Work is intentionally not yet included, pending discussion with the author.\n')
package=base/'output/submission/zone_materiali_editoriali_20261116.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(support.iterdir()):
        if path.is_file():z.write(path,path.name)
with zipfile.ZipFile(package) as z:assert z.testzip() is None
print(json.dumps({'pdf':str(outpdf),'pages':qa['pages'],'package':str(package),'supplement_members':len(records),'latex_source_files':len(files)},indent=2))
