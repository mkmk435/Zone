from pathlib import Path
import re,csv,json
root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
old=(root/'sections/extension_results.tex').read_text(encoding='utf-8')
tables={}
for t in re.findall(r'\\begin\{table\}.*?\\end\{table\}',old,re.S):
    tables[re.search(r'\\label\{([^}]+)\}',t).group(1)]=t
method=r'''\section{Experimental Design for the Extensions}\label{sec:methodology}
\subsection{Questions and Test Populations}
The extended evaluation asks four questions. Can the identification methods
find annotated data without misclassifying code? How often do native and
LLM transformations produce outputs that pass a functional test? How does
wrapping perform when moving from small controlled programs to the original
payload corpus? Finally, what do static scans show once duplicate outputs
and unsuccessful executions are accounted for?

We use three populations with different purposes. The \emph{benign
functional corpus} contains thirteen fixtures, meaning small programs
constructed to exercise specified behavior: seven x64 and six x86 cases
cover arithmetic, branches, loops, local calls, mixed control flow, strings,
and an additional x64 address-acquisition case. Each fixture writes to a
256-byte output buffer. The expected writes are declared before
transformation, and every other byte must retain its initial
\texttt{0xCC} value. This initial value is a \emph{sentinel}: changing it
reveals an unexpected write. A separate C runner returns the complete
buffer for comparison. All thirteen unmodified fixtures pass.

The \emph{classification corpus} contains six further fixtures with
independent reference data ranges: two programs containing multiple strings
(one per architecture), an x64 binary table, two programs containing no data,
and an x64 program whose instruction bytes resemble printable text. This
last case tests whether a classifier mistakes code for a string. Neither
the annotations nor the other classifier's answer is given to the model.
These are six distinct inputs; repetitions measure repeated outcomes on
those inputs rather than enlarging the program population.

The \emph{original payload corpus} contains the same 38 x64 and 64 x86
input files as the conference study. The current harness observes a dialog
for MessageBox, the prescribed connection event for network cases, or
clean process exit for the remaining cases. All 102 originals pass these
checks. These observables are narrower than complete output-buffer
equality: for example, observing a connection does not establish that every
later interaction is correct. We use ``working'' below to mean passing the
specified harness, not proven equivalence for every execution.

\subsection{Versions, Experimental Cells, and Call Accounting}
The code was frozen in three experiment snapshots. B1 (13 November 2026,
13:07 CET) supplies the benign native matrix and x64 LLM tests. B2
(14:05 CET) supplies the x86 LLM tests, x86 wrapping port, and classifier
tests. B3 supplies the full-payload campaign; the hashed rewriting and LLM
modules match B2. Consequently, a comparison between B1 x64 and B2 x86
does not isolate architecture alone.

The benign native matrix uses three runs per input and family. The benign
LLM matrix uses four families, two prompting conditions, and three
single-generation invocations per cell: $7\times4\times2\times3=168$
x64 invocations and $6\times4\times2\times3=144$ x86 invocations.
Rejected responses and transport failures remain in these totals; none is
replaced. Classification uses three LLM invocations and one symbolic run
per annotated fixture.

On the original corpus, wrapping uses three recorded randomization seeds
per input, giving $102\times3=306$ planned variants. It is assessed alone
after data preparation. The LLM matrix has $102\times4\times2=816$ cells,
targeting one accepted output per cell. The output-token ceiling is 65,536.
The saved ledger contains 830 run records: fourteen failed cells were
restarted and failed again. Four run records contain multiple generations;
the other records with known counts contain one. In total, 835 API calls
are recorded, with usage missing for one further run record. Two accepted
outputs required a second generation. Thus this completed campaign is not
a uniform one-generation-per-cell experiment. Cell-level reporting retains
all 816 cells, while cost accounting includes all 830 run records.

The data-identification payload comparison selects nineteen inputs
(thirteen x64, six x86) for which symbolic preparation extracts movable
data. Both methods use the shared deterministic handling and the same
functional harness. This selection evaluates their behavior on those
inputs; it cannot estimate identification accuracy across all 102 inputs.

\subsection{Construction, Functionality, and Identification Measures}
Let $N$ be the number of planned cases, $B$ the number of constructed
outputs, and $W$ the number passing the functional test. We distinguish
\[
  \text{build rate}=B/N,\qquad
  \text{overall working rate}=W/N,\qquad
  \text{working rate among builds}=W/B.
\]
For example, if ten cases yield eight binaries and six pass, these rates
are 80\%, 60\%, and 75\%, respectively. Reporting only the last value
would omit the two cases for which no binary was produced. Retesting a
failed binary does not create a new variant. $U$ denotes the number of
distinct output SHA-256 hashes, a measure of byte-level uniqueness.

For annotated fixtures, exact identification means that all reported data
intervals equal the reference intervals, with no missing or extra region.
We also count missed data bytes and code bytes incorrectly labeled as data.
Writing $P$ for predicted data bytes and $G$ for reference data bytes,
data precision is $|P\cap G|/|P|$ and recall is $|P\cap G|/|G|$.
Inputs without reference data are evaluated as empty-set decisions;
undefined ratios are not replaced by favorable scores. On unannotated
payloads we report interval agreement and final-output identity, not
accuracy. The available comparison matches symbolic extracted ranges
against reported LLM proposals, so it also compares different processing
stages.

\subsection{Representation, Static Scans, and Resource Use}
LLM sequence similarity compares the prepared input listing with an
accepted output using normalized mnemonic-and-operand signatures.
The \texttt{SequenceMatcher} ratio is $S=2M/(u+v)$, where $M$ is the
number of matched elements and $u,v$ are the sequence lengths~\cite{python_difflib}.
A larger value means more sequence overlap, not greater behavioral
correctness. NOP-like instructions are removed in the NOP condition;
therefore $S=1$ can coexist with changed binary bytes. Means include
accepted outputs only. This measure differs from the historical cosine
and entropy measurements in Section~\ref{sect:var_metrics}.

Static scanning has two units of analysis. For a file with $m_i$ malicious
engine responses and $a_i$ total reported responses, $d_i=m_i/a_i$.
Across files, $q$ is the fraction with at least one malicious response.
For example, one malicious response among 75 gives $d_i=1/75$, but the
file counts as detected when computing $q$. The present nonempty reports
contain 75 responses each, including unsupported formats, timeouts, and
failures; those categories are disclosed rather than interpreted as benign
verdicts. An empty report is not an evaluated negative and has no $d_i$.

Scans are deduplicated by hash. A hash shared by multiple transformation
conditions retains membership in each condition, so adding table rows
does not give the size of their union. We also separate passing and failing
LLM outputs before interpreting their scan results. Historical, earlier
pilot, and current scans remain separate cohorts because their inputs,
selection, and collection periods differ.

Time and token usage come from saved records; costs are local tariff
estimates, not invoices. We include failed and restarted runs in campaign
costs and do not treat run duration as pure API latency. The accompanying
evidence freezes the completed logs available on 14 November 2026, including
scan records through 01:17 CET, with source hashes and derived tables.
Earlier benchmark evidence is retained under its original snapshot.
'''
(root/'sections/extension_methodology.tex').write_text(method,encoding='utf-8')

