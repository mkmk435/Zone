from pathlib import Path
import re, shutil, json

ROOT = Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
BACKUP = ROOT / 'before_30page_revision_20261115'
if not BACKUP.exists():
    BACKUP.mkdir()
    for name in ['main.tex', 'main.pdf', 'bibliography.bib', 'README_REVISIONE.md']:
        shutil.copy2(ROOT/name, BACKUP/name)
    shutil.copytree(ROOT/'sections', BACKUP/'sections')
EVIDENCE = ROOT/'evidence/compact_20261115'
EVIDENCE.mkdir(exist_ok=True)

def read(name):
    return (BACKUP/name).read_text(encoding='utf-8')

def save(name, text):
    (ROOT/name).write_text(text, encoding='utf-8')

def span(text, start, end, new):
    a=text.index(start)
    b=text.index(end,a+len(start))
    return text[:a]+new.strip()+'\n\n'+text[b:]

def para(text, start, new):
    a=text.index(start)
    b=text.find('\n\n',a)
    if b<0: b=len(text)
    return text[:a]+new.strip()+text[b:]

def object_block(text, env, label):
    matches=re.finditer(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}',text,re.S)
    return next(m.group(0) for m in matches if label in m.group(0))

main=read('main.tex')
main=span(main, r'\section{Introduction}', r'\section{Background}', r'''
\section{Introduction}\label{sec:introduction}
Metamorphic rewriting changes a program's instruction sequence, whereas
polymorphic encoding typically changes an encrypted body and its decoding
routine. Both complicate byte-pattern recognition, but expose different
representations during execution~\cite{PEsurveybible,metamorphic1,metamorphic2}.
Zone is a modular \emph{bin2bin} engine for studying these effects on
Windows x86 and x64 payloads without source code or debugging symbols.

\paragraph{Motivation and Contributions of the Extension.}
The conference study~\cite{zone_secrypt_2026} evaluated 102 payloads under
15 transformation configurations and observed substantial functional loss.
Embedded data is one source of failure: a disassembler can interpret a
string as instructions, which rewriting then modifies. Preserving the
bytes alone is also insufficient when changes invalidate their references.
This extension addresses data preparation and evaluates additional ways
to transform the prepared code. Its contributions are:
\begin{itemize}
\item Alternative symbolic/heuristic and LLM data classifiers, followed by
shared deterministic handling of supported data and references.
\item An LLM transformation path for EQ, NOP, BCF, and IBP, comparing
requests without examples and with two worked examples.
\item Integration and assessment of the existing assembly-wrapping
technique on both x64 and x86.
\item Completed experiments on annotated and controlled programs and the
original corpus, including recovery tests on previously problematic
inputs, functional outcomes, static detection, diversity, and cost.
\end{itemize}

The original architecture, PII design, experiments, and comparison with
Shikata Ga Nai provide the baseline. Reused figures, tables, listings, and
the algorithm carry source citations; added methods and measurements are
identified separately. The selected x64 recovery cohort improves from
1.2\% to 80.2\% working rate, motivating a joint assessment of construction
and execution rather than detection alone.

The scope remains compact, position-independent payloads. Full Portable
Executable (PE) rewriting requires additional treatment of imports,
sections, relocations, alignment, and entry points, and signatures may
also occur outside code~\cite{sigdetPEnoncode}. Raw-file scan results and
payload-level execution tests therefore describe the tested representations,
not complete malicious applications or deployed endpoint protection.

Sections~\ref{sec:background}--\ref{sec:comparison} summarize the baseline
methods, results, and limitations. Sections~\ref{sec:code_data}--\ref{sec:wrapping}
present the added methods; Sections~\ref{sec:methodology} and~\ref{sec:extended_results}
describe their evaluation. Discussion, related work, and conclusions follow
in Sections~\ref{sec:extension_limits}--\ref{sec:conclusion3}.
''')
main=span(main, r'\subsection{Metamorphic Engines}', r'\subsection{Morphing Techniques}', r'''
\subsection{Metamorphic Engines}\label{sub:meth}
A metamorphic engine rewrites an instruction-level representation with
functional preservation as its objective. Substitution, insertion, and
reordering produce different byte sequences but require preservation of
control flow, references, and relevant processor state~\cite{historycodeobf,identifyingmeth,metworm}.
Unlike polymorphic encoding, metamorphism does not require a
decrypt-and-execute stage. Shikata Ga Nai varies its decoding stub, whose
recurring features can themselves be recognized~\cite{sgnstrong}; after
decoding, its original body may be available to memory analysis~\cite{codeExtraction}.
A rewritten body instead executes in its transformed representation,
without this distinction alone guaranteeing runtime evasion.
''')
main=span(main, r'\paragraph{Instruction Block Permutation.}', r'\paragraph{Bogus Control Flow.}', r'''
\paragraph{Instruction Block Permutation.}
IBP partitions the instruction sequence, links each block to its logical
successor, permutes physical placement while retaining the entry block,
and updates control-flow references. Block granularity determines layout
variation and rewriting overhead. Because instructions within a block can
remain unchanged, short internal signatures may survive even when longer
contiguous sequences change.
''')
main=span(main, '\n\\begin{enumerate}\n\\item \\textbf{Inserted regions.}', r'\section{Zone Architecture}', '')
# Preserve the short numbered IBP explanation for readability.
original_main=read('main.tex')
ibp_start=original_main.index(r'\paragraph{Instruction Block Permutation.}')
ibp_end=original_main.index(r'\paragraph{Bogus Control Flow.}',ibp_start)
main=span(main,r'\paragraph{Instruction Block Permutation.}',r'\paragraph{Bogus Control Flow.}',original_main[ibp_start:ibp_end])
main=span(main, 'Two scope restrictions are relevant', r'\paragraph{Testing Method.}', r'''The x64 and x86 collections differ in membership as well as size, so
architecture comparisons also reflect their input composition. Large,
DLL-based components fall outside the payload-level scope.''')
# The list was part of the paragraph replaced above; remove its retained body.
main=re.sub(r'\n\\begin\{itemize\}\n\s*\\item \\textbf\{Architecture coverage\.\}.*?\\end\{itemize\}', '', main, flags=re.S)
old_working=object_block(main,'figure',r'\label{fig:working_rate}')
(EVIDENCE/'historical_working_plot_before_consolidation.tex').write_text(old_working+'\n',encoding='utf-8')
main=main.replace(old_working,'')
main=para(main, r'The \emph{working rate}', r'''The \emph{working rate} is the proportion passing the execution checks:
an expected connection for reverse shells, port opening for bind shells,
or exception-free termination for other generic cases.
Table~\ref{tab:overall_working_update} consolidates historical rates
recomputed from retained test records with the update for 49 retested
inputs. This replaces the earlier working-rate plot and aligns
configuration labels with those records. The historical study reported
greater stability for EQ and lower stability for PII, particularly on x86.''')
main=span(main, r'\draftnote{The detailed historical', 'This section restates', r'''
\draftnote{Historical detection-plot associations and similarity provenance
still require reconciliation with the conference records
(\texttt{BASELINE\_CHECKS.md}). Working rates are consolidated in
Table~\ref{tab:overall_working_update} using the retained test records.}
''')
main=span(main, r'\paragraph{Evaluation Limitations.}', r'\section{Size and Statistical Measurements}', r'''
\paragraph{Evaluation Limitations.}
Raw \texttt{.bin} submissions may receive a different analysis path from
complete executables, including unsupported-format responses and omitted
execution-based analysis. Comparing originals and variants under the
same format assumptions provides a corpus-specific comparison, not an
evaluation of complete antivirus or EDR products during deployment~\cite{zone_secrypt_2026}.
''')
main=span(main, 'The conference paper also characterized', r'\paragraph{Payload Length Variation.}', r'''
The conference paper measured file length, entropy change, and cosine
similarity to characterize the rewritten representations~\cite{zone_secrypt_2026}.
''')
main=span(main, 'In the assembly results,', '\\begin{figure}', r'''
NOP insertion increased assembly entropy, whereas PII decreased it,
consistent with repeated bookkeeping instructions. BCF combined small
entropy changes with increased length and a changed opcode distribution;
IBP could change layout while retaining similar instruction frequencies.
Entropy describes the representation, not functional preservation.
''')
main=para(main, 'Here $A_i$', r'''Here $A_i$ and $B_i$ are opcode frequencies and $n$ is their joint
vocabulary size. This representation-level comparison~\cite{llmobf}
does not establish equivalent behavior.''')
main=para(main, 'Instruction-frequency agreement', r'''The execution checks in Section~\ref{sec:results} assess functionality
separately: even a small error can alter behavior without substantially
changing instruction frequencies.''')
main=span(main, 'Accurate recovery of instructions', r'\begin{table}', r'''
Recovering instructions and references is a general challenge in static
analysis~\cite{staticdisasmTuringComplete}. The two published examples
below show one concrete distinction: an inline string versus a string
encoded within an instruction operand.
''')
main=para(main, 'In Table~\\ref{tab:broken-payload}', r'''In Table~\ref{tab:broken-payload}, part of the trailing
\texttt{calc.exe} string decodes as a branch and can be modified by rewriting.''')
main=para(main, 'Table~\\ref{tab:functional-payload} shows', r'''In Table~\ref{tab:functional-payload}, the string is an immediate
operand at \texttt{0x8e}; the reported transformation avoids that inline-data
failure. Section~\ref{sec:code_data} develops the corresponding preparation stage.''')
main=span(main, r'\section{Comparison with Shikata Ga Nai}', '% Added material', r'''
\section{Comparison with Shikata Ga Nai}\label{sec:comparison}
The conference study~\cite{zone_secrypt_2026} compared Zone with the
Shikata Ga Nai (SGN) polymorphic encoder~\cite{sgnarticle}, using the
original x86 encoder and an unofficial x64 implementation~\cite{sgn64}.
Reported mean static detection rates were 0\% for SGN versus 0.57\% for
Zone on x64, and 10.22\% versus 0.25\% on x86; PII reached 0\% on both.

SGN varies an encoded body and its decoding stub, whose recurring
features may be recognized~\cite{sgnstrong}. The conference study also
scanned memory dumps from SGN execution and reported verdicts matching
the unencoded inputs, consistent with exposure of the original body after
decoding~\cite{codeExtraction}. Zone instead intends to retain the
rewritten representation during execution. The dump comparison measures
recognizability of submitted memory contents, not runtime detection by
a deployed endpoint product.
''')
save('main.tex',main)

