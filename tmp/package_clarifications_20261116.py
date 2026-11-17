from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
paper = root / 'tmp/ccis_rewrite_20261114'
qa = json.loads((paper / 'qa_clarifications_20261116/qa_report.json').read_text())
assert qa['pages'] == 30 and qa['table_bodies']['all_identical']
pdf = root / 'output/pdf/zone_revisione_20261116_chiarimenti.pdf'
shutil.copy2(paper / 'main.pdf', pdf)
assert hashlib.sha256(pdf.read_bytes()).hexdigest() == qa['pdf_sha256']
source = root / 'output/submission/zone_sorgenti_20261116_prompting.zip'
target = root / 'output/submission/zone_sorgenti_20261116_chiarimenti.zip'
changed = {'sections/extension_code_data.tex', 'sections/extension_llm.tex', 'sections/extension_results.tex'}
with zipfile.ZipFile(source) as old, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as new:
    for name in old.namelist():
        if name in changed:
            new.write(paper / name, name)
        elif name == 'README.txt':
            new.writestr(name, 'Revision: 16 November 2026. Main file: main.tex. 30 pages including references. Clarifies preparation caching versus repeated API requests, the rationale for retaining data outside generation, interpretation of shared failures and differing regions, and the x86 recovery denominators. Includes the previous prompting and Future Work revisions. Experimental numbers, tables and figures are unchanged. Compile with a standard TeX distribution and BibTeX, or build.ps1 on Windows.\n')
        else:
            new.writestr(name, old.read(name))
with zipfile.ZipFile(target) as check:
    assert check.testzip() is None
    for name in changed:
        assert check.read(name) == (paper / name).read_bytes()
readme = paper / 'README_REVISIONE.md'
old = readme.read_text(encoding='utf-8')
readme.write_text('# Chiarimenti metodologici - 16 novembre 2026\n\nVersione corrente: `../../output/pdf/zone_revisione_20261116_chiarimenti.pdf`, 30 pagine.\nSorgenti: `../../output/submission/zone_sorgenti_20261116_chiarimenti.zip`.\nChiarite cache e chiamate effettive, separazione dati/generazione, interpretazione WinHTTP/WinHTTPS e denominatori del recupero x86.\nNessun nuovo esperimento. Numeri, tabelle e figure invariati.\nQA: `qa_clarifications_20261116/`; backup: `before_clarifications_20261116/`.\n\n---\n\n' + old, encoding='utf-8')
evidence = {
    'classification_stats_files': 18,
    'classification_api_calls': 18,
    'historical_x86_recorded_tests': 5195,
    'updated_x86_tests': {'inputs': 36, 'configurations': 15, 'repetitions': 5, 'total': 2700},
    'shared_winhttp_failure_outputs_identical': True,
    'root_cause_of_shared_failures_established': False,
    'new_experiments': False,
    'pdf_sha256': qa['pdf_sha256'],
    'pages': qa['pages'],
    'source_files': sorted(changed),
}
(paper / 'CLARIFICATIONS_20261116.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'pdf': str(pdf), 'sources': str(target), 'pages': 30}, indent=2))
