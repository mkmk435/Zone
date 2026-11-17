"""Revise manuscript and tabulate existing records. No engine or payload execution."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import shutil

ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'tmp/ccis_rewrite_20261114'
BACK=P/'before_followup_20261115'
BACK.mkdir(exist_ok=True)
for f in [P/'main.tex',P/'main.pdf',*list((P/'sections').glob('*.tex'))]:
    dest=BACK/f.relative_to(P);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copy2(f,dest)
E=P/'evidence/followup_20261115';E.mkdir(parents=True,exist_ok=True)

def old(rel):return (BACK/rel).read_text(encoding='utf-8')
def put(rel,text):
    f=P/rel;f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(text.strip()+'\n',encoding='utf-8')
def save_csv(name,rows):
    with (E/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

TECHS=['nop','eq','pii','bcf','ibp','eq_nop_pii','eq_nop_bcf','eq_nop_ibp',
       'nop_eq','nop_pii','nop_bcf','nop_ibp','eq_pii','eq_bcf','eq_ibp']
tests=list(csv.DictReader((ROOT/'working_rate_unified_tests.csv').open(encoding='utf-8-sig',newline='')))
agg=collections.defaultdict(lambda:[0,0])
for r in tests:
    if r['dataset'] not in ['old_original','new_xd_ebi'] or r['technique'] not in TECHS:continue
    k=(r['dataset'],r['arch'],r['payload'],r['technique'])
    agg[k][0]+=r['status']=='OK';agg[k][1]+=1
overall=[];contributions=[]
for arch in ['x64','x86']:
    for tech in TECHS:
        keys=sorted(k for k in agg if k[0]=='old_original' and k[1]==arch and k[3]==tech)
        denom=sum(agg[k][1] for k in keys)
        hist=sum(agg[k][0] for k in keys)/denom
        updated_numerator=0.0
        for k in keys:
            key2=('new_xd_ebi',*k[1:]);chosen=agg.get(key2,agg[k]);weight=agg[k][1]
            contribution=weight*chosen[0]/chosen[1]
            updated_numerator+=contribution
            contributions.append(dict(arch=arch,payload=k[2],technique=tech,
                historical_passed=agg[k][0],historical_tested=weight,
                used_updated=key2 in agg,selected_passed=chosen[0],selected_tested=chosen[1],
                weighted_success_contribution=contribution))
        updated=updated_numerator/denom
        assert 0<=hist<=1 and 0<=updated<=1
        overall.append(dict(arch=arch,technique=tech,historical_rate_pct=100*hist,
            reconstructed_rate_pct=100*updated,historical_test_count=denom,
            historical_input_count=len(keys)))
save_csv('overall_working_rate.csv',overall)
save_csv('overall_working_rate_contributions.csv',contributions)
means={a:{'historical':sum(r['historical_rate_pct'] for r in overall if r['arch']==a)/15,
          'reconstructed':sum(r['reconstructed_rate_pct'] for r in overall if r['arch']==a)/15} for a in ['x64','x86']}

table=[]
for t in TECHS:
    a=next(r for r in overall if r['arch']=='x64' and r['technique']==t)
    b=next(r for r in overall if r['arch']=='x86' and r['technique']==t)
    label=t.upper().replace('_','+')
    table.append(f"{label} & {a['historical_rate_pct']:.1f} & {a['reconstructed_rate_pct']:.1f} & {b['historical_rate_pct']:.1f} & {b['reconstructed_rate_pct']:.1f} \\\\")
table.append(f"\\midrule\n\\textbf{{Mean}} & {means['x64']['historical']:.1f} & {means['x64']['reconstructed']:.1f} & {means['x86']['historical']:.1f} & {means['x86']['reconstructed']:.1f} \\\\")
put('sections/overall_working_table.tex',r'''
\begin{table}[t]
\caption{Overall working rates (\%): historical measurements and a
reconstructed update using the recovery tests. The update replaces rates
only for the 49 retested inputs and retains historical rates for the rest.
Historical input weights are held fixed. The final row is the unweighted
mean over the 15 configurations, as in the historical presentation.
This is a combined evidence summary, not a new execution of the full corpus.}
\label{tab:overall_working_update}
\centering\small\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
 & \multicolumn{2}{c}{x64} & \multicolumn{2}{c}{x86} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Configuration & Historical & Updated & Historical & Updated \\
\midrule
'''+ '\n'.join(table)+r'''
\bottomrule
\end{tabular}
\end{table}
''')

# Archival details remain available without interrupting the main exposition.
prior_results=old('sections/extension_results.tex')
pilot_start=prior_results.index(r'\subsection{Relationship to Earlier Pilots')
put('evidence/followup_20261115/earlier_pilots.tex',prior_results[pilot_start:])
controlled_start=prior_results.index(r'\subsection{Functional Tests')
controlled_end=prior_results.index(r'\subsection{Wrapping on All',controlled_start)
put('evidence/followup_20261115/controlled_benchmark_details.tex',prior_results[controlled_start:controlled_end])
scan_start=prior_results.index(r'\subsection{Detection Rates')
put('evidence/followup_20261115/scan_details_previous_layout.tex',prior_results[scan_start:pilot_start])

# Configuration provenance: shared client, no overrides in experiment drivers.
client=ROOT/'bench/engines/2026-11-13_block3/llm_technique.py'
client_text=client.read_text(encoding='utf-8')
assert 'temperature: float = 0.2' in client_text
request=client_text[client_text.index('def _request('):client_text.index('data = json.dumps',client_text.index('def _request('))]
assert '"temperature": self.options.temperature' in request
assert '"seed"' not in request and '"top_p"' not in request
drivers=[ROOT/f for f in ['bench/run_llm.py','bench/run_llm_data.py','bench/run_classifier_compare.py',
                         'tmp/campaign/build_llm.py','tmp/campaign/run_data_compare.py']]
assert all('temperature' not in f.read_text(encoding='utf-8') for f in drivers)

data=old('sections/extension_code_data.tex')
data=data.replace('pattern-based rules look for candidate strings and graph-inferred data.',r'''pattern-based rules recognize printable ASCII and UTF-16LE string
candidates, including their terminators, and consider regions identified
as data by the control-flow analysis. Candidates overlapping confirmed
instruction bytes are filtered out. These rules supply recognizable
patterns and supporting evidence; an unexplored region alone is not
sufficient to classify it as data.''')
data=data.replace('locations are known. Integrity checks verify the preserved contents.',r'''locations are known. Integrity checks compare the bytes of each retained
data region with the original saved bytes at its final location. Supported
address references are also checked against their expected destinations;
a mismatch causes the construction to fail.''')
data=data.replace('The classifier also supports correction requests. If a proposed data\ninterval extends beyond the input, for example, validation can return that\ndiagnostic and request a revised interval set.',r'''Correction requests append the rejected answer and the validator's error
message to the conversation, then ask the LLM for a revised proposal.
For example, a data interval extending beyond the input is returned with
an out-of-bounds diagnostic. This cycle is bounded by the configured
attempt limit.''')
put('sections/extension_code_data.tex',data)

llm=old('sections/extension_llm.tex')
llm=llm.replace('wrapping remain native engine operations.',r'''wrapping remain native engine operations. This is an implementation scope
choice: the LLM interface defines requests and validators for the four
listed families. PII and wrapping also impose constraints on the binary
layout and encoding that this interface does not implement. Their absence
from LLM mode is not a claim that a model could never propose them.''')
llm=llm.replace('kept separately, so the model works on the instruction representation.',r'''kept separately, so the model proposes changes to the instruction
representation while the pipeline retains the exact data contents.
Identification may itself use an LLM, but copying retained data and checking
its contents are deterministic operations. This separation makes the role
being evaluated explicit. An end-to-end model that also rewrites data would
be a different design and is not compared in these experiments.''')
llm=llm.replace('Neither test selects generations within these two experiments. The earlier\nMessageBox pilot did use its dialog check during generation and is therefore\nkept separate.',
                'The functional test is applied after generation in these experiments.')
llm=llm.replace('model designation available in these records.',r'''model designation available in these records. Both LLM roles use a
requested temperature of 0.2; the client supplies neither a sampling seed
nor an explicit top-p setting. Repeated requests are therefore not treated
as deterministic reproductions.''')
put('sections/extension_llm.tex',llm)

wrap=old('sections/extension_wrapping.tex')
wrap=wrap.replace('representation; the implementation retains these in separate, unwrapped\nregions.',r'''representation. For example, an instruction sequence longer than the
available operand field does not fit inside that container. The
implementation retains unsupported cases in ordinary, unwrapped regions.''')
start=wrap.index('Data preparation remains necessary.')
end=wrap.index(r'\subsection{How Wrapping',start)
wrap=wrap[:start]+wrap[end:]
put('sections/extension_wrapping.tex',wrap)

method=old('sections/extension_methodology.tex')
method=method.replace('The native controlled benchmark uses three runs',r'''The requested LLM temperature is 0.2 for transformation and data
identification. The client does not set a sampling seed or top-p. These
settings describe the submitted requests; the campaign does not assume
identical answers on repeated calls.

The native controlled benchmark uses three runs''')
start=method.index(r'\paragraph{Similarity.}')
end=method.index(r'\paragraph{Detection rate.}',start)
method=method[:start]+r'''\paragraph{Representation measurements.}
The historical cosine and entropy measurements retain their original
definitions. The LLM client additionally records a SequenceMatcher score
between its prepared input listing and the returned listing. It is an
internal sequence-overlap diagnostic, with NOP-like operations filtered in
the NOP condition, and is reported in the supplementary records rather
than used as a substitute for the historical similarity measures.

'''+method[end:]
start=method.index(r'\paragraph{Detection rate.}')
end=method.index(r'\paragraph{Diversity and resources.}',start)
method=method[:start]+r'''\paragraph{Detection rate.}
We use the same engine-level definition as the historical evaluation:
$d_i=m_i/a_i$, where $m_i$ is the number of malicious responses for file
$i$ and $a_i$ is its total reported engine-response count. Tables report
$\overline d$, the mean across files, as a percentage. For example,
3 malicious responses among 75 give a detection rate of 4\%.
Nonempty current reports contain 75 responses. Unsupported formats,
timeouts, and failed analyses remain in that denominator, consistently
with the historical convention; their breakdown and report-completeness
checks are included in the supplementary records. Missing reports are not
assigned a zero detection rate. Each distinct output hash is scanned once.

'''+method[end:]
# Add transparent standardized weights for the requested overall update.
needle='recorded tests, matching the available historical\nrecords.'
method=method.replace(needle,r'''recorded tests, matching the available historical
records. The overall update in Table~\ref{tab:overall_working_update}
combines the new rates for retested inputs with the retained historical
rates for other inputs. Each input keeps its historical test-count weight.
This avoids changing the composition of the x86 average merely because
the new campaign uses fewer repetitions. No missing historical outcome is
imputed; detailed contributions are supplied with the artifact.''')
method=method.replace('The recovery figure compares\nsuccessful tests with recorded tests',
                      'The selected-cohort comparison divides\nsuccessful tests by recorded tests')
for word,num in [('thirteen','13'),('nineteen','19'),('fifteen','15')]:
    method=re.sub(r'\b'+word+r'\b',num,method)
put('sections/extension_methodology.tex',method)

results=prior_results[:pilot_start]
results=results.replace('(Figure~\\ref{fig:recovery_working})',
                        '(Section~\\ref{sec:recovery})')
results=results.replace('Without independent annotations, neither 9/19 nor 16/19 measures classifier\naccuracy.',
'''These two values describe agreement between the methods, whereas
accuracy against known answers is measured on the annotated programs.''')
results=results.replace('An earlier three-case benign\ncheck records another 9/9 exact LLM results; those repetitions are not\nadded to the six-fixture population.', '')
start=results.index(r'\subsection{Functional Tests')
end=results.index(r'\subsection{Wrapping on All',start)
controlled=r'''\subsection{Functional Tests on 13 Controlled Programs}
The functional benchmark asks whether a transformed program still produces
its expected output. Each native configuration is run three times per
input: 21 tests on the 7 x64 programs and 18 on the 6 x86 programs.
Table~\ref{tab:controlled_functional} shows successful tests over planned
tests. It combines the two LLM prompting conditions to keep the functional
comparison readable; their separate results are supplied in the supplement.

\begin{table}[t]
\caption{Functional success on the controlled programs. Each entry is
successful tests/planned tests. LLM columns combine zero-shot and two-shot
requests at temperature 0.2. PII is outside this benchmark; wrapping is
native-only. The native x86 IBP row refers to the recorded earlier version.}
\label{tab:controlled_functional}
\centering\small\setlength{\tabcolsep}{7pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
 & \multicolumn{2}{c}{Native} & \multicolumn{2}{c}{LLM} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Family & x64 & x86 & x64 & x86 \\
\midrule
EQ & 21/21 & 18/18 & 42/42 & 36/36 \\
NOP & 21/21 & 18/18 & 42/42 & 36/36 \\
BCF & 21/21 & 18/18 & 42/42 & 36/36 \\
IBP & 21/21 & 0/18 & 41/42 & 30/36 \\
Wrapping & 21/21 & 18/18 & -- & -- \\
\bottomrule
\end{tabular}
\end{table}

All native x64 tests pass. Native x86 EQ, NOP, BCF, and wrapping also
pass; the recorded native x86 IBP configuration produces 17 binaries from
18 attempts, but none passes the complete-buffer test.

The LLM produces 305 accepted outputs from 312 requests (97.8\%), and
every accepted output has the correct buffer. The remaining seven requests
comprise five structural-validation rejections and two transport errors.
Thus the main result is functional preservation for all accepted outputs
on these controlled inputs, with construction availability recorded separately.

Repeated output hashes are most visible in EQ. These inputs are short,
offer few locations for substitutions, and are subject to the restricted
set of supported transformations. This provides a straightforward
explanation for limited diversity on this suite; different requests need
not produce different accepted instruction sequences. Detailed hashes,
per-shot outcomes, time, and cost remain available in the supplement.

'''
results=results[:start]+controlled+results[end:]
start=results.index('The logs include incomplete instruction interpretation')
end=results.index(r'\subsection{Completed LLM',start)
results=results[:start]+r'''The construction logs include incomplete instruction interpretation and
inconsistent address references. These failure stages have a direct
relationship to preparation: interpreting embedded data as instructions
can prevent a complete valid disassembly, and a reference that no longer
points to the intended location fails the consistency check after layout
changes. The logs identify these symptoms; they do not assign one common
cause to every failed execution.

'''+results[end:]
results=results.replace('The 350 built outputs contain 323 distinct hashes. Their mean recorded\nsequence similarity is 0.906. The median retained-run duration is',
                        'The 350 built outputs contain 323 distinct hashes. The median retained-run duration is')
start=results.index(r'\subsection{Working-Rate Improvement')
end=results.index(r'\subsection{Detection Rates',start)
recovery=r'''\subsection{Updated Working Rates by Transformation}
\label{sec:recovery}
The recovery campaign retests 49 previously low-rate inputs: 13 x64 and
36 x86. On this selected subset, the x64 working rate rises from
23/1,941 (1.2\%) to 1,564/1,950 (80.2\%). The x86 rate rises from
772/5,195 (14.9\%) to 699/2,700 (25.9\%). These observations measure
the updated implementation and test harness together.

Table~\ref{tab:overall_working_update} places the recovery results back
into the overall historical population. For each transformation, the
retested inputs use their updated rates; other inputs retain their
historical rates. We keep the original input weights so that the reduction
from generally ten to five x86 repetitions cannot increase the overall
rate merely by reducing the influence of difficult inputs.

The reconstructed mean across the 15 configurations increases from
55.6\% to 82.6\% on x64 and from 45.0\% to 50.3\% on x86.
These are summaries of combined historical and updated evidence. The
original published figure is retained as the baseline; the update appears
here with its construction stated explicitly.

\input{sections/overall_working_table}

The lower x86 recovery rate concerns a deliberately difficult subset,
not all x86 inputs. Of its 36 inputs, 13 still have no successful
transformed variant. Preparation-only controls pass 340/360 tests (94.4\%),
whereas adding the native transformations yields 699/2,700 (25.9\%).
This separates successful preparation from the additional transformation
failures; it does not support attributing every remaining failure to data
identification. The dominant recorded execution symptom is an access
violation, which alone does not identify the underlying implementation error.

The improvement is substantially stronger on x64. Even excluding
MessageBox, whose test recognition was corrected, the selected x64 rate
rises from 19/1,791 (1.1\%) to 1,414/1,800 (78.6\%). Per-input and
per-configuration counts, including the selected-subset comparison, remain
available in the supplementary records.

'''
results=results[:start]+recovery+results[end:]

# Static detection results: use the existing raw reports only, no service calls.
manifest=json.loads((ROOT/'vt_manifest_campaign.json').read_text())
reports={r['sha256']:r for r in (json.loads(line) for line in (ROOT/'tmp/vt_results_campaign.jsonl').read_text().splitlines()) if r.get('status')=='completed'}
llm_rows=list(csv.DictReader((ROOT/'tmp/campaign/llm_summary.csv').open(encoding='utf-8-sig',newline='')))
conditions=[]
def scan_row(label,entries):
    hh={r['sha256'] for r in entries}
    valid=[reports[h] for h in hh if reports[h].get('total',0)>0]
    assert valid
    return dict(condition=label,output_files=len(entries),unique_hashes=len(hh),valid_reports=len(valid),
                mean_engine_detection_pct=100*sum(r['malicious']/r['total'] for r in valid)/len(valid),
                detected_file_pct=100*sum(r['malicious']>0 for r in valid)/len(valid),
                mean_malicious_count=sum(r['malicious'] for r in valid)/len(valid))
conditions.append(scan_row('Wrapping',[r for r in manifest if r['group']=='wrap']))
for arch in ['x64','x86']:
    conditions.append(scan_row('LLM '+arch,[r for r in manifest if r['group']=='llm' and r['arch']==arch]))
conditions.append(scan_row('LLM overall',[r for r in manifest if r['group']=='llm']))
working_hashes={r['sha256'] for r in llm_rows if r['worked']=='1' and r['built']=='1'}
conditions.append(scan_row('LLM working outputs',[r for r in manifest if r['group']=='llm' and r['sha256'] in working_hashes]))
save_csv('scan_overall.csv',conditions)
scan_table=[]
for r in conditions:
    prefix=r'\midrule'+'\n' if r['condition']=='LLM overall' else ''
    scan_table.append(prefix+f"{r['condition']} & {r['output_files']} & {r['unique_hashes']} & {r['valid_reports']} & {r['mean_engine_detection_pct']:.2f} \\\\")
start=results.index(r'\subsection{Detection Rates')
results=results[:start]+r'''\subsection{Overall Detection Rates for Wrapping and LLM Transformation}
The detection evaluation covers the outputs from the full 102-input LLM
campaign, not only the separate 19-input data-identification experiment.
Of the 816 planned LLM cells, 350 produce binaries, representing 323
distinct hashes. Table~\ref{tab:current_scans} reports the mean engine
detection rate using the same definition as the historical paper.

\begin{table}[t]
\caption{Static detection of the current outputs. Files: produced binaries;
hashes: distinct contents; reports: nonempty scan results. DR is the mean
percentage of engine responses marked malicious.
The working-output row is a subset of the overall LLM row. Report
completeness and response-category details are supplied in the supplement.}
\label{tab:current_scans}
\centering\small\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
Condition & Files & Hashes & Reports & DR (\%) \\
\midrule
'''+ '\n'.join(scan_table)+r'''
\bottomrule
\end{tabular}
\end{table}

The overall LLM mean detection rate is 5.06\% across 322 nonempty reports,
equivalent to 3.80 malicious engine responses per file. The 275 outputs
that pass the functional test correspond to 263 distinct hashes and have
a mean detection rate of 5.89\%. Showing both rows distinguishes all
constructed outputs from the functionally successful subset.

All 207 distinct wrapping outputs have nonempty reports with no malicious
responses. These are static raw-file measurements; the engine-response
denominator follows the historical convention described in the methodology.
The separate data-identification scans and earlier pilot campaigns are
archived in the supplementary evidence rather than pooled into these results.
'''
# Use digits consistently for experimental population sizes.
for word,num in [('nineteen','19'),('thirteen','13'),('eighteen','18'),('fourteen','14'),('fifteen','15'),('sixty','60')]:
    results=re.sub(r'\b'+word+r'\b',num,results)
put('sections/extension_results.tex',results)

discussion=old('sections/extension_discussion.tex')
discussion=discussion.replace('The native x86 IBP failure also shows that a controlled\nprogram can expose an implementation problem directly.',
'''The recorded native x86 IBP result remains associated with its tested
version; a future corrected implementation requires a separately identified
evaluation.''')
discussion=discussion.replace('The recovery comparison provides direct evidence',
                             'The selected-subset recovery comparison provides direct evidence')
for word,num in [('thirteen','13'),('nineteen','19')]:
    discussion=re.sub(r'\b'+word+r'\b',num,discussion)
put('sections/extension_discussion.tex',discussion)
main=old('main.tex')
main=main.replace(r'Figure~\ref{fig:recovery_working} adds the updated before/after comparison for the 49 retested low-rate payloads.',
                 r'Table~\ref{tab:overall_working_update} adds a separately identified overall update using the 49 retested low-rate inputs and retained historical evidence for the rest.')
main=main.replace('Six annotated\nbenign fixtures','Six annotated\nbenign programs')
main=re.sub(r'\bthirteen\b','13',main)
main=main.replace('Current raw-file scans report no malicious verdicts for\n207 distinct wrapping outputs and at least one malicious verdict for\n221 of 322 evaluable LLM-transformed outputs; one additional LLM report\nis empty.',
'''Current raw-file scans give a mean engine detection rate of 0\\%
for 207 distinct wrapping outputs and 5.06\\% across 322 nonempty reports
for LLM-transformed outputs.''')
put('main.tex',main)

notes=r'''
Supplementary accounting and measurement definitions - 15 November 2026

1. Overall working rate. For input i and configuration t, let n_it be its
historical recorded test count, r_it its historical rate, and r'_it the
updated rate when available. The reconstructed rate is sum_i(n_it*r'_it) /
sum_i(n_it), using r_it for inputs not retested. This holds the original
input weights constant even when updated trials have fewer repetitions.
No new execution count is invented: fractional weighted contributions are
statistical weights, not observed successful executions. Missing historical
input/configuration cells receive no imputed observation or positive result.
PII-containing historical configurations have incomplete input coverage;
the update preserves that reported population. The table's mean row is the
unweighted mean across the same 15 configurations. Exact contributions are
in overall_working_rate_contributions.csv. This is not a full rerun of 102
inputs and is not a claim that the retained historical outputs were regenerated.

2. Temperature. The frozen client used by all three engine snapshots defines
temperature=0.2 and sends it in the request body. The experiment drivers do
not override it. The CLI construction uses the same default in both
architectures and both LLM roles. Neither sampling seed nor top_p is sent.
Per-call run summaries do not independently echo provider-side sampling
configuration; the evidence establishes the submitted client configuration.

3. Similarity. The client's SequenceMatcher score remains in saved records
and the archived detailed controlled-benchmark tables. It compares prepared
and returned instruction listings and filters NOP-like operations in the
NOP condition. It is not renamed as cosine similarity. No new historical-
metric cosine/entropy campaign was performed in this editorial revision.

4. Scan completeness. The campaign contains 549 unique submitted hashes and
549 completed-status records. One BCF/0 LLM report has zero total responses
and is treated as missing, leaving 548 usable reports (322 LLM, 207 wrapping,
19 data-only). The missing hash is
4d7ddb053e7f2234c392c9f6ad3cf7d019941b99535c1b949ca2e315dcc4e007.
It is not classified as undetected. No new upload, reanalysis, or API call
was made in this revision. Its recorded functional test failed. Therefore
all 263 hashes belonging to functionally successful LLM outputs have reports.

5. Detection denominator. The mean DR uses malicious / total reported
responses, with 75 responses per nonempty report, matching the historical
denominator convention. Unsupported/timeouts/failures remain in that total.
For wrapping these categories are 3,090 / 132 / 29 across 15,525 responses.
Across all current groups they are 8,184 / 298 / 74. These are not benign
verdicts. The supplementary scan_overall.csv also retains detected-file rate
(q) and mean malicious-engine count; q is removed from the main table.

6. Data-only scans. The separate 19-output LLM-data group has 19 detected
hashes, mean 20.63 malicious responses and mean engine DR 27.51%. These scans
were already present, not repeated for this revision. They do not replace
the 350-output evaluation of the LLM transformation campaign on 102 inputs.

7. Earlier pilots. earlier_pilots.tex preserves the former section 12.7:
the earlier 220-hash cohort, 13 original controls, MessageBox pilot selection
policy, and historical artifact-availability audit. Those records are not
mixed into the completed campaign. controlled_benchmark_details.tex preserves
the previous native and per-shot LLM tables, including similarity and costs.

8. Scope of this revision. All changes are editorial or offline statistical
analyses of saved data. No rewriting engine was modified, and no payload was
generated or executed. The recorded native x86 IBP result is unchanged.
'''
put('evidence/followup_20261115/NOTES.md',notes)
audit={'means':means,'scan_summary':conditions,'temperature_requested':0.2,
       'sampling_seed_supplied':False,'top_p_supplied':False,
       'engine_modified':False,'payloads_executed':False,'new_scans':False,
       'source_hashes':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in
           [ROOT/'working_rate_unified_tests.csv',ROOT/'vt_manifest_campaign.json',ROOT/'tmp/vt_results_campaign.jsonl',client,*drivers]}}
(E/'SUMMARY.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps({'means':means,'scans':conditions},indent=2))