s=read('sections/extension_code_data.tex')
fig=object_block(s,'figure',r'\label{fig:extended_pipeline}')
s=r'''
\section{Code--Data Identification and Data-Preserving Rewriting}
\label{sec:code_data}
\subsection{Why Data Identification Comes Before Transformation}
A raw binary contains no explicit distinction between instructions and
embedded strings or tables. String bytes may decode as plausible
instructions, so rewriting their apparent instruction sequence can corrupt
data. Table~\ref{tab:broken-payload} illustrates this failure; in
Table~\ref{tab:functional-payload}, the string instead occupies an
instruction operand that must remain intact.

Preparation separates two responsibilities. \emph{Identification} proposes
data regions; \emph{data handling} preserves supported objects and updates
their references after layout changes. A reference is an instruction
operand or address calculation pointing to code or data. Preserving a
string is insufficient if the program still reads its old address.
Figure~\ref{fig:extended_pipeline} shows the alternative symbolic/heuristic
and LLM classifiers feeding shared handling. Independently, instructions
can be transformed natively or by an LLM: classification does not imply
LLM transformation.
'''+fig+r'''

\subsection{What a Classification Result Means}
A proposed region is an interval $[s,e)$ of input byte offsets: it includes
$s$ but excludes $e$, so $[2,8)$ denotes six bytes. An optional type names
an encoding such as ASCII or UTF-16LE. The answer is a set of candidate
intervals, not a replacement binary.

Proposed, accepted, and extracted regions are distinct. A correct proposal
may be unsupported if its references cannot be updated; different proposals
may yield the same binary when shared checks retain the same objects.
The experiments therefore compare annotations, accepted regions, and final
hashes at their respective stages.

\subsection{Symbolic Exploration Combined with Static Heuristics}
The non-LLM method combines three sources. First, angr's CFGFast recovers
a control-flow graph whose nodes are instruction blocks and edges are
possible transfers~\cite{angr_cfg_docs}. Second, bounded symbolic execution
explores paths with unknown register and memory values represented as
expressions. Third, pattern-based rules recognize printable ASCII and
UTF-16LE strings, including terminators, and consider regions identified
as data by control-flow analysis. Candidates overlapping observed code
are excluded by the string heuristic; overlaps with graph-recovered code
require additional structural support.

An observed instruction protects its entire decoded byte span, including
interior bytes of variable-length instructions. Newly observed entry
points can support another graph-recovery pass. Exploration has time,
solver, and state limits, and its initial state does not reproduce all
Windows API behavior. Unvisited regions consequently remain unknown,
rather than being classified as data solely because exploration missed
them. Reports preserve stopping reasons, unresolved states, and errors.

\subsection{LLM Identification and Shared Data Handling}
The LLM receives hexadecimal bytes, a linear disassembly, and candidate
printable strings, and returns structured data intervals. The disassembly
is evidence to assess, not a trusted annotation. This mode neither
extracts data nor rewrites instructions.

Deterministic parsing rejects empty or out-of-bounds intervals and invalid
overlaps. The engine examines supported references and retains accepted
data separately from the instructions. After transformation, it finalizes
references using the new layout. Integrity checks compare retained bytes
with their saved originals at the final locations and verify supported
references against their expected destinations; mismatches reject the
construction. Address handling is architecture-specific.

For example, a benign routine may copy embedded strings \texttt{alpha}
and \texttt{beta} into a buffer. Identification locates the strings;
handling preserves their contents and links; the final execution test
checks the expected buffer. These test different stages of the pipeline.

Correction requests append the rejected answer and validator diagnostic
to the conversation and ask for a revised proposal, within the configured
attempt limit. An interval beyond the input, for example, receives an
out-of-bounds diagnostic. Classification feedback concerns data locations;
transformation feedback concerns assembly. Likewise, examples illustrating
classification are independent of the transformation zero-shot/two-shot
conditions in the next section.

Caching reuses identified regions associated with an input identity.
References are computed again for the working representation because
rewriting can move code and data. Reusing identification therefore does
not reuse obsolete addresses. Both classifiers feed the same handling,
which can reconcile different proposals into identical final binaries.
'''
# Keep the fuller definitions and bounded-analysis explanation where the
# author had specifically requested clarity. Other new prose is condensed.
original_data=read('sections/extension_code_data.tex')
for start,end in [
    (r'\subsection{What a Classification Result Means}',r'\subsection{Symbolic Exploration'),
    (r'\subsection{Symbolic Exploration',r'\subsection{LLM Identification'),
]:
    a=original_data.index(start)
    b=original_data.index(end,a+len(start))
    s=span(s,start,end,original_data[a:b])
