from pathlib import Path
import re, json, shutil, csv, hashlib, collections, zipfile

ROOT=Path(r'C:\Users\ubu\Desktop\Zone')
PAPER=ROOT/'tmp/ccis_rewrite_20261114'
BACK=PAPER/'before_editorial_corrections_20261115'
if not BACK.exists():
    BACK.mkdir()
    for name in ['main.tex','main.pdf','bibliography.bib','README_REVISIONE.md','BASELINE_CHECKS.md']:
        shutil.copy2(PAPER/name,BACK/name)
    shutil.copytree(PAPER/'sections',BACK/'sections')
EVIDENCE=PAPER/'evidence/editorial_20261115'
EVIDENCE.mkdir(exist_ok=True)
SUPPORT=ROOT/'output/submission/zone_editorial_20261115'
SUPPORT.mkdir(parents=True,exist_ok=True)

def original(name):return (BACK/name).read_text(encoding='utf-8')
def save(name,s):(PAPER/name).write_text(s,encoding='utf-8')
def between(s,start,end,new):
    a=s.index(start);b=s.index(end,a+len(start))
    return s[:a]+new.strip()+'\n\n'+s[b:]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

categories=['nop','eq','pii','bcf','ibp','eq_nop_pii','eq_nop_bcf','eq_nop_ibp','eq_nop','eq_pii','eq_bcf','eq_ibp','nop_pii','nop_bcf','nop_ibp']
raw=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
dedup={}
for row in raw:
    key=re.sub('/+','/',row['file'].replace('\\','/')).casefold()
    if key not in dedup or row.get('date','')>=dedup[key].get('date',''):dedup[key]=row
assert len(raw)==15021 and len(dedup)==15020
groups=collections.defaultdict(list)
for path,row in dedup.items():
    arch='x64' if '/x64/' in path else 'x86'
    m=re.search(r'_(eq_nop_pii|eq_nop_bcf|eq_nop_ibp|nop_eq|eq_nop|eq_pii|eq_bcf|eq_ibp|nop_pii|nop_bcf|nop_ibp|nop|eq|pii|bcf|ibp)_\d+\.bin$',path)
    assert m,path
    tech=m.group(1).replace('nop_eq','eq_nop')
    assert row['total_scans']>0
    groups[arch,tech].append(100*row['malicious']/row['total_scans'])