pieces=[r'''\section{Results of the Extended Evaluation}\label{sec:extended_results}
The new results show a consistent distinction between small controlled
tests and the original payload corpus. The benign programs usually survive
transformation, whereas construction failures and execution failures become
substantial in the broader corpus. We first examine identification and
controlled behavior, then the completed wrapping and LLM campaigns, and
finally the scans of the outputs those campaigns produced.

\subsection{Can the Methods Identify Annotated Data?}
On the six classification fixtures, all eighteen LLM invocations and all
six symbolic runs return the exact reference interval sets
(Table~\ref{tab:new_classifier}). Both methods miss zero data bytes and
classify zero code bytes as data. The three fixtures containing data have
precision and recall equal to one; the other three correctly return no
data. All resulting executions pass their buffer checks. This includes
the deliberately misleading printable-code case, which is rejected as
data rather than extracted as a string.
''',tables['tab:new_classifier'],r'''
These results establish correctness on the six annotated examples, not on
arbitrary payloads. The nineteen selected original payloads illustrate
why that distinction matters. Both pipelines build 19/19 outputs and pass
17/19 harness checks. Their compared intervals agree in only 9/19 cases,
while their final binaries are byte-identical in 16/19. Shared filtering
and reference handling can therefore remove differences between proposals.
Without independent annotations, neither 9/19 nor 16/19 measures classifier
accuracy. The same two inputs fail in both arms, which is consistent with
a shared downstream limitation but does not by itself isolate its cause.

The recorded median durations are 123.95 seconds for symbolic preparation
and 59.88 seconds for the LLM arm. The latter's estimated cost is \$0.2218
over nineteen runs. Different preparation and caching work prevents a
controlled general speedup claim. On the separate six-fixture benchmark,
the total LLM cost is approximately \$0.0059. An earlier three-case benign
check records another 9/9 exact LLM results; those repetitions are not
added to the six-fixture population.

\subsection{Do Transformations Preserve the Benign Fixtures' Outputs?}
Table~\ref{tab:new_native} reports the native engine tests. For x64, each
family passes 21/21 runs (seven fixtures, three runs each). For x86, EQ,
NOP, and BCF pass 18/18. B1 IBP builds 17/18 binaries but none passes the
complete-buffer check; the remaining case raises a construction exception.
The B2 x86 wrapping implementation passes all 18/18. A constructed binary
can thus fail even these controlled observables, as the IBP row demonstrates.
''',tables['tab:new_native'],r'''
The LLM benchmark yields accepted outputs with correct buffers in 167/168
x64 invocations and 138/144 x86 invocations. Every accepted output passes
the external test. The seven unsuccessful invocations comprise five
family-specific validation rejections and two transport errors, rather
than seven executions with incorrect buffers. Table~\ref{tab:new_llm_benign}
keeps these failures in each condition's denominator.
''',tables['tab:new_llm_benign'],r'''
Across conditions, x64 produces 108 distinct hashes at an estimated cost
of \$0.5205; x86 produces 99 at \$0.5132. Hashes shared across conditions
explain why the union is smaller than the sum of row-wise uniqueness.
EQ frequently repeats outputs. NOP's similarity of 1.000 follows from
filtering NOP-like operations before matching; it does not indicate that
the binaries are identical.

For x86 IBP, the two-shot condition passes 17/18 invocations compared with
13/18 for zero-shot. For x64 IBP, the corresponding outcomes are 20/21 and
21/21. These are observations on six or seven fixtures under the stated
versions; they do not demonstrate a general advantage for two examples.

\subsection{Wrapping on All 102 Original Payloads}
The full B3 campaign attempts 306 variants, three per input. It constructs
243 binaries (79.4\% of planned cases), of which 170 pass the harness.
Thus $W/N=55.6$\%, whereas $W/B=70.0$\%. The distinction reveals a
substantial coverage gap that would be hidden by reporting only the
successful benign tests.
''',tables['tab:new_wrap_full'],r'''
The two architectures fail at different stages. On x64, 51 attempts do
not build, while all 63 constructed outputs pass. On x86, only twelve
attempts do not build, but 73 of the 180 constructed outputs fail the
harness. All 73 also fail the saved isolated retests; those retests are
not counted as additional variants. There are 207 distinct hashes among
the 243 binaries, showing that different seeds do not always produce
different bytes.

The logs include incomplete instruction interpretation and reference
consistency errors during construction. These symptoms accord with the
method's dependence on data preparation and supported relocation. They
do not establish a single cause for every execution failure. The earlier
selected x64 experiment, which built 200/260 variants and passed 198/200
constructed outputs, concerns a different and smaller population and is
not substituted for the full-corpus results.

\subsection{Completed LLM Transformation on the Original Corpus}
All 816 planned cells have an outcome. The campaign constructs 350
outputs, and 275 pass the external harness: a build rate of 42.9\%, an
overall working rate of 33.7\%, and a working rate among builds of 78.6\%.
Table~\ref{tab:payload_llm} shows the complete architecture/family/shot
breakdown. These are pipeline outcomes, including the retries described
in Section~\ref{sec:methodology}.
''']
rows=list(csv.DictReader((root/'evidence/completed_20261114/llm_by_condition.csv').open()))
t=r'''\begin{table}[t]
\caption{Completed B3 LLM payload matrix. $N$: planned cells; $B$: accepted
builds; $W$: builds passing the external harness; $U$: distinct built-output
hashes within the condition. Every planned cell is retained.}
\label{tab:payload_llm}
\centering\small
\begin{tabular}{@{}lllrrrr@{}}
\toprule
Arch. & Family & Shots & $N$ & $B$ & $W$ & $U$ \\
\midrule
'''
for i,r in enumerate(rows):
    if i==8:t+='\\midrule\n'
    t+=' & '.join([r['arch'],r['family'].upper(),r['shots'],r['cells'],r['built'],r['working'],r['unique']])+r' \\'+'\n'
