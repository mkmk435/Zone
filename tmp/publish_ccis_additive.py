from pathlib import Path
import json
import hashlib
import shutil
import re

src=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_additive_20261113').resolve()
dst=Path(r'C:\Users\ubu\Desktop\CCIS').resolve()
audit=json.loads((src/'REVISION_AUDIT.json').read_text())
if hashlib.sha256((dst/'main.tex').read_bytes()).hexdigest()!=audit['previous_project_main_sha256']:
    raise RuntimeError('main.tex changed while the additive revision was being prepared; concurrent edits will not be overwritten.')
qa=json.loads((src/'qa/qa_report.json').read_text())
assert qa['pages']==27 and not qa['unresolved_markers'] and not any(qa['out_of_page_characters'])
assert 'Overfull' not in (src/'main.log').read_text(errors='replace')
baseline=(dst/'backup_before_extension_20261113/main.tex').read_text()
new=(src/'main.tex').read_text()
for env in ['figure','table','lstlisting','algorithm']:
    pattern=r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}'
    before=re.findall(pattern,baseline,re.S);after=re.findall(pattern,new,re.S)
    assert all(x in after for x in before)
audit['pdf_checks']={'pages':27,'unresolved_references':0,'overfull_boxes':0,
 'out_of_page_characters':0,'all_pages_rendered':True,
 'visual_review':'all five contact sheets and selected full-size historical and extension pages inspected'}
audit['pdf_sha256']=hashlib.sha256((src/'main.pdf').read_bytes()).hexdigest()
(src/'REVISION_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
backup=dst/'backup_reorganized_22pages_20261113'
index=1
while backup.exists():
    index+=1
    backup=dst/f'backup_reorganized_22pages_20261113_{index}'
assert backup.resolve().parent==dst
backup.mkdir()
for f in dst.iterdir():
    if f.is_file():shutil.copy2(f,backup/f.name)
# Move the previous, superseded source directories into the dated backup.
# Both endpoints are verified to remain inside the explicitly requested project.
for name in ['sections','figures']:
    origin=(dst/name).resolve();saved=(backup/name).resolve()
    assert origin.parent==dst and saved.parent==backup and backup.parent==dst
    if origin.exists():shutil.move(str(origin),str(saved))
shutil.copytree(src/'sections',dst/'sections')
for name in ['main.tex','bibliography.bib','main.pdf','main.bbl',
 'EDITOR_DIFFERENCES.txt','README_REVISIONE.md','BASELINE_CHECKS.md','REVISION_AUDIT.json']:
    shutil.copy2(src/name,dst/name)
# Preserve the project-local compiler and make newly used TeX packages available.
cache_source=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_extension_20261113\.tools\tectonic-cache')
cache_dest=(dst/'.tools/tectonic-cache').resolve()
assert cache_dest.is_relative_to(dst)
shutil.copytree(cache_source,cache_dest,dirs_exist_ok=True)
receipt={'project':str(dst),'revision':'additive extension with complete original results',
 'backup_previous_reorganization':str(backup),
 'backup_original_preparation':str(dst/'backup_before_extension_20261113'),
 'pages':27,'pdf_sha256':hashlib.sha256((dst/'main.pdf').read_bytes()).hexdigest()}
assert receipt['pdf_sha256']==audit['pdf_sha256']
(dst/'REVISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
