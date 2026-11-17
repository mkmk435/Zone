from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
paper = root / 'tmp/ccis_rewrite_20261114'
qa = json.loads((paper / 'qa_prompt_20261116/qa_report.json').read_text())
assert qa['pages'] == 30 and qa['table_bodies']['all_identical']
out = root / 'output/pdf/zone_revisione_20261116_prompting.pdf'
shutil.copy2(paper / 'main.pdf', out)
assert hashlib.sha256(out.read_bytes()).hexdigest() == qa['pdf_sha256']
source = root / 'output/submission/zone_editorial_future_work_20261116/Manuscript_LaTeX.zip'
target = root / 'output/submission/zone_sorgenti_20261116_prompting.zip'
with zipfile.ZipFile(source) as old, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as new:
    for name in old.namelist():
        if name == 'sections/extension_llm.tex':
            new.write(paper / name, name)
        elif name == 'README.txt':
            new.writestr(name, 'Revision: 16 November 2026. Main file: main.tex. 30 pages including references. Section 9.2 describes the structured prompt and the shared specification across zero-shot and two-shot conditions. Other source files and experimental results are unchanged from the Future Work revision. Compile with a standard TeX distribution and BibTeX, or build.ps1 on Windows.\n')
        else:
            new.writestr(name, old.read(name))
with zipfile.ZipFile(target) as check:
    assert check.testzip() is None
    assert check.read('sections/extension_llm.tex') == (paper / 'sections/extension_llm.tex').read_bytes()
readme = paper / 'README_REVISIONE.md'
text = readme.read_text(encoding='utf-8')
readme.write_text('# Aggiornamento prompting - 16 novembre 2026\n\nVersione corrente: `../../output/pdf/zone_revisione_20261116_prompting.pdf`, 30 pagine.\nSorgenti: `../../output/submission/zone_sorgenti_20261116_prompting.zip`.\nSezione 9.2: struttura dei messaggi, regole, vincoli, informazioni sull\'input, formato della risposta e differenza fra condizioni zero-shot e two-shot.\nRipetizioni ridotte in 9.1 e 9.3 per rispettare il limite. Nessun nuovo risultato sperimentale.\nQA: `qa_prompt_20261116/`; backup: `before_prompt_revision_20261116/`.\n\n---\n\n' + text, encoding='utf-8')
print(json.dumps({'pdf': str(out), 'pages': qa['pages'], 'sources': str(target)}, indent=2))