t+=r'\bottomrule'+'\n'+r'\end{tabular}'+'\n'+r'\end{table}'+'\n'
pieces += [t,r'''
On x64, only 53/304 cells produce binaries, but 52/53 of those binaries
pass. On x86, 297/512 produce binaries and 223/297 pass. Construction is
therefore the principal observed bottleneck on x64, while x86 also has a
substantial failure rate after construction. The aggregate success on
benign fixtures does not predict these corpus-level outcomes.

Zero-shot produces 178 builds and 139 passing outputs from 408 cells;
two-shot produces 172 builds and 136 passing outputs from 408 cells.
Their overall working rates are 34.1\% and 33.3\%. These descriptive
differences offer no consistent evidence that adding two examples improves
the outcome. They also concern repeated configurations of the same inputs,
not 816 independent programs.

The 466 failed cells have recorded error categories comprising 245
disassembly/boundary errors, 74 validation errors, 53 output-length
terminations, one transport error, and 93 other errors. These labels
describe the observed failure stage, not proven root causes. In particular,
truncation means the response reaches its output limit before delivering
a complete acceptable listing; it is distinct from a generated program
failing at execution time.

The 350 built outputs contain 323 distinct hashes. Their mean recorded
sequence similarity is 0.906. The median retained-run duration is
160.3 seconds, including local processing. Summing the representative
record for each cell gives an estimated \$19.2700, but including the
fourteen restarted failed runs raises recorded campaign cost to
\$19.6258. The latter is the appropriate total for work actually recorded;
missing usage for one run prevents claiming complete billing coverage.

\subsection{Static Scans of the Completed Campaign}
The current manifest contains 612 file entries: 243 wrapping outputs,
350 LLM-transformed outputs, and nineteen outputs from LLM data handling.
They correspond to 549 distinct hashes. Every hash has a record marked
completed, but one LLM BCF zero-shot record contains no engine responses.
We exclude that empty result from measured scan rates: 548 hashes are
evaluable, with 75 reported responses each. Table~\ref{tab:current_scans}
retains each hash in every condition to which it belongs.
''']
vt=list(csv.DictReader((root/'evidence/completed_20261114/vt_by_membership.csv').open()))
t=r'''\begin{table}[t]
\caption{Current raw-file scans. $U$: distinct submitted hashes; $V$:
hashes with nonempty results; $D$: hashes with a malicious response;
$q=D/V$; $\overline m$: mean malicious-response count over $V$.
The empty BCF/0 report is excluded from $V$.}
\label{tab:current_scans}
\centering\small\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Condition & $U$ & $V$ & $D$ & $q$ (\%) & $\overline m$ \\
\midrule
'''
byname={r['group']:r for r in vt}
for name in ['wrap','llm_eq_s0','llm_eq_s2','llm_nop_s0','llm_nop_s2','llm_bcf_s0','llm_bcf_s2','llm_ibp_s0','llm_ibp_s2','lldata']:
    r=byname[name]
    label='Wrapping' if name=='wrap' else 'LLM data only' if name=='lldata' else 'LLM '+name.split('_')[1].upper()+' / '+name[-1]
    vals=[label,r['hashes'],r['evaluable'],r['detected'],f"{100*int(r['detected'])/int(r['evaluable']):.1f}",f"{float(r['mean_malicious']):.2f}"]
    t+=' & '.join(vals)+r' \\'+'\n'