save('sections/extension_code_data.tex',s.strip()+'\n')

s=read('sections/extension_llm.tex')
s=span(s, 'In transformation mode,', 'Before sending a request,', r'''
In this mode the LLM receives assembly and proposes a new instruction
sequence intended to preserve behavior. It supports the EQ, NOP, BCF,
and IBP families introduced in Section~\ref{sec:background}; data
classification instead returns only locations. PII and wrapping remain
native operations because their layout and encoding constraints are not
implemented in the LLM interface's requests and validators. This is an
implementation boundary, not an intrinsic limitation of language models.
''')
s=span(s, 'Before sending a request,', 'The experiments request', r'''
Zone prepares an assembly listing with identified data retained separately.
The model proposes instruction changes while deterministic handling
preserves exact data contents; identification itself may use an LLM.
Relevant locations receive symbolic labels, which name destinations
independently of their changing numerical offsets. An end-to-end model
that also regenerates data would be a different, unevaluated design.

The model returns a complete listing. Zone assembles it, restores retained
data, and checks the construction. The original binary, prepared listing,
and final binary are therefore different representations. The internal
LLM similarity score compares prepared and returned listings, excluding
changes already made during preparation.
''')
s=para(s, 'The experiments request', r'''The requested model is \texttt{deepseek-flash}; local version names come
from the client's alias table, without independent provider confirmation.
Both LLM roles request temperature 0.2, with no sampling seed or explicit
top-p. Repeated requests are not treated as deterministic reproductions.''')
s=span(s, 'If structural validation rejects', r'\subsection{From a Proposed Listing', r'''
Validation feedback returns a rejected answer and its diagnostic---for
example, a missing label or assembly failure---and requests a correction.
It contains neither a functional success signal nor a scanner verdict.
The controlled benchmark disables correction and makes three independent
single-generation requests per cell, retaining failures. The original-corpus
campaign targets one output per cell, with some retries and failed
restarts in its logs. Its results are cell outcomes rather than uniform
first-generation success rates (Section~\ref{sec:methodology}).
''')
s=span(s, 'Functional assessment then uses', '\nThe functional test is applied', r'''
An external \emph{test harness} launches the output and records its result.
It compares the complete expected buffer for controlled programs and
checks the class-specific observable for original payloads
(Section~\ref{sec:methodology}).
''') if '\nThe functional test is applied' in s else s
s=para(s, 'Functional assessment then uses', r'''An external \emph{test harness} launches the output and records its result.
After generation, it compares the complete expected buffer for controlled
programs and checks the class-specific observable for original payloads
(Section~\ref{sec:methodology}). Records distinguish requests, accepted
outputs, execution outcomes, duration, and cost.''') if 'Functional assessment then uses' in s else s
save('sections/extension_llm.tex',s)

