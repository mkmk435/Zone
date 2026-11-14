from pathlib import Path
import json,re,hashlib

ROOT=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_update_20261113')
E=ROOT/'evidence'
S=json.loads((E/'SUMMARY.json').read_text())
M=json.loads((E/'SOURCES.json').read_text())
main=(ROOT/'main.tex').read_text(encoding='utf-8')
baseline=Path(r'C:\Users\ubu\Desktop\CCIS\backup_before_extension_20261113\main.tex').read_text(encoding='utf-8')

abstract=r'''\begin{abstract}
Zone is a binary-to-binary metamorphic engine for compact Windows x86
and x64 payloads. This extended article retains the original design,
Position-Independent Instruction method, and evaluation of 102 inputs
under fifteen configurations. It adds symbolic and heuristic code--data
identification, an alternative LLM classifier, LLM-assisted assembly
transformation, and an implementation of assembly wrapping for both
architectures. A new corpus of thirteen benign fixtures supplies
predeclared output-buffer checks; six further fixtures provide
independent code--data annotations. DeepSeek-assisted transformation
produced accepted outputs with correct buffers in 167/168 x64 and
138/144 x86 invocations under separately versioned experiments.
The classifier matched all eighteen LLM and six symbolic reference
tests on the six identification fixtures. A separate wrapping campaign
on the 102 original payloads built 243/306 variants, of which 170
passed the stated functional checks, exposing a substantial gap
between construction and observed functionality. Completed earlier
static scans and ongoing payload-level LLM experiments are reported
as separate cohorts. The assessment distinguishes classification,
construction, functionality, static verdicts, similarity, diversity,
and cost, without extrapolating raw-binary observations to deployed
endpoint protection.
\keywords{Binary Rewriting \and Metamorphic Code \and
Code--Data Identification \and Large Language Models \and Functional Preservation}
\end{abstract}'''
main=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:abstract,main,count=1,flags=re.S)
main=re.sub(r'\\draftnote\{The original study.*?findings before submission\.\}',lambda _:r'''\draftnote{Results are frozen at 21:20 CET on 13 November 2026.
The completed benign benchmark, earlier scan cohort, and current
payload campaign have separate denominators. The full-corpus LLM and
current scan campaigns are still in progress.}''',main,count=1,flags=re.S)
main=main.replace('technique, with the x86 implementation under development;', 'technique, with separately assessed x64 and x86 implementations;')
main=main.replace('Additional sections\naddress the limitations identified by that study through:', 'Additional sections\naddress the limitations identified by that study through:')
old=r'''\item additional evaluation of classification quality, build and
functional outcomes, static verdicts, similarity, diversity, and cost.'''
new=r'''\item additional evaluation on benign fixtures with predeclared
functional oracles and code--data annotations, complemented by
separately identified payload and static-scan campaigns. Classification,
construction, functionality, similarity, diversity, and cost remain
distinct measurements.'''
main=main.replace(old,new)