t+=r'\bottomrule'+'\n'+r'\end{tabular}'+'\n'+r'\end{table}'+'\n'
pieces += [t,r'''
None of the 207 wrapping hashes receives a malicious response. Across
their 15,525 reported responses, however, 3,090 are format-unsupported,
132 time out, and 29 fail. The observation is therefore an absence of
malicious verdicts for those submitted raw files, not 75 successful benign
classifications per file. It also applies to constructed outputs, including
ones that fail the functional harness; it is not a result for all 306
planned variants.

For LLM transformation, 221 of 322 evaluable hashes receive a malicious
response ($q=68.6$\%), with mean 3.80 malicious responses per hash. The
additional submitted hash has an empty report. The 275 passing files
correspond to 263 hashes, of which 210 are detected (79.8\%, mean 4.41).
The 75 failing files correspond to sixty hashes, of which 59 have usable
reports and eleven are detected (18.6\%, mean 1.05). The lower scan rate
of failing outputs must not be interpreted as successful behavioral
preservation with reduced detection. It instead shows why functionality
and verdicts must be linked when interpreting the experiment.

All nineteen LLM data-handling hashes receive malicious responses, with
mean 20.63. That arm preserves supported data and references without
requesting one of the four instruction-transformation families. It answers
a different experimental question from LLM morphing. Across the whole
current scan cohort, 8,184 responses are format-unsupported, 298 time out,
and 74 fail; all remain visible in the response denominator.

\subsection{Relationship to Earlier Pilots and Scan Results}
The earlier 2026 cohort has 239 file entries and 220 distinct hashes,
all with nonempty completed reports. Twelve hashes receive at least one
malicious response. Table~\ref{tab:new_vt_cohort} retains its original group
membership and is separate from the current 549-hash manifest.
''',tables['tab:new_vt_cohort'],r'''
In that selected x64 cohort, none of the 197 distinct wrapping outputs
receives a malicious verdict. Thirteen contemporaneous original controls
all do, with mean 26.62/75 responses. Across the earlier cohort's 16,500
mutant-engine responses, 3,259 are format-unsupported, 283 time out, and
73 fail. The thirteen controls do not constitute a matched scan baseline
for every input and configuration in the new full-corpus campaign.

The earlier MessageBox transformation pilot retains 24 passing final
outputs, but its dialog check already participated in generation-time
selection and a failed run was restarted. Its 24/24 therefore measures
selected artifacts, not the single-invocation protocol of the benign
benchmark. No benign fixture from that benchmark was submitted for scanning.
The historical archive also has missing local artifacts for 6,972 of
15,021 mutant records, and its 102 original records represent ninety
distinct hashes. These facts limit retrospective verification and
independence without turning the published results into newly repeated
experiments.
''']
(root/'sections/extension_results.tex').write_text('\n\n'.join(pieces),encoding='utf-8')
discussion=r'''\section{Discussion of the Extensions}\label{sec:extension_limits}
The experiments answer different parts of the rewriting problem. Exact
classification on the six annotated fixtures shows that the two
identification methods handle those controlled layouts, including a
printable-code counterexample. The selected payload comparison shows why
classification and data handling must still be assessed separately:
different interval proposals often converge to the same output after
deterministic processing. More broadly representative annotations would
be needed to quantify identification accuracy beyond these examples.

The strongest functional results occur on the benign corpus, whose
observable behavior is specified precisely. Both wrapping and LLM
transformation then lose substantial coverage on the original payloads.
On x64 the principal measured obstacle is obtaining a constructed output;
on x86 some accepted outputs also fail execution checks. These outcomes
support retaining all three stages---interpretation, construction, and
execution---in the evaluation. A change that increases build availability
cannot be assumed to improve the other stages.

Wrapping produces a marked difference in static representation, and its
207 submitted hashes receive no malicious responses in this scan cohort.
The experiment does not isolate that representation as the cause of every
verdict: format support, failed analyses, and input selection also affect
the observations. Likewise, the apparent scan advantage of unsuccessful
LLM outputs disappears as evidence of useful transformation once their
failed functional checks are considered. These measurements concern raw
files and prescribed harness observables, not a deployed endpoint
protection system's response to a complete application.

The study is descriptive. The same inputs occur in multiple conditions;
some inputs and outputs share hashes; the benign architectures use
different frozen versions; and the full LLM campaign includes nonuniform
retry histories. These dependencies prevent treating every cell as an
independent sample or attributing small differences solely to prompting.
The source snapshots, per-cell outcomes, hashes, and separate cost totals
make those limitations inspectable. The completed results identify the
remaining reliability gap without presenting structural validation or a
successful limited observable as a proof of semantic equivalence.
'''
(root/'sections/extension_discussion.tex').write_text(discussion,encoding='utf-8')
print('Rewrote methodology, results, and discussion')
