from pathlib import Path
import json, csv, hashlib, io, shutil, zipfile

root=Path(r'C:\Users\ubu\Desktop\Zone')
paper=root/'tmp/ccis_rewrite_20261114'
support=root/'output/submission/zone_editorial_20261115'
evidence=paper/'evidence/editorial_20261115'
sha=lambda b:hashlib.sha256(b).hexdigest()

# Extend the existing numerical supplement with the 19-input comparison,
# recorded summaries, and version manifests. No engine or executable is copied.
archive=support/'Supplementary_Material_S1.zip'
with zipfile.ZipFile(archive) as z:
    entries={n:z.read(n) for n in z.namelist() if n!='CHECKSUMS.json'}
rows=list(csv.DictReader((paper/'evidence/completed_20261114/sources/tmp/campaign/data_compare.csv').open(encoding='utf-8')))
assert len(rows)==19
fields=[k for k in rows[0] if k not in ('symbolic_set','llm_set')]
buf=io.StringIO(newline='')
w=csv.DictWriter(buf,fieldnames=fields,extrasaction='ignore')
w.writeheader();w.writerows(rows)
entries['evidence/data_handling_comparison.csv']=buf.getvalue().encode('utf-8')
extra=[
    'evidence/completed_20261114/SUMMARY.json',
    'evidence/followup_20261115/SUMMARY.json',
    'evidence/followup_20261115/controlled_benchmark_details.tex',
    'evidence/followup_20261115/earlier_pilots.tex',
    'evidence/followup_20261115/scan_details_previous_layout.tex',
]
for name in extra:entries[name]=(paper/name).read_bytes()
for version in ('2026-11-13_block1','2026-11-13_block2'):
    entries[f'evidence/version_manifests/{version}.json']=(paper/f'evidence/sources/bench/engines/{version}/VERSION.json').read_bytes()
entries['README.md']+=b'\nAdditional records: data_handling_comparison.csv provides the 19-input data comparison; version_manifests/ contains metadata and hashes only; SUMMARY.json files provide aggregate accounting; the .tex files retain detailed numerical tables and earlier pilot summaries moved out of the main manuscript.\n'
manifest={n:{'sha256':sha(b),'bytes':len(b)} for n,b in entries.items()}
entries['CHECKSUMS.json']=(json.dumps(manifest,indent=2)+'\n').encode('utf-8')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name,b in entries.items():z.writestr(name,b)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,info in manifest.items():assert sha(z.read(name))==info['sha256']

# Include the new table that reuses historical measurements in the inventory.
inventory=support/'REUSE_INVENTORY.csv'
with inventory.open(encoding='utf-8',newline='') as f:
    reader=csv.DictReader(f); fields=reader.fieldnames; items=list(reader)
if not any(r['current_object']=='Table 12' for r in items):
    items.append(dict(zip(fields,['Table 12','tab:overall_working_update','10.5220/0015170600004103','New table combining reaggregated historical data with new measurements','Confirm applicable rights; no permission represented as granted'])))
with inventory.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(items)

qa=json.loads((paper/'qa_editorial_20261115/qa_report.json').read_text())
assert qa['pages']==30 and qa['table_bodies']['all_identical']
outpdf=root/'output/pdf/zone_revisione_30_pagine_editoriale.pdf'
shutil.copy2(paper/'main.pdf',outpdf)
assert sha(outpdf.read_bytes())==qa['pdf_sha256']
audit=json.loads((evidence/'EDITORIAL_AUDIT.json').read_text())
audit.update({'pdf_pages':30,'pdf_sha256':qa['pdf_sha256'],'unchanged_table_bodies':13,'visual_review_completed':True,'supplement_included_files':len(manifest),'supplement_sha256':sha(archive.read_bytes()),'output_pdf':str(outpdf),'reuse_inventory_objects':len(items)})
(evidence/'EDITORIAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
(support/'EDITORIAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')

readme=paper/'README_REVISIONE.md'
old=readme.read_text(encoding='utf-8')
prefix='''# Revisione editoriale corrente - 15 novembre 2026

Il PDF corrente è `main.pdf`, distribuito anche come
`../../output/pdf/zone_revisione_30_pagine_editoriale.pdf`: 30 pagine,
bibliografia inclusa. La precedente consegna da 30 pagine resta conservata.

Sono state aggiunte la nota di extended version in prima pagina e la
dichiarazione di disponibilità dei materiali, chiarite le due aggregazioni
della Tabella 12 e precisati alias del modello e versione del test IBP.
Il grafico storico di detection è stato ricalcolato dai record salvati con
etichette corrette; la similarità è descritta come confronto fra vettori
di frequenze dei mnemonici aggregati per corpus. La nota di lavoro è rimossa.
I corpi delle 13 tabelle sono invariati. Tabella 12: pagina 26; Tabella 13:
pagina 27. Le sezioni nuove iniziano a pagina 14. Font e margini sono invariati.

Restano da confermare da parte degli autori la dichiarazione degli interessi
e la copertura del riuso. I materiali pronti per queste verifiche, i due
paragrafi per l'editor, la risposta IBP e il supplemento numerico S1 sono in
`../../output/submission/zone_editorial_20261115/` e nel pacchetto ZIP di consegna.
Non sono stati inviati messaggi, eseguiti nuovi esperimenti o modificati motori.

Verifiche: `qa_editorial_20261115/qa_report.json` e
`evidence/editorial_20261115/EDITORIAL_AUDIT.json`. La copia precedente dei
sorgenti è in `before_editorial_corrections_20261115/`.

---

'''
if not old.startswith('# Revisione editoriale corrente'):
    readme.write_text(prefix+old,encoding='utf-8')

package=root/'output/submission/zone_materiali_editoriali.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(support.iterdir()):
        if path.is_file():z.write(path,path.name)
with zipfile.ZipFile(package) as z:assert z.testzip() is None
print(json.dumps({'pdf':str(outpdf),'pages':qa['pages'],'support_package':str(package),'support_bytes':package.stat().st_size,'supplement_files':len(manifest),'tables_unchanged':13},indent=2))