code_data=r'''\section{Code--Data Identification and Data-Preserving Rewriting}
\label{sec:code_data}
\subsection{Problem and Representations}
For an input byte sequence $B=(b_0,\ldots,b_{n-1})$, identification
returns candidate data intervals $[s_j,e_j)$ in payload-relative
coordinates, with optional kinds such as ASCII, UTF-16LE, or another
data object. Acceptance for rewriting additionally depends on reference
evidence and implementation support. The original inline-data and
immediate-operand examples in Tables~\ref{tab:broken-payload}
and~\ref{tab:functional-payload} motivate this added layer.

The implementation distinguishes a model's reported intervals, regions
accepted by deterministic checks, and regions actually extracted.
These sets need not coincide. An unsupported reference can prevent
processing of a correctly identified object, while filtering can make
different proposals yield identical final binaries. Evaluation retains
the output stage associated with each observation.

\subsection{Symbolic and Heuristic Identification}
The non-LLM path combines CFGFast candidate blocks and inferred data
with bounded symbolic exploration. Observed instruction starts are
expanded into their decoded byte spans, and newly observed entries
can seed a further graph-recovery pass. This prevents interior bytes
of an observed instruction from being treated as unvisited data solely
because only its start address was recorded.

The initial state leaves uninitialized registers and memory symbolic;
it does not reproduce a complete Windows process or all API behavior.
Time, state/block-step, pending-state, and solver limits bound the
analysis. Reports record termination reasons, unresolved states, and
errors. Missing observations therefore do not prove that a region is
data or unreachable.

Printable ASCII and UTF-16LE patterns supply additional candidate
evidence. Observed code spans prevent their acceptance under the
string heuristic. For strings overlapping candidate graph code,
additional structural corroboration is required. Graph-inferred
data and bytes outside recovered blocks retain different evidential
categories; the latter are uncertain rather than a complete data
partition. The available analysis limits and candidate categories
accompany the classification result.

\subsection{LLM Identification and Deterministic Handling}
The alternative path presents hex bytes, a heuristic linear disassembly,
and printable candidates to the model. It requests structured intervals
instead of rewritten code. The parser checks bounds, positive lengths,
and overlap. Reference scanning and data handling remain deterministic;
a proposal is applied to a fresh engine instance so that rejection
does not reuse partially modified state.

Accepted data contents and supported references are retained through
layout changes. The engine finalizes the supported references once
the code layout is known and checks integrity of the preserved data.
These checks do not establish that every reference in an arbitrary
input has been recovered. Architecture-specific operands require
separate x64 and x86 implementations even though the conceptual
contract is shared.

An invalid proposal can trigger feedback and another request in the
general pipeline. The reported classifier experiments specify their
actual call budgets separately from the transformation experiments.
The classifier's default worked-example condition is not labeled
zero-shot or two-shot merely because those conditions are compared
in assembly transformation.

Caching reuses identified regions for an input identity while references
are recomputed for the working representation. Timing must distinguish
new analysis from cached results. On curated fixtures, independent
annotations allow reference-based assessment; on the selected real
payloads, agreement and functional checks remain different forms of
evidence. The experiments in Section~\ref{sec:extended_results}
explicitly retain that distinction.
'''
(ROOT/'sections/extension_code_data.tex').write_text(code_data,encoding='utf-8')

llm=r'''\section{LLM-Assisted Assembly Transformation}\label{sec:llm}
\subsection{Task, Representation, and Model Role}
Zone delegates one of EQ, NOP insertion, BCF, or IBP to an LLM,
requesting a complete modified assembly representation. PII and
wrapping remain native transformations. The model generates an
instruction proposal; deterministic preparation, assembly, data
handling, and validation remain part of the evaluated pipeline.

The engine prepares symbolic labels for relevant code locations and
keeps the data representation outside the generated instruction text.
Original bytes, the prepared intermediate representation, and final
output identity are recorded separately. In particular, similarity to
the intermediate input does not measure every change from the original
file. The experiments request the model identifier
\texttt{deepseek-flash}. Version names assigned by a local alias or
pricing table are not independent confirmation of the provider's
model version.

\subsection{Zero-Shot, Two-Shot, and Call Budgets}
The initial zero-shot request supplies a textual specification without
worked examples; the two-shot request adds two input/output examples.
Example identities and prompt versions are part of the condition.
Repeated run numbers do not imply controlled or independent service
seeds. After rejection, the general pipeline can supply the previous
answer and validation feedback, so any later attempt is identified
as feedback-assisted.

The benign benchmark deliberately disables these internal retries:
each invocation allows one generation, and each input/family/shot
cell has three invocations in total, including failures. No failed
invocation is replaced. The ongoing payload campaign instead uses
one target output per cell and a driver supporting up to three
generation attempts. These are different experimental designs and
are not merged into one success percentage.

\subsection{Validation and Independent Functional Assessment}
Structural checks cover assembly, decoding coverage, tracked control
flow, data consistency, and family-specific requirements. A proposal
can be rejected because it is malformed, loses required structure,
or fails to apply the requested transformation. Structural acceptance
alone does not establish behavioral equivalence.

For the new benign benchmark, functional verification follows
generation in a separate harness and compares the complete output
buffer against its predeclared expected contents. It is not a
generation-time selection oracle. This differs from the earlier
MessageBox pilot, where the dialog verifier was included in output
acceptance. That earlier pilot is retained as a separate cohort.

Records preserve accepted and rejected invocations, transport failures,
hashes, timing, usage, and locally estimated cost. Reusing a completed
output is distinguished from a new model call. A correct buffer is
empirical evidence for the fixture's specified observable, not a
proof of all-state equivalence or correctness on unrelated payloads.
'''
(ROOT/'sections/extension_llm.tex').write_text(llm,encoding='utf-8')

