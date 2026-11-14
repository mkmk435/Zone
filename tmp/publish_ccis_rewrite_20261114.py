from pathlib import Path
import json,hashlib,shutil,datetime

src=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114').resolve()
dst=Path(r'C:\Users\ubu\Desktop\CCIS').resolve()
assert str(dst)==r'C:\Users\ubu\Desktop\CCIS'
evid=src/'evidence/completed_20261114'
manifest=json.loads((evid/'SOURCES.json').read_text())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,expected in manifest['prior_ccis_hashes'].items():
    if digest(dst/name)!=expected:raise RuntimeError('Concurrent source edit: '+name)
for item in manifest['sources']:
    assert digest(evid/'sources'/item['path'])==item['sha256'],item['path']
qa=json.loads((src/'qa/qa_report.json').read_text())
assert qa['pages']==33 and qa['rendered_pages']==33
assert not any(qa[k] for k in ['out_of_page_characters','replacement_character_pages','unresolved_markers','overfull_boxes','undefined_references','missing_glyph_warnings'])
assert all(v['unchanged'] for v in qa['retained_baseline_objects'].values())
assert digest(src/'main.pdf')==qa['pdf_sha256']
tex=(src/'main.tex').read_text()+'\n'.join(p.read_text() for p in (src/'sections').glob('*.tex'))
for stale in ['still in progress','Ongoing DeepSeek','30 finished run','reserve the extended']:
    assert stale not in tex,stale
audit={'revision':'Full explanatory rewrite and completed original-corpus campaign, 14 November 2026',
       'evidence':'evidence/completed_20261114/SOURCES.json',
       'prior_evidence_retained':'evidence/SOURCES.json',
       'pdf_checks':qa,'pdf_sha256':qa['pdf_sha256'],
       'visual_review':'All 33 pages inspected in contact sheets; full-size pipeline, revised wrapping diagram, and current scan table inspected.',
       'new_experiments_or_external_scans_performed':False,
       'material_accounting_corrections':['830 recorded runs over 816 cells; 14 failed restarts; four multi-generation runs','835 recorded API calls; one run without usage','All-run recorded cost USD 19.625838237 versus USD 19.269954795 for retained cell records','549 completed scan records, 548 with nonempty responses; empty result excluded from measured negative scans','75 failing LLM files correspond to 60 hashes, 59 with evaluable reports'],
       'source_files':{str(p.relative_to(src)):digest(p) for p in [src/'main.tex',src/'bibliography.bib',*(src/'sections').glob('*.tex')]}}
(src/'REVISION_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
stamp=datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=1))).strftime('%Y%m%d_%H%M%S')
backup=dst/('backup_before_rewrite_'+stamp)
assert backup.resolve().parent==dst and not backup.exists()
backup.mkdir()
for p in dst.iterdir():
    if p.is_file():shutil.copy2(p,backup/p.name)
for name in ['sections','evidence']:
    shutil.copytree(dst/name,backup/name)
files=['main.tex','main.pdf','main.bbl','main.log','README_REVISIONE.md','EDITOR_DIFFERENCES.txt','REVISION_AUDIT.json']
for name in files:shutil.copy2(src/name,dst/name)
shutil.copytree(src/'sections',dst/'sections',dirs_exist_ok=True)
assert not (dst/'evidence/completed_20261114').exists()
shutil.copytree(evid,dst/'evidence/completed_20261114')
assert digest(dst/'main.pdf')==audit['pdf_sha256']
for name,value in audit['source_files'].items():assert digest(dst/name)==value
receipt={'project':str(dst),'revision':audit['revision'],'backup':str(backup),'pages':qa['pages'],
         'pdf_sha256':audit['pdf_sha256'],'evidence':audit['evidence'],'saved_at_berlin':stamp}
(dst/'REVISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