s=read('sections/extension_methodology.tex')
s=span(s, 'The 13 \\emph{controlled functional programs}', 'The original corpus contains', r'''
The 13 \emph{controlled functional programs} (test fixtures) are purpose-built
assembly programs of 19--68 bytes. Six per architecture cover arithmetic,
branches, loops, local calls, combined control flow, and embedded strings;
one extra x64 case accesses data through a computed code address. Each
writes a known result into a 256-byte buffer. A native C runner compares
the entire buffer, including untouched positions, with the expected bytes.
All 13 originals pass.

The six \emph{annotated classification programs} instead test data
locations: two contain multiple strings, one a binary table, two no
separate data, and one instruction bytes resembling text. Correct regions
are annotated before either classifier runs and withheld from the model.
These suites check individual mechanisms; original payloads provide the
broader application-level evaluation.
''')
s=para(s, 'An experimental \\emph{cell}', r'''A \emph{cell} combines an input, transformation, and prompting condition:
for example, one x64 program transformed with EQ and two examples.
Repeating that combination gives repetitions of the same cell.''')
s=para(s, 'The requested LLM temperature', r'''Both LLM roles request temperature 0.2 without a sampling seed or top-p;
these client settings do not imply identical repeated answers.''')
s=span(s, 'For classification, \\emph{predicted}', r'\subsection{Similarity, Detection Rate', r'''
For classification, predicted positions $P$ are bytes labelled as data;
reference positions $G$ are the preannotated correct data bytes. Precision
is $|P\cap G|/|P|$ and recall is $|P\cap G|/|G|$. For a reference string
at bytes 20--29, predicting 20--27 gives 100\% precision and 80\% recall.
Exact matching requires all intervals to agree; programs without separate
data require an empty set. For unannotated original payloads, the evaluation
reports agreement between methods and downstream functionality.
''')
s=para(s, r'\paragraph{Representation measurements.}', r'''\paragraph{Representation measurements.}
Historical cosine and entropy definitions are retained. The LLM client's
SequenceMatcher compares prepared and returned listings, filtering
NOP-like operations in the NOP condition. This diagnostic is supplied in
the supplementary records rather than substituted for the historical metrics.''')
save('sections/extension_methodology.tex',s)