wrap=r'''\section{Integration of Assembly Wrapping}\label{sec:wrapping}
\subsection{Existing Technique and Implementation Scope}
Assembly wrapping is an existing technique based on alternative
instruction interpretations~\cite{assembly_wrapping}. The contribution
here is its integration into Zone and empirical assessment. The
instruction view obtained by static decoding can differ from the
stream followed during execution; representation measurements must
state which view they use.

The implementation now supports both x64 and x86. The x86 path was
added after the first benchmark snapshot and is assessed against a
separately identified version. Register width, instruction encodings,
and addressing require architecture-specific treatment; an x64 outcome
is not transferred to x86 by assumption.

\subsection{Integration and Assessment Boundary}
Wrapping depends on an adequate instruction interpretation, data
preparation, and consistent handling of supported references. Some
regions may remain outside the main wrapped representation, and
construction may be refused on unsupported inputs. Availability,
construction success, empirical functionality, size, and diversity
are therefore distinct outcomes.

The benign x64 and x86 fixture results and the separate 102-payload
campaign appear in Section~\ref{sec:extended_results}. The latter
includes unbuilt and non-working outputs. Functional results on the
curated fixtures are not used as evidence of universal payload support.
The older selected x64 wrapping/static-scan cohort is also identified
separately, including its construction failures and duplicate outputs.
'''
(ROOT/'sections/extension_wrapping.tex').write_text(wrap,encoding='utf-8')

methods=r'''\section{Additional Experimental Methodology}\label{sec:methodology}
\subsection{Corpora, Frozen Versions, and Observables}
Three additional cohorts complement the original study. The benign
functional corpus contains seven x64 and six x86 fixtures covering
arithmetic, branches, loops, local calls, mixed control flow, strings,
and an x64 address-acquisition case. Expected writes are declared
before transformation in a 256-byte buffer; all remaining bytes must
retain their \texttt{0xCC} sentinel. A separate C runner executes the
code and returns the complete buffer. All thirteen originals pass
their checks before transformation.

Six further classifier fixtures have independent data-range annotations:
two multi-region cases (one per architecture), an x64 binary table,
two inputs without data, and an x64 case containing ASCII-like code
that must not be classified as data. The model receives neither these
annotations nor the other method's answer. These fixtures support
reference-based assessment; they do not represent the diversity of
arbitrary Windows payloads.

Snapshot B1 (13 November, 13:07 CET) is used for the benign native
matrix and x64 LLM transformation. Snapshot B2 (14:05 CET) is used
for x86 LLM transformation, x86 wrapping, and classifier assessment.
The payload campaign uses the separately named B3 copy, whose hashed
rewriting and LLM modules match B2. Snapshot identity, architecture,
corpus, and call policy remain associated with each result. B1/B2
architecture comparisons consequently do not isolate architecture
alone. The current full-payload matrix comprises 38 x64 and 64 x86
inputs with three wrapping runs each; all 102 originals pass the
stated current harness checks. Its network, port, dialog, or clean-exit
observables are weaker than the benign buffer oracle.

\subsection{Counting, Classification, and Functional Measures}
For $N$ planned cases, $B$ constructed outputs, and $W$ successful
functional checks, we report $B/N$, $W/N$, and $W/B$ separately.
Unbuilt cases remain in planned-case denominators. Repeated tests of
one failed output do not become independent variants. The benign LLM
matrix uses three single-generation invocations per cell; rejected
answers and transport failures remain in its denominator. The ongoing
payload driver has a separate retry policy, with completed cells and
generation attempts counted independently.

Identification uses exact equality of annotated and reported interval
sets, complemented by missed data bytes and code bytes classified
as data. Data-positive precision and recall are $|P\cap G|/|P|$
and $|P\cap G|/|G|$ for predicted and reference byte sets $P,G$.
Empty-data cases are assessed through exact empty-set decisions;
undefined precision/recall are not assigned favorable numerical values.
For real payloads without independent labels, the comparison is
agreement and downstream functionality. Reported LLM proposals,
symbolically extracted regions, and final binary hashes are different
output stages and are not treated as interchangeable annotations.

\subsection{Similarity, Static Verdicts, and Cost}
The additional LLM score is the normalized instruction-sequence
matching ratio from \texttt{SequenceMatcher}, $2M/(u+v)$ for $M$
matched elements and sequence lengths $u,v$~\cite{python_difflib}.
NOP-like operations are filtered in that condition, so a value of one
does not imply byte identity. Table~\ref{tab:new_llm_benign} averages
this score over accepted outputs only. Exact diversity counts unique
hashes, both within conditions and across the cohort. Neither score
establishes semantic equivalence. The historical cosine and entropy
measurements remain in Section~\ref{sect:var_metrics}.

For completed static scans, $d_i=m_i/a_i$ is the per-file fraction of
malicious verdicts, and $q$ is the fraction of files with any malicious
verdict. The completed earlier 2026 cohort below uses all 75 reported
engine responses in $a_i$; unsupported formats, timeouts, and failures
are separately disclosed. These are not benign verdicts. A pending
scan has neither a measured $d_i$ nor a zero detection result.
Scan deduplication is per hash, while a shared hash retains membership
in every experimental group to which it belongs. Group counts are
therefore not summed to obtain the union.

Time and cost are taken from the saved records. Costs are local tariff
estimates rather than invoices; failed invocations are included.
The classifier payload-arm medians include different preparation and
analysis work and are not a controlled claim of general speedup.
Evidence tables, source hashes, and experiment settings are frozen
at 21:20 CET on 13 November 2026. Later writes to active campaign
logs are outside this manuscript snapshot.

\subsection{Validity of the Extensions}\label{sec:extension_limits}
Bounded exploration, missing environment behavior, reference support,
and shared deterministic filtering limit attribution to the classifier
alone. Buffer equality exercises a specified observable, while a
successful connection or dialog supplies narrower evidence. Different
snapshots, input selection, model aliases, and scan dates limit causal
comparisons. The benign corpus is deliberately small and structured;
its outcomes are not extrapolated to the unfinished payload LLM
matrix or to deployed endpoint products.
'''
(ROOT/'sections/extension_methodology.tex').write_text(methods,encoding='utf-8')