rates={(a,t):sum(v)/len(v) for (a,t),v in groups.items()}
means={a:sum(rates[a,t] for t in categories)/15 for a in ['x64','x86']}
with (EVIDENCE/'historical_detection_reanalysis.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['arch','configuration','distinct_file_paths','mean_engine_detection_pct'])
    for a in ['x64','x86']:
        for t in categories:w.writerow([a,t,len(groups[a,t]),rates[a,t]])

main=original('main.tex')
main=main.replace(r'\maketitle',r'''\maketitle
\begingroup
\renewcommand{\thefootnote}{}
\footnotetext{\raggedright Extended and revised version of our SECRYPT 2026 paper~\cite{zone_secrypt_2026}, DOI: \href{https://doi.org/10.5220/0015170600004103}{10.5220/0015170600004103}.}
\endgroup''')
main=between(main,r'\draftnote{Historical detection-plot', 'This section restates', '')
main=main.replace('This section restates the protocol and results of the conference paper~\\cite{zone_secrypt_2026}. It introduces no additional measurements.',
'''This section summarizes the conference study~\\cite{zone_secrypt_2026}.
Figure~\\ref{fig:all_payloads} reaggregates its retained scan records with
corrected configuration labels; no new scans are included.''')
main=main.replace('Figure~\\ref{fig:all_payloads} presents the published transformed-file results.',
'''Figure~\\ref{fig:all_payloads} reports a reanalysis of 15,020 distinct
file paths from 15,021 saved records, retaining the latest record for the
repeated path. Each file uses its recorded engine-response denominator.''')

fig=next(m.group(0) for m in re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}',main,re.S) if r'\label{fig:all_payloads}' in m.group(0))
newfig=fig
for arch,color in [('x64','orange'),('x86','blue')]:
    # Replace only the relevant plotted series, labels, and its reference line.
    series=re.search(r'\\addplot\[only marks[^\]]*'+color+r'[^\n]*\n\\addlegendentry\{'+arch+r'\}.*?(?=\\addplot|\\end\{axis\})',newfig,re.S)
    assert series,arch
    block=series.group(0)
    coords=' '.join(f'({i},{rates[arch,t]:.6f})' for i,t in enumerate(categories))
    block=re.sub(r'coordinates \{[^}]*\}',lambda m:'coordinates {'+coords+'}',block,count=1)
    def node(m):
        i=int(m.group(1));v=rates[arch,categories[i]]
        return f'at (axis cs:{i},{v:.6f}) {{{v:.2f}}};'
    block=re.sub(r'at \(axis cs:(\d+),[-\d.]+\) \{[-\d.]+\};',node,block)
    newfig=newfig[:series.start()]+block+newfig[series.end():]
    newfig=re.sub(r'(\\addplot\['+color+r'[^\n]*forget plot\] coordinates )\{[^}]*\}',lambda m:m.group(1)+f'{{(0,{means[arch]:.6f}) (14,{means[arch]:.6f})}}',newfig)
newcaption=r'''Reanalysis of the historical raw-file scans of~\cite{zone_secrypt_2026}.
Configuration labels follow the file records; duplicate paths are counted once.
Dashed lines are equal-weight means over the 15 configurations (x64: '''+f'{means["x64"]:.2f}'+r'''\%; x86: '''+f'{means["x86"]:.2f}'+r'''\%).'''
newfig=re.sub(r'\\caption\{.*?\}\n\\label\{fig:all_payloads\}',lambda m:'\\caption{'+newcaption+'}\n\\label{fig:all_payloads}',newfig,flags=re.S)
newfig=re.sub(r'\\Description\{.*?\}\n\\caption',lambda m:'\\Description{Historical detection rates reaggregated from deduplicated saved records, with configuration labels aligned to their filenames.}\n\\caption',newfig,flags=re.S)
main=main.replace(fig,newfig)

main=main.replace('The frequency vectors $A$ and $B$ represent the opcode distributions of an original file and its transformed variant. Their cosine similarity is:',
'''The historical assembly analysis compares corpus-level opcode-frequency
vectors for each architecture: $A$ aggregates original inputs and $B$
aggregates outputs of one configuration. The retained script extracts
instruction mnemonics. This is a corpus comparison, not an average of paired
original/variant similarities. Its cosine similarity is:''')
main=main.replace('Cosine similarity between original and transformed opcode-frequency vectors; the reference level is one.',
'Cosine similarity between original-corpus and configuration-level opcode-frequency vectors; the reference level is one.')

# Unknown interests must remain explicit until the authors confirm them.
main=main.replace(r'\emph{To be completed by the authors before submission.}',
r'\emph{Declaration pending confirmation by all authors.}')
availability=r'''
\subsubsection{Data and Artifact Availability.}
The Zone source repository is available at
\url{https://github.com/jakydibe/Zone}. Supplementary Material S1 contains
the numerical evidence for this article: configuration summaries,
per-cell and per-input outcomes, scan summaries, version provenance,
calculation notes, and checksums. It is supplied as a separate archive
with the manuscript; the public repository is not a frozen snapshot of
all experimental versions. The supplementary archive contains analysis
records, not executable payloads.
'''
main=main.replace(r'\end{credits}',availability+'\n'+r'\end{credits}')
save('main.tex',main)

table=original('sections/overall_working_table.tex')
table=table.replace('The final row is the unweighted\nmean over the 15 configurations, as in the historical presentation.',
'''Within each configuration, input weights are historical test counts.
The final row gives every configuration weight $1/15$, irrespective of
its sample count; it is not a pooled success/test ratio.''')
save('sections/overall_working_table.tex',table)
method=original('sections/extension_methodology.tex')
method=method.replace('imputed; detailed contributions are supplied with the artifact. A repeated execution of the same binary is not a new variant.',
'''imputed. The final table row is the arithmetic mean of the 15
configuration rates, not weighted by their sample counts. Detailed
contributions are supplied in Supplementary Material S1. Repeated
executions of one binary are not new variants.''')
method=method.replace('artifact and are not a controlled comparison of engine versions.',
'''artifact. The native x86 IBP result therefore characterizes that recorded
version; no current-version retest is available, and no version-improvement
claim is inferred from comparing these campaigns.''')
save('sections/extension_methodology.tex',method)
llm=original('sections/extension_llm.tex')
llm=llm.replace("The requested model is \\texttt{deepseek-flash}; local version names come\nfrom the client's alias table, without independent provider confirmation.",
'''The requested model is \\texttt{deepseek-flash}. Provider documentation
accessed on 15 November 2026 maps this alias to DeepSeek-V4.1-Flash~\\cite{deepseek_models}.
The experiment records retain the alias, not an independently verified
provider snapshot for each call.''')
save('sections/extension_llm.tex',llm)
bib=original('bibliography.bib')+r'''

@misc{deepseek_models,
  author = {{DeepSeek}},
  title = {Lists Models},
  howpublished = {Official API documentation},
  url = {https://api-docs.deepseek.com/api/list-models/},
  note = {Accessed 15 November 2026}
}
'''
save('bibliography.bib',bib)

# Prepare an inventory; no permission has been represented as granted.
inventory=[]
for env,kind in [('table','Table'),('figure','Figure'),('lstlisting','Listing'),('algorithm','Algorithm')]:
    number=0
    for m in re.finditer(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}',main,re.S):
        number+=1
        if 'zone_secrypt_2026' not in m.group(0):continue
        lab=re.search(r'\\label\{([^}]+)\}',m.group(0))
        inventory.append([f'{kind} {number}',lab.group(1) if lab else '', '10.5220/0015170600004103','Reproduced, adapted, or redrawn; see caption','Not confirmed; check signed agreement or obtain written permission'])
with (SUPPORT/'REUSE_INVENTORY.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['current_object','label','source_doi','reuse','permission_status']);w.writerows(inventory)

(SUPPORT/'PERMISSION_REQUEST.txt').write_text('''Subject: Reuse permission for invited extended version of SECRYPT 2026 paper 195

Dear SECRYPT / SCITEPRESS Editorial Team,

We are preparing the invited revised and extended version of our paper:
Stefano Bistarelli, Jacopo Di Benedetto and Francesco Santini,
"On Automating the Obfuscation of Malware Payloads: Zone, a bin2bin Metamorphic Engine",
SECRYPT 2026, Volume 1, pp. 216-227,
DOI: 10.5220/0015170600004103.

The extended manuscript is intended for the Springer CCIS selected-papers volume.
It reuses or adapts Tables 1-6, Figures 1, 2 and 4-7, Listings 1-4, and Algorithm 1
from the conference paper. Original Figure 3 is not reproduced. The historical
detection plot is reaggregated from retained scan records with corrected labels;
the new overall working-rate table combines historical and updated measurements.
Every reused object cites the conference paper. An itemized inventory is attached.

Please confirm whether this reuse and adaptation are already covered by our
signed agreement or by the post-publication arrangement. If not, we request
permission for reproduction and adaptation in the printed and electronic
versions of the Springer CCIS chapter, with worldwide distribution in English.
Please specify any required credit line, conditions, or permission reference.

Thank you.
The authors
''',encoding='utf-8')

(SUPPORT/'REVIEWER_RESPONSE_IBP.txt').write_text('''Proposed response on native x86 IBP version coverage

We agree that a rerun with one common engine version would be necessary to
measure version-to-version improvement. The reported controlled native x86 IBP
experiment, however, was performed with the earlier implementation identified
in the supplementary provenance. It produced 17 binaries in 18 planned tests,
and none passed the complete-buffer check. No current-version rerun is available
in this evidence set. We retain all 18 cases and explicitly tie the result to
the tested version rather than infer that later LLM or wrapping outcomes
demonstrate a repair of native IBP. The revised methodology and Table 9 caption
make this scope explicit. The available records do not establish why a later
rerun was not performed; no retrospective justification is invented here.
''',encoding='utf-8')

(EVIDENCE/'BASELINE_RECONCILIATION.md').write_text('''# Baseline reconciliation - 15 November 2026

The historical working-rate figure was already consolidated into Table 12.
The detection plot now uses the retained results.json records rather than
the inconsistent category/value associations in the preparation manuscript.
There are 15,021 records and 15,020 distinct normalized file paths. The latest
record is retained for the repeated path. Each file uses its own total_scans
denominator; groups are derived from the transformation suffix in its filename.
The eq_nop display category corresponds to files labelled nop_eq. Reference
lines give the arithmetic mean of the 15 configuration rates. This is a
reanalysis of historical records, not a new scan campaign. Historical SGN
comparisons remain explicitly reported conference results.

The available create_var.py analysis was inspected, not executed. Its
disassemble_file function emits insn.mnemonic only. The tokenizer's comments
mention operands, but none are supplied on this path. For each architecture,
the script concatenates original mnemonic listings and separately concatenates
listings within a configuration before computing cosine similarity. The text
and caption now describe corpus-level mnemonic-frequency vectors. The
published similarity values are retained; this revision does not rerun the
historical binary-analysis experiment.
''',encoding='utf-8')
baseline_note='''# Baseline checks reconciled - 15 November 2026

Working rates are consolidated in Table 12 with provenance and weighting stated.
The historical detection chart has been reaggregated from deduplicated saved
records, with configuration labels derived from filenames. The manuscript
identifies this as a reanalysis rather than a new scan campaign.

The cosine description now matches the available analysis path: corpus-level
mnemonic-frequency vectors, not pairwise full-token vectors. Numeric values
remain the reported historical values. See evidence/editorial_20261115/
BASELINE_RECONCILIATION.md and historical_detection_reanalysis.csv.

The previous check list is preserved in before_editorial_corrections_20261115/.
Reuse permission and the authors' competing-interests declaration remain
separate unresolved editorial items; they are not implied by these checks.
'''
save('BASELINE_CHECKS.md',baseline_note)

# Numerical evidence supplement: explicit allowlist, no binary or engine files.
datafiles=[
 'evidence/native.csv','evidence/llm_benign.csv','evidence/classifier.csv','evidence/wrap_full_corpus.csv',
 'evidence/completed_20261114/llm_cells.csv','evidence/completed_20261114/llm_by_condition.csv',
 'evidence/completed_20261114/vt_by_membership.csv','evidence/completed_20261114/CALCULATION_NOTES.md',
 'evidence/clarity_revision/recovery_by_payload.csv','evidence/clarity_revision/recovery_by_technique.csv',
 'evidence/clarity_revision/recovery_summary.json','evidence/clarity_revision/REPRODUCIBILITY_NOTES.md',
 'evidence/followup_20261115/overall_working_rate.csv','evidence/followup_20261115/overall_working_rate_contributions.csv',
 'evidence/followup_20261115/scan_overall.csv','evidence/followup_20261115/NOTES.md',
 'evidence/editorial_20261115/historical_detection_reanalysis.csv','evidence/editorial_20261115/BASELINE_RECONCILIATION.md'
]
provenance=json.loads((PAPER/'evidence/SOURCES.json').read_text(encoding='utf-8'))
(EVIDENCE/'version_provenance.json').write_text(json.dumps({'retained_source_inventory':provenance,'historical_record_sha256':sha(ROOT/'results.json'),'available_metric_script_sha256':sha(ROOT/'create_var.py')},indent=2)+'\n',encoding='utf-8')
datafiles.append('evidence/editorial_20261115/version_provenance.json')
manifest={p:{'sha256':sha(PAPER/p),'bytes':(PAPER/p).stat().st_size} for p in datafiles}
readme='''# Supplementary Material S1 - Zone numerical evidence

This archive accompanies the revised manuscript. It provides numerical records,
derived tables, provenance, and calculation notes for inspecting the reported
results. It is not a frozen executable release of the engine and does not
contain payload binaries. The public Zone repository is linked in the paper.

File map:
- evidence/native.csv and llm_benign.csv: controlled functional benchmark.
- evidence/classifier.csv: annotated classification benchmark.
- evidence/wrap_full_corpus.csv: full-corpus wrapping outcomes.
- evidence/completed_20261114/: 816 LLM cells, grouped outcomes, scan membership
  and calculation notes. All cell outcomes remain, including failures.
- evidence/clarity_revision/: recovery outcomes by input and configuration.
- evidence/followup_20261115/: weighted overall update, per-input contributions,
  overall scan rates and accounting notes.
- evidence/editorial_20261115/: historical detection reanalysis and provenance.

The mean row of the overall working-rate table assigns each configuration 1/15
weight. Input rates within each configuration retain historical test-count
weights. These two aggregation levels must not be conflated.

Some calculation notes name raw source files maintained by the authors; those
files are documented through provenance but are not all included here. S1
supports inspection of numerical summaries, not regeneration of every binary
or rerunning every experiment. CHECKSUMS.json records the included file hashes.
'''
with zipfile.ZipFile(SUPPORT/'Supplementary_Material_S1.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in datafiles:z.write(PAPER/name,name)
    z.writestr('README.md',readme)
    z.writestr('CHECKSUMS.json',json.dumps(manifest,indent=2)+'\n')

audit={'historical_records':len(raw),'deduplicated_file_paths':len(dedup),'historical_detection_configuration_means':means,'rewriting_engines_modified':False,'new_payload_executions_or_scans':False,'interests_status':'User could not confirm; declaration remains pending','permission_status':'Not confirmed; request and inventory prepared, not sent','model_alias_source':'https://api-docs.deepseek.com/api/list-models/','publisher_rights_source':'https://portal.insticc.org/copyright','new_data_table_values_changed':False,'historical_metric_script_sha256':sha(ROOT/'create_var.py'),'historical_record_sha256':sha(ROOT/'results.json'),'supplement_included_files':len(datafiles)}
(EVIDENCE/'EDITORIAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
