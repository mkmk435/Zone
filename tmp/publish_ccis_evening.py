from pathlib import Path
import json,hashlib,shutil,re

src=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_update_20261113').resolve()
dst=Path(r'C:\Users\ubu\Desktop\CCIS').resolve()
manifest=json.loads((src/'evidence/SOURCES.json').read_text())
for name,expected in manifest['prior_ccis_hashes'].items():
    if hashlib.sha256((dst/name).read_bytes()).hexdigest()!=expected:
        raise RuntimeError(f'Concurrent source edit detected in {name}; refusing to overwrite.')
qa=json.loads((src/'qa/qa_report.json').read_text())
assert qa['pages']==28 and not qa['unresolved_markers'] and not any(qa['out_of_page_characters'])
log=(src/'main.log').read_text(errors='replace')
assert 'Overfull' not in log and 'undefined' not in log
baseline=(dst/'backup_before_extension_20261113/main.tex').read_text()
main=(src/'main.tex').read_text()
for env in ['figure','table','lstlisting','algorithm']:
    pattern=r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}'
    old=re.findall(pattern,baseline,re.S);current=re.findall(pattern,main,re.S)
    assert all(x in current for x in old)
audit=json.loads((src/'REVISION_AUDIT.json').read_text())
audit['pdf_checks']={'pages':28,'undefined_references':0,'overfull_boxes':0,'out_of_page_characters':0,
 'all_pages_rendered':True,'visual_review':'all five contact sheets and full-size abstract/results pages inspected'}
audit['pdf_sha256']=hashlib.sha256((src/'main.pdf').read_bytes()).hexdigest()
(src/'REVISION_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
backup=dst/'backup_before_results_update_20261113_2120'
i=1
while backup.exists():
    i+=1;backup=dst/f'backup_before_results_update_20261113_2120_{i}'
assert backup.resolve().parent==dst
backup.mkdir()
for p in dst.iterdir():
    if p.is_file():shutil.copy2(p,backup/p.name)
for name in ['sections','evidence']:
    if (dst/name).exists():shutil.copytree(dst/name,backup/name)
for name in ['main.tex','main.pdf','main.bbl','main.log','EDITOR_DIFFERENCES.txt','README_REVISIONE.md','REVISION_AUDIT.json']:
    shutil.copy2(src/name,dst/name)
shutil.copytree(src/'sections',dst/'sections',dirs_exist_ok=True)
shutil.copytree(src/'evidence',dst/'evidence',dirs_exist_ok=True)
assert hashlib.sha256((dst/'main.pdf').read_bytes()).hexdigest()==audit['pdf_sha256']
receipt={'project':str(dst),'revision':'additive original study plus completed new benchmarks and frozen ongoing DeepSeek campaign',
 'cutoff_berlin':manifest['cutoff_berlin'],'backup':str(backup),'pages':28,'pdf_sha256':audit['pdf_sha256'],
 'evidence':'evidence/SOURCES.json'}
(dst/'REVISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