def f(v,n=3):return f'{v:.{n}f}'
native_rows=[]
for r in S['native']:
    native_rows.append(f"{r['arch']} & {r['technique'].upper()} & B{r['block']} & {r['n']} & {r['built']} & {r['working']} & {r['unique']} \\\\")
llm_rows=[]
for r in S['llm']:
    llm_rows.append(f"{r['arch']} & {r['technique'].upper()} & {r['shots']} & {r['working']}/{r['n']} & {f(r['similarity'])} & {r['unique']}/{r['built']} & {f(r['mean_seconds'],1)} & {f(r['cost_usd'])} \\\\")
cls_by={(r['arch'],r['case'],r['method']):r for r in S['classifier']}
cls_rows=[]
for a,c in sorted({(r['arch'],r['case']) for r in S['classifier']}):
    l=cls_by[a,c,'llm'];z=cls_by[a,c,'symbolic']
    cls_rows.append(f"{a} & {c} & {l['data_bytes']} & {l['exact']}/{l['n']} & {z['exact']}/{z['n']} & {f(l['mean_seconds'],1)} & {f(z['mean_seconds'],1)} \\\\")
wrap_rows=[]
for r in S['wrap_full']:
    wrap_rows.append(f"{r['arch']} & {r['inputs']} & {r['built']}/{r['n']} & {r['working']}/{r['n']} & {r['working']}/{r['built']} & {r['unique']} \\\\")
vt_names={'wrap':'Wrapping (prior x64)','wrap_full':'Wrapping combined (prior x64)','lldata':'LLM data only','lldata_eq':'LLM data + EQ'}
vt_rows=[]
for r in S['vt_previous']:
    t=r['technique'];name=vt_names.get(t,t.replace('llm_','LLM ').replace('_s0',' / 0').replace('_s2',' / 2').upper())
    vt_rows.append(f"{name} & {r['unique']} & {r['detected']}/{r['completed']} & {f(100*r['mean_fraction_all_reported'],2)} & {f(r['mean_malicious'],2)} \\\\")

