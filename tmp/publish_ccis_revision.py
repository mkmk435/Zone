from pathlib import Path
import hashlib
import json
import shutil

source=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_extension_20261113').resolve()
target=Path(r'C:\Users\ubu\Desktop\CCIS').resolve()
audit=json.loads((source/'REVISION_AUDIT.json').read_text())
current=(target/'main.tex').read_text(encoding='utf-8')
if hashlib.sha256(current.encode('utf-8')).hexdigest()!=audit['original_source_sha256']:
    raise RuntimeError('CCIS/main.tex changed during preparation; refusing to overwrite concurrent edits.')
backup=target/'backup_before_extension_20261113'
index=1
while backup.exists():
    index+=1
    backup=target/f'backup_before_extension_20261113_{index}'
if backup.resolve().parent!=target:
    raise RuntimeError('Backup target is outside the requested project.')
backup.mkdir()
for name in ['main.tex','bibliography.bib','llncs.cls','splncs04.bst']:
    shutil.copy2(target/name,backup/name)
for name in ['main.tex','bibliography.bib','llncs.cls','splncs04.bst','main.pdf','main.bbl',
             'EDITOR_DIFFERENCES.txt','README_REVISIONE.md','REVISION_AUDIT.json','build.ps1','.gitignore']:
    shutil.copy2(source/name,target/name)
for name in ['sections','figures','.tools']:
    destination=(target/name).resolve()
    if destination.parent!=target:
        raise RuntimeError('Copy destination is outside the requested project.')
    shutil.copytree(source/name,destination,dirs_exist_ok=True)
pdf_hash=hashlib.sha256((target/'main.pdf').read_bytes()).hexdigest()
assert pdf_hash==hashlib.sha256((source/'main.pdf').read_bytes()).hexdigest()
receipt={'project':str(target),'backup':str(backup),'pdf_sha256':pdf_hash,
         'pages':22,'status':'working draft, extended results pending; x86 wrapping in development'}
(target/'REVISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