s=read('sections/extension_results.tex')
# Retain the short outcome-led introduction to the new results.
s=para(s, 'Both methods correctly identify', r'''On the 19 original data-handling inputs, both pipelines build 19/19
outputs and pass 17/19 checks. Their intervals agree in 9/19 cases and
their final binaries in 16/19: shared handling can reconcile different
proposals. These measure agreement between methods; the annotated tests
above measure classification against known answers. The two shared
functional failures are the x86 custom and Meterpreter WinHTTP cases.
On three x64 WinHTTPS inputs, different accepted regions still yield
working outputs.''')
# The paragraph containing the original comparison also contains its timing;
# restore those observations explicitly if that replacement removed them.
if '59.88' not in s and '59.9' not in s:
    at=s.index(r'\subsection{Functional Tests')
    s=s[:at]+r'''Median end-to-end duration is 123.95 seconds for symbolic preparation and
59.88 seconds for the LLM arm; the latter costs \$0.2218 over 19 runs.
The two shared failures are the x86 custom and Meterpreter WinHTTP cases.
On three x64 WinHTTPS inputs, different accepted data regions still yield
working outputs.

'''+s[at:]
s=s.replace('The\noriginal published figure is retained as the baseline; the update appears\nhere with its construction stated explicitly.',
'''Historical and updated rates appear together in the table, with the
reconstruction stated explicitly.''')
save('sections/extension_results.tex',s)