results=r'''\section{Additional Experimental Results}\label{sec:extended_results}
The detailed conference results in Sections~\ref{sec:results}--\ref{sec:comparison}
remain the historical foundation. This section adds completed benign
experiments, the current full-corpus wrapping and identification
campaigns, and a separately identified earlier 2026 scan cohort.
The payload-level LLM matrix and its new scan campaign remain partial
at the stated cutoff.

\subsection{Benign Functional Benchmark}
Table~\ref{tab:new_native} reports the native matrix. All x64 methods
pass 21/21 fixture runs. On x86, EQ, NOP, and BCF pass 18/18;
B1 IBP builds 17/18 outputs but none pass the buffer check, with
an observed construction exception in the remaining case. The B2
x86 wrapping port passes 18/18. These counts characterize the
specified fixture oracle and versions, rather than universal support.

\begin{table}[t]
\caption{New native fixture results. $N$: attempts; $B$: builds;
$W$: correct complete buffers; $U$: distinct built-output hashes.
B1/B2 identify different frozen engine versions.}
\label{tab:new_native}
\centering\small
\begin{tabular}{@{}lllrrrr@{}}
\toprule
Arch. & Family & Version & $N$ & $B$ & $W$ & $U$ \\
\midrule
'''+'\n'.join(native_rows)+r'''
\bottomrule
\end{tabular}
\end{table}

\subsection{DeepSeek Transformation on the Benign Corpus}
The model is invoked on all seven x64 and six x86 fixtures, four
families, two shot conditions, and three invocations per cell. The
result is 168 x64 invocations under B1 and 144 x86 invocations under
B2. Respectively 167 and 138 yield accepted outputs, all of which
pass the independent buffer check. Five invocations are rejected by
the family-specific validator and two encounter transport errors.
No failed invocation is replaced. The x86 IBP figures include both
types of failure; they are not all semantic execution failures.

\begin{table}[t]
\caption{Benign DeepSeek transformation. $W/N$ includes rejected and
failed invocations. $S$ is mean sequence similarity over accepted outputs;
$U/B$ is unique hashes per built output within the condition. Time is
mean invocation seconds; cost is the sum of local USD estimates.}
\label{tab:new_llm_benign}
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lllrrrrr@{}}
\toprule
Arch. & Family & Shots & $W/N$ & $S$ & $U/B$ & Time & Cost \\
\midrule
'''+'\n'.join(llm_rows)+r'''
\bottomrule
\end{tabular}
\end{table}

The x64 outputs contain 108 distinct hashes and cost an estimated
\$0.5205; x86 contains 99 distinct hashes and costs \$0.5132.
These union counts differ from sums of per-condition uniqueness
because outputs can recur across conditions. EQ in particular has
repeated outputs. The NOP similarity of one follows the stated
filtering rule and is consistent with byte differences.

On x86 IBP, the observed result changes from 13/18 in the zero-shot
condition to 17/18 with two examples; x64 IBP instead records 21/21
and 20/21. The small number of input fixtures and differing versions
do not support a general claim that two-shot prompting is superior.
The controlled benchmark supports bounded functional observations
and exposes construction, diversity, and cost differences.

\subsection{Reference-Based Code--Data Identification}
On the six classifier fixtures, all eighteen LLM invocations and all
six symbolic runs exactly match the independent interval annotations
(Table~\ref{tab:new_classifier}). Both methods record zero missed
data bytes and zero code bytes classified as data. The three
data-positive fixtures have exact precision/recall on these cases;
the three empty-data cases are evaluated as correct empty sets.
All resulting executions pass their buffer checks. These are six
curated inputs, not twenty-four independent program samples.

\begin{table}[t]
\caption{Independent classifier fixtures. $D$ is annotated data bytes.
Exact interval sets are compared against predeclared references.
Mean times are per run in seconds.}
\label{tab:new_classifier}
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}llrrrrr@{}}
\toprule
Arch. & Case & $D$ & LLM exact & Symbolic exact & LLM time & Sym. time \\
\midrule
'''+'\n'.join(cls_rows)+r'''
\bottomrule
\end{tabular}
\end{table}

An earlier three-case benign data-handling check also records 9/9
exact LLM results. It remains separate from the six-fixture comparison.
For the six-fixture cohort the total model cost is approximately
\$0.0059, excluding the earlier cohort and pilot calls.

\subsection{Wrapping on the Original 102 Payloads}
The separate B3 campaign attempts three prepared wrapping variants
for every original input: 114 x64 and 192 x86 attempts. All 102
unmodified inputs pass the current class-specific harness checks.
Table~\ref{tab:new_wrap_full} includes every planned wrapping case.
Overall, 243/306 outputs are constructed and 170/306 pass the harness.
Among constructed outputs, 170/243 pass. The aggregate is descriptive;
the architecture-specific counts retain the relevant failure stages.

\begin{table}[t]
\caption{Full original-corpus wrapping campaign, B3. The harness
observables are distinct from the benign exact-buffer oracle.
$U$ counts distinct constructed hashes.}
\label{tab:new_wrap_full}
\centering\small
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Arch. & Inputs & $B/N$ & $W/N$ & $W/B$ & $U$ \\
\midrule
'''+'\n'.join(wrap_rows)+r'''
\bottomrule
\end{tabular}
\end{table}

All 63 constructed x64 outputs pass, while 51 attempts do not build.
On x86, 180 outputs build and 107 pass; the 73 initial failures also
fail in the saved retest records. Retests are not additional variants.
This contrasts with the complete success of wrapping on the much
smaller benign fixture corpus and demonstrates why build rate and
conditional working rate are reported separately. The earlier selected
x64 cohort, with 200/260 builds and 198/200 passing outputs, is not
substituted for this full-corpus campaign.

\subsection{Identification on Nineteen Selected Payloads}
The payload identification comparison selects thirteen x64 and six
x86 inputs for which the symbolic preparation reports extracted data.
Both arms build 19/19 outputs and pass 17/19 harness checks. Symbolic
extracted ranges and reported LLM proposals agree exactly in 9/19
cases, whereas the final binary hashes agree in 16/19. The stages
being compared are different; neither count is reference accuracy
on these unlabeled payloads. Their divergence also shows why final
byte identity cannot be used to infer identical classification.

The recorded median wall times are 123.95 seconds for symbolic
preparation and 59.88 seconds for the LLM arm; the latter costs an
estimated \$0.2218 across the nineteen recorded runs. Different
preparation, caching, and analysis budgets limit performance comparison.
The common failures and agreement concern this selected set and the
current harness, not the whole identification population.

\subsection{Completed Earlier Static-Scan Cohort}
The earlier 2026 manifest contains 239 file entries and 220 distinct
hashes, with completed results for all 220. Twelve distinct hashes
receive at least one malicious verdict. Table~\ref{tab:new_vt_cohort}
joins results to each group's hash membership, retaining shared hashes
in every applicable row. Therefore the row counts need not sum to 220.
This avoids assigning a shared output solely to the first group in
which it appeared.

\begin{table}[t]
\caption{Completed earlier 2026 raw-file cohort. $q$ is detected hashes
over completed hashes; $\overline d$ is the percentage of all reported
engine responses that are malicious, averaged per file. $\overline m$
is mean malicious-engine count. These are separate measures.}
\label{tab:new_vt_cohort}
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
Group & Hashes & $q$ & $\overline d$ (\%) & $\overline m$ \\
\midrule
'''+'\n'.join(vt_rows)+r'''
\bottomrule
\end{tabular}
\end{table}

The 197 unique wrapping outputs in this selected x64 cohort receive
no malicious verdicts. Thirteen contemporaneous original controls
all receive malicious verdicts, with mean 26.62/75 engines. This
describes constructed raw files from that cohort, not the availability
or functionality of all wrapping attempts. Across its 16,500 reported
mutant-engine responses, 3,259 are format-unsupported, 283 time out,
and 73 fail. Zero malicious verdicts must be interpreted with those
unresolved responses and the raw-file scope visible.

The earlier MessageBox LLM pilot has 24 final passing outputs but
includes generation-time dialog selection and a restarted failed run;
its recorded accepted artifacts do not provide the same denominator
as the single-attempt benign benchmark. The differing scan outcomes
across its small groups likewise do not establish a general prompting
ranking. No benign fixture is submitted to the scan service in the
new functional benchmark.

An audit of the historical archive finds that 6,972 of the 15,021
mutant records no longer have a locally available artifact for hash
verification; the 102 original records correspond to 90 distinct
hashes. The conference results remain published observations, while
these losses and duplicates limit retrospective verification and
independence. They are not treated as newly repeated experiments.

\subsection{Ongoing DeepSeek Campaign: Snapshot Only}
At 21:20 CET, the new payload transformation ledger contains
30 completed cells of a planned 816 (102 inputs, four families,
two shot conditions): eleven accepted builds and nineteen failed
cells. Its records account for 35 API calls where available and
an estimated \$0.7538. Transport failures can leave incomplete
usage information. Observed rejection categories include truncated
responses and structural validation failures. This is progress
accounting, not a final construction or functional rate for the
planned matrix; a recorded build is not a passed execution test.

The associated current scan ledger records 208 uploaded hashes and
no completed verdict records at the cutoff. These submissions are
kept separate from Table~\ref{tab:new_vt_cohort}. Pending current
scans supply no measured detection rate. The frozen evidence and
source hashes accompany this manuscript so that later campaign
writes do not silently change the reported snapshot.
'''
(ROOT/'sections/extension_results.tex').write_text(results,encoding='utf-8')

