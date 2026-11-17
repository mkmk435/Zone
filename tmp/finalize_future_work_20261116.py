from pathlib import Path
import shutil, json, zipfile, hashlib, re

base=Path(r'C:\Users\ubu\Desktop\Zone')
paper=base/'tmp/ccis_rewrite_20261114'
qa_dir=paper/'qa_future_work_20261116'
qa=json.loads((qa_dir/'qa_report.json').read_text())
assert qa['pages']==30 and qa['table_bodies']['all_identical']
assert all(v['all_identical'] for v in qa['retained_objects'].values())
qa['retained_objects']['figure'].pop('intentional_revision',None)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unchanged=[]
for n in range(1,28):
    a=paper/'qa_structure_20261116'/f'page-{n:02d}.png'
    b=qa_dir/f'page-{n:02d}.png'
    if a.exists() and sha(a)==sha(b):unchanged.append(n)
qa['rendered_pages_identical_to_previous_revision']=unchanged
(qa_dir/'qa_report.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')

prior=base/'output/submission/zone_editorial_20261116'
support=base/'output/submission/zone_editorial_future_work_20261116'
support.mkdir(exist_ok=True)
for name in ('PERMISSION_REQUEST.txt','REUSE_INVENTORY.csv','REVIEWER_RESPONSE_IBP.txt','REVIEWER_RESPONSE_SEED.txt','VERIFIED_SOURCES.json','Supplementary_Material_S1.zip'):
    shutil.copy2(prior/name,support/name)
notes=(prior/'REVISIONS_AND_OPEN_POINTS.md').read_text(encoding='utf-8')
a=notes.index('## Da discutere');b=notes.index('Resta da verificare la copertura',a)
notes=notes[:a]+'''## Future Work inserito dopo la conferma dell'autore

La sezione 14.1 ora presenta le due direzioni concordate: supporto ai file
PE e ampliamento della validazione funzionale. Il supporto PE è collegato
esplicitamente all'aumento della varietà di programmi testabili, a condizioni
di esecuzione più rappresentative e alla valutazione dell'utilità pratica
del tool su applicazioni complete. Le direzioni sono presentate come lavoro
futuro, senza attribuire alla versione attuale risultati non misurati.

Il PDF comprende 30 pagine, bibliografia inclusa. Dati, figure e risultati
sperimentali sono invariati rispetto alla precedente versione da 29 pagine.

'''+notes[b:]
(support/'REVISIONS_AND_OPEN_POINTS.md').write_text(notes,encoding='utf-8')
letter=(prior/'EDITOR_DIFFERENCES.txt').read_text(encoding='utf-8').rstrip()
letter+=' The concluding future-work section identifies PE support as a way to broaden testing and assess practical applicability on complete applications, alongside a wider functional-validation programme.\n'
(support/'EDITOR_DIFFERENCES.txt').write_text(letter,encoding='utf-8')

outpdf=base/'output/pdf/zone_revisione_20261116_future_work.pdf'
shutil.copy2(paper/'main.pdf',outpdf)
assert sha(outpdf)==qa['pdf_sha256']
audit={'date':'2026-11-16','pages':30,'pdf_sha256':sha(outpdf),'future_work_section':'14.1','future_work_page':28,'author_approved_topics':['PE support and practical applicability','broader functional validation'],'visual_review_completed':True,'unchanged_table_bodies':13,'unchanged_figures':8,'new_experiments':False,'qa':qa,'supplement_unchanged':sha(support/'Supplementary_Material_S1.zip')==sha(prior/'Supplementary_Material_S1.zip')}
(paper/'FUTURE_WORK_REVISION_20261116.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
(support/'FUTURE_WORK_REVISION_20261116.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')

readme=paper/'README_REVISIONE.md'
s=readme.read_text(encoding='utf-8')
s=s.replace('# Versione corrente - 16 novembre 2026','# Versione corrente con Future Work - 16 novembre 2026',1)
s=s.replace('`../../output/pdf/zone_revisione_20261116.pdf`: 29 pagine, bibliografia inclusa.','`../../output/pdf/zone_revisione_20261116_future_work.pdf`: 30 pagine, bibliografia inclusa.',1)
s=s.replace('Future Work da discutere: l\'autore ha esplicitamente chiesto di non inserirlo\nancora. Resta margine entro il limite di 30 pagine.','Future Work inserito in sezione 14.1, pagina 28, dopo la conferma dell\'autore.\nIl testo collega il supporto PE alla capacità di test su applicazioni complete\ne alla valutazione dell\'utilità pratica; include inoltre la validazione più ampia.',1)
s=s.replace('Verifiche in `qa_structure_20261116/` e `STRUCTURE_REVISION_20261116.json`.\nVersione precedente in `before_structure_revision_20261116/`.','Verifiche in `qa_future_work_20261116/` e `FUTURE_WORK_REVISION_20261116.json`.\nVersione precedente in `before_future_work_20261116/`.',1)
s=s.replace('`../../output/submission/zone_editorial_20261116/`.','`../../output/submission/zone_editorial_future_work_20261116/`.',1)
readme.write_text(s,encoding='utf-8')

files={'main.tex','bibliography.bib','llncs.cls','splncs04.bst','build.ps1'}
def collect(name):
    for inc in re.findall(r'\\input\{([^}]+)\}',(paper/name).read_text(encoding='utf-8')):
        inc=inc if inc.endswith('.tex') else inc+'.tex'
        if inc not in files:files.add(inc);collect(inc)
collect('main.tex')
with zipfile.ZipFile(support/'Manuscript_LaTeX.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(files):z.write(paper/name,name)
    z.writestr('README.txt','Revision with Future Work: 16 November 2026. Main file: main.tex. PDF: 30 pages including references. Section 14.1 adds PE support and broader functional validation as future directions. Compile with a standard TeX distribution and BibTeX, or build.ps1 on Windows. Figures are drawn in LaTeX.\n')
package=base/'output/submission/zone_materiali_20261116_future_work.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(support.iterdir()):
        if path.is_file():z.write(path,path.name)
with zipfile.ZipFile(package) as z:assert z.testzip() is None
print(json.dumps({'pdf':str(outpdf),'pages':30,'package':str(package),'unchanged_rendered_pages':unchanged},indent=2))