s=read('sections/extension_discussion.tex')
s=span(s, 'The selected-subset recovery comparison', 'The controlled suites', r'''
Recovery tests show improved functionality on the selected difficult
inputs, with a larger gain on x64. The full-corpus wrapping and LLM
campaigns complement this comparison by assessing the added modes on all
102 inputs.
''')
s=para(s, 'The two LLM roles remain distinct.', r'''The two LLM roles remain distinct. Data identification feeds shared
handling, giving identical binaries in 16/19 original cases and matching
17/19 functional outcomes. Assembly transformation proposes a new listing;
zero-shot and two-shot have similar aggregate outcomes. Input size,
construction success, and execution outcome offer more informative
distinctions in this campaign.''')
save('sections/extension_discussion.tex',s)

s=read('sections/overall_working_table.tex')
s=s.replace('Historical measurements', 'Historical measurements')
s=s.replace('Historical input weights are held fixed.', 'Historical rates are recomputed from the retained test records of~\\cite{zone_secrypt_2026}; input weights are held fixed.')
save('sections/overall_working_table.tex',s)

# Leave the wrapping explanation intact: it was recently clarified at the
# author's request and already occupies a short section.
save('sections/extension_wrapping.tex',read('sections/extension_wrapping.tex'))

def count(s):
    for env in ['figure','table','lstlisting','algorithm']:
        s=re.sub(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}', '',s,flags=re.S)
    return len(re.findall(r'\b[A-Za-z]+\b',s))
files=['main.tex']+[str(p.relative_to(BACKUP)) for p in (BACKUP/'sections').glob('extension_*.tex')]
stats={name:{'before_prose_tokens':count(read(name)),'after_prose_tokens':count((ROOT/name).read_text(encoding='utf-8'))} for name in files}
(EVIDENCE/'compression_counts.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
print(json.dumps(stats,indent=2))