start=main.index(r'\section{Conclusions}\label{sec:conclusion3}')
end=main.index(r'\begin{credits}',start)
conclusions=r'''\section{Conclusions}\label{sec:conclusion3}
The original Zone design and its 102-payload evaluation remain the
foundation of this extended study. Their detection, working-rate,
size, entropy, and similarity observations show why representation
change and empirical functionality require separate measurements.
The PII design and historical SGN comparison are retained within
their original experimental boundaries.

The extensions add explicit code--data identification, LLM-assisted
transformation, and wrapping for both architectures. Independent
annotations on six curated fixtures give exact identification in
18/18 LLM and 6/6 symbolic runs. The benign transformation experiments
produce accepted outputs with correct buffers in 167/168 x64 and
138/144 x86 invocations, under different frozen versions. These
results are bounded by the fixture oracle and do not establish
universal semantic preservation.

The broader wrapping campaign builds 243/306 variants and passes
170/306 harness checks, despite complete wrapping success on the
small benign corpus. On nineteen selected real payloads, final-output
identity and reported range agreement also differ. Together these
observations expose the limits of extrapolation from curated tests
and the need to separate classification, construction, and execution.
Completed raw-file scans characterize a separate earlier cohort;
the ongoing full-payload DeepSeek and current scan campaigns remain
incomplete at the declared cutoff. Their final outcomes must be
assessed with their own versions, budgets, and denominators.

'''
main=main[:start]+conclusions+main[end:]
(ROOT/'main.tex').write_text(main,encoding='utf-8')

editors='''The extended manuscript retains the original Zone architecture, Position-Independent Instruction design, experimental protocol, all seven figures, six tables, four code listings, and the algorithm from the CCIS preparation of the SECRYPT 2026 study. The detailed detection, working-rate, size, entropy, similarity, limitations, and Shikata Ga Nai comparison remain available as the published foundation and carry source citations. The conference paper is cited and included in the references. The title, abstract, introductory contributions, and conclusions have been revised to describe the original study together with the extension; retrospective archive limitations are reported separately from the original findings.

The added sections introduce symbolic/heuristic and LLM code--data identification, shared deterministic data handling, zero-shot and two-shot LLM assembly transformation, and x64/x86 assembly wrapping as an implementation of an existing technique. New experiments include thirteen benign fixtures with predeclared complete-buffer oracles, six independently annotated identification fixtures, separately versioned x64/x86 LLM and native matrices, a three-run wrapping campaign on all 102 original payloads, and an identification comparison on nineteen selected payloads. Completed earlier 2026 scans are joined by per-group hash membership and reported separately from an ongoing full-payload DeepSeek campaign. The manuscript distinguishes correctness, build availability, static verdicts, similarity, diversity, and cost, and freezes evidence at 21:20 CET on 13 November 2026. Final results of the ongoing campaigns remain explicitly outside that snapshot.
'''
(ROOT/'EDITOR_DIFFERENCES.txt').write_text(editors,encoding='utf-8')
notes='''# Aggiornamento sperimentale - 13 novembre 2026, ore 21:20 CET

La revisione mantiene la struttura additiva e tutti i risultati della conferenza. I dati nuovi sono estratti dai file grezzi congelati in `evidence/sources/`, con hash in `evidence/SOURCES.json` e tabelle derivate CSV. Non sono state eseguite nuove chiamate LLM, scansioni o esecuzioni di payload per questa revisione.

## Che cosa e cambiato

- Il wrapping x86 e ora implementato e valutato: 18/18 run delle fixture benigne superano il buffer oracle; la campagna sui payload originali ha risultati separati, piu limitati.
- Benchmark benigno: 13 fixture, baseline 13/13; matrici native per versione; LLM x64 167/168 e x86 138/144. Ogni invocazione ammette una generazione, con tre invocazioni per cella e nessuna sostituzione dei fallimenti. Le tabelle includono similarita SequenceMatcher, unicita, tempo e costo.
- Classifier: sei fixture indipendenti, 18/18 chiamate LLM e 6/6 analisi simboliche esatte. Tre casi sono data-positive, tre senza dati. Questa evidenza non si estende automaticamente ai payload reali.
- Wrapping sul corpus originale: 306 tentativi; 243 build; 170 test funzionali superati. I 73 retest falliti non sono nuove varianti.
- Classificazione su 19 payload selezionati: entrambe le pipeline 17/19 test; 9/19 accordi degli intervalli confrontati, 16/19 identita finali. Non e una misura di accuratezza senza ground truth.
- VT precedente: 220 hash completati; la nuova tabella corregge il conteggio per appartenenza ai gruppi, conservando gli hash condivisi in ciascun gruppo. Le somme delle righe non sono il totale dell'unione.
- DeepSeek sul corpus originale e attivo separatamente: fotografia 30 celle completate su 816 pianificate, 11 build accettati e 19 fallimenti. Nessuna percentuale finale viene ricavata da questo parziale. Le 208 sottomissioni VT correnti non avevano verdetti completati alla fotografia.

## Dove continuare

`main.tex` conserva lo studio originale e include i moduli `sections/extension_*.tex`. Aggiornare `extension_results.tex` solo usando una nuova fotografia coerente e distinguendo versioni e campagne. Aggiornare contestualmente abstract, conclusioni, nota editor e SOURCES.json. I vecchi risultati non vanno sostituiti dai nuovi.

Il modello e identificato dal nome richiesto `deepseek-flash`; model_version nei client e una mappatura locale, non una conferma del provider. I costi sono stime tariffarie locali. I record di errori di rete possono non avere usage completo. Non sommare come repliche indipendenti le varianti uguali, i retest e le riprese di una cella.

Per compilare eseguire `build.ps1`. Le note blu di lavoro si nascondono con `\\workingdraftfalse` solo dopo la loro risoluzione. Restano da completare corresponding author, disclosure degli interessi e controlli storici descritti in BASELINE_CHECKS.md. L'invito richiede almeno 30% di nuovo materiale sostanziale: i conteggi testuali non ne sono una certificazione.
'''
(ROOT/'README_REVISIONE.md').write_text(notes,encoding='utf-8')

audit={'revision':'additive manuscript updated against frozen evening evidence','cutoff_berlin':M['cutoff_berlin'],
 'evidence':'evidence/SOURCES.json; evidence/SUMMARY.json; per-condition CSV tables',
 'retained_objects':{},'new_calls_or_payload_tests_performed_for_paper_update':False}
for env in ['figure','table','lstlisting','algorithm']:
    pat=r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}'
    old=re.findall(pat,baseline,re.S);now=re.findall(pat,main,re.S)
    assert all(x in now for x in old)
    audit['retained_objects'][env]={'count':len(old),'unchanged':True}
(ROOT/'REVISION_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('Updated manuscript; all original scientific objects retained.')
