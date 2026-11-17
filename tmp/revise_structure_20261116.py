from pathlib import Path
import shutil, re, json

root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
back=root/'before_structure_revision_20261116'
if not back.exists():
    back.mkdir()
    for name in ('main.tex','main.pdf','bibliography.bib','README_REVISIONE.md'):
        shutil.copy2(root/name,back/name)
    shutil.copytree(root/'sections',back/'sections')
s=(back/'main.tex').read_text(encoding='utf-8')

def replace_region(start,end,new):
    global s
    a=s.index(start); b=s.index(end,a+len(start))
    s=s[:a]+new.strip()+'\n\n'+s[b:]

replace_region(r'\begingroup',r'\begin{abstract}','')
replace_region(r'\paragraph{Motivation and Contributions of the Extension.}',
               'The original architecture, PII design, experiments, and comparison with',r'''
\paragraph{Motivation and Contributions of the Extension.}
In this article, we extend our SECRYPT 2026 paper~\cite{zone_secrypt_2026},
which introduced Zone and evaluated 102 payloads under 15 transformation
configurations. The original study revealed substantial functional loss.
One cause is embedded data: a disassembler can interpret a string as
instructions, which rewriting then modifies. Preserving the bytes also
requires maintaining their references when the layout changes. We address
these issues and extend the transformation and evaluation framework with:
\begin{itemize}
\item Alternative symbolic/heuristic and LLM data classifiers, followed by
shared handling of supported data and references
(Section~\ref{sec:code_data}).
\item An LLM transformation path for EQ, NOP, BCF, and IBP, with zero-shot
and two-shot prompting (Section~\ref{sec:llm_transform}).
\item Integration and assessment of the existing assembly-wrapping
technique on x64 and x86 (Section~\ref{sec:wrapping}).
\item New experiments on annotated programs, controlled functional
programs, and the original corpus, including recovery tests, static
detection, output diversity, and cost
(Sections~\ref{sec:methodology} and~\ref{sec:extended_results}).
\end{itemize}''')
# Resolve the actual existing label rather than introduce a dangling reference.
llm=(root/'sections/extension_llm.tex').read_text(encoding='utf-8')
llm_label=re.search(r'\\section\{[^}]+\}\\label\{([^}]+)\}',llm).group(1)
s=s.replace(r'\ref{sec:llm_transform}',r'\ref{'+llm_label+'}')
s=s.replace('describe their evaluation. Discussion, related work, and conclusions follow\nin Sections~\\ref{sec:extension_limits}--\\ref{sec:conclusion3}.',
'''describe their evaluation. Section~\\ref{sect:related_work} positions the
contributions within prior research, and Section~\\ref{sec:conclusion3}
discusses the findings and concludes the article.''')

# Shorten repeated exposition in the historical sections; retain every table,
# plot, listing, algorithm, numerical result, and source attribution.
s=s.replace('The following background distinguishes metamorphic rewriting from polymorphic encoding and introduces the transformation families used in the baseline evaluation.\n\n','')
replace_region(r'\subsection{Metamorphic Engines}\label{sub:meth}',r'\subsection{Morphing Techniques}',r'''
\subsection{Metamorphic Engines}\label{sub:meth}
A metamorphic engine changes instructions while aiming to preserve
control flow, references, and relevant processor
state~\cite{historycodeobf,identifyingmeth,metworm}. Its rewritten body
executes directly. Polymorphic encoding instead uses a decoding stage:
Shikata Ga Nai varies its stub, but recurring features may remain
recognizable~\cite{sgnstrong}, and decoding can expose the original body
to memory analysis~\cite{codeExtraction}.''')
replace_region(r'\subsection{Morphing Techniques}',r'\paragraph{Equal Code Substitution.}',r'''
\subsection{Morphing Techniques}
The baseline considers EQ, NOP insertion, IBP, and BCF, separately and in
selected combinations. They change instruction vocabulary, add operations,
rearrange blocks, or introduce branches and unreachable regions.
PII additionally separates placement from logical execution order
(Section~\ref{sec:pii}). The following summarizes the original
design~\cite{zone_secrypt_2026}; Section~\ref{sect:related_work} discusses
its antecedents.''')
replace_region(r'\paragraph{Equal Code Substitution.}',r'\begin{table}',r'''
\paragraph{Equal Code Substitution.}
EQ replaces an operation with an alternative representation, such as
\texttt{XOR rax, rax} and \texttt{MOV rax, 0x0}. Equivalent effects on one
register do not imply preservation of all processor state.
Table~\ref{tab:instruction_substitutions_x86} reproduces the original
substitution examples, including arithmetic and stack-based sequences.
This transformation family has a long
history~\cite{desai2008towards,desai2010highly,szor2001hunting}.''')
replace_region(r'\paragraph{NOP/Dead Code Insertion.}',r'\begin{table}',r'''
\paragraph{NOP/Dead Code Insertion.}
Inserted operations are intended to leave the relevant computation
unchanged. Table~\ref{tab:nop_instructions} lists the original examples.
Arithmetic no-ops can still affect processor flags; the original
implementation therefore used the flag-preserving sequence in
Table~\ref{tab:flag_preserving_nop}. Such repeated sequences may themselves
become recognizable artifacts~\cite{pushfmeth}.''')
replace_region(r'\paragraph{Instruction Block Permutation.}',r'\paragraph{Bogus Control Flow.}',r'''
\paragraph{Instruction Block Permutation.}
IBP divides instructions into blocks, links each block to its logical
successor, permutes their placement while retaining the entry block, and
updates control-flow targets. The chosen granularity affects layout
variation and overhead. Instructions within a block can remain unchanged,
so rearrangement need not alter short internal patterns.''')
replace_region(r'\section{Zone Architecture}\label{sec:developing_meth}',r'\subsection{Position-Independent Instruction}',r'''
\section{Zone Architecture}\label{sec:developing_meth}
Zone is implemented in Python: Capstone disassembles the input, the
selected transformations modify its instruction representation, and
Keystone assembles the output. This \emph{bin2bin} interface requires
neither source code nor Program Database (PDB) symbols. Although initial
development also explored PE files, the evaluated scope remains raw
payloads~\cite{zone_secrypt_2026}. The public repository is linked in the
Data and Artifact Availability statement.''')
replace_region('The representation consists of four components:',r'\paragraph{Physical Placement.}',r'''
The representation has four components: a base-address stub (Stub1), a
redirector (Stub2), an offset table, and wrapped instructions.
Stub1 establishes the runtime location (Listing~\ref{lst:stub1}).
Each wrapper executes its original instruction and supplies its logical
index to Stub2 (Listing~\ref{lst:instrWrap}). The redirector uses the base
address and offset table to locate the successor, preserving the state
it uses before transferring control (Listing~\ref{lst:stub2red}).''')
replace_region(r'\subsection{How Instructions Are Patched}\label{sec:instr_patch}',r'\begin{algorithm}',r'''
\subsection{How Instructions Are Patched}\label{sec:instr_patch}
Moving instructions can invalidate their references. Patching updates
tracked control-flow destinations and other supported references for
the modified layout. Algorithm~\ref{alg:zonealg} reproduces the original
workflow~\cite{zone_secrypt_2026}; complete PE files introduce additional
metadata dependencies outside this evaluation.''')
replace_region(r'\subsection{Transformation Pipeline}',r'\section{Published Experimental Baseline}',r'''
\subsection{Transformation Pipeline}
Algorithm~\ref{alg:zonealg} first constructs instruction objects and an
address-indexed lookup. A label table associates tracked branches with
target objects, retaining those associations as addresses change.
Capstone's \texttt{Skipdata} option does not resolve inline data that also
decodes as instructions~\cite{bin2binobf}. After transformation, addresses
are recomputed, tracked branches are reassembled against updated targets,
and the resulting bytes are written to a raw binary. The added preparation
and transformation paths are described in
Sections~\ref{sec:code_data}--\ref{sec:wrapping}.''')
replace_region('The corpus contains 102 Windows payloads:',r'\paragraph{Testing Method.}',r'''
The corpus comprises 38 x64 and 64 x86 Windows payloads, mostly from
Metasploit, including reverse and bind shells. It represents selected
payload types rather than all Windows malware; large DLL-based components
are outside scope. Architecture comparisons also reflect the different
input memberships.''')
replace_region(r'The execution checks in Section~\ref{sec:results} assess functionality',r'\section{Limitations and Defensive Implications}',r'''
Figure~\ref{fig:cosine_similarity} shows higher similarity for EQ and IBP
than for insertion-heavy configurations. Together with length and entropy,
this characterizes representation changes. Functional preservation is
assessed separately by the execution tests in Section~\ref{sec:results}.''')

s=s.replace(r'\input{sections/extension_discussion}'+'\n','')
replace_region(r'\section{Related Work}\label{sect:related_work}',r'\begin{credits}',r'''
\input{sections/related_work}
\input{sections/conclusions}''')
s=s.replace(r'\emph{Declaration pending confirmation by all authors.}'+'\n'+
'''% TODO-AUTHORS: Insert the truthful competing-interests declaration. Do not
% replace this with a no-conflict declaration until every author has confirmed it.''',
'The authors have no competing interests to declare.')
(root/'main.tex').write_text(s,encoding='utf-8')

related=r'''
\section{Related Work}\label{sect:related_work}
\paragraph{Metamorphic rewriting and software protection.}
Instruction substitution, insertion, and control-flow changes predate
this work and appear across both offensive and defensive
research~\cite{survey1,survey2}. Earlier engines, including
W95/Regswap~\cite{desai2010highly} and MetaPHOR~\cite{MetaPHOR}, illustrate
register substitution and code reorganization. Studies of highly
metamorphic programs also examine the relationship between the diversity
of generated variants and the regularities that remain available to
detectors~\cite{desai2008towards,desai2010highly,szor2001hunting}.
Zone uses established transformation families within a payload-level
binary rewriting workflow; the contribution is evaluated through the
resulting construction, functional, and detection outcomes.

Compiler-based protection provides a different starting representation.
Obfuscator-LLVM applies transformation passes to LLVM intermediate
representation, with advantages for language and architecture
coverage~\cite{llvmobf}. Zone instead starts from raw machine code without
source or debugging symbols. The relevant distinction is the information
available before transformation: code boundaries and references must be
recovered from the binary. Consequently, findings from a compiler-based
setting do not directly establish reliability for the inputs studied here.
Practical binary-obfuscation work likewise identifies disassembly and
reference handling as central concerns~\cite{bin2binobf}.

\paragraph{LLM-based transformation.}
Madani~\cite{llm2} investigates LLM-driven program mutation and a
self-testing mutation framework, motivating the evaluation of generated
variants alongside their proposed changes. Mohseni et al.~\cite{llmobf}
introduce MetamorphASM and its MAD dataset of 328,200 assembly samples,
covering dead-code insertion, register substitution, and control-flow
changes. Their study compares multiple language models using
information-theoretic measurements and human review.

Our evaluation addresses a complementary question: how often an LLM
proposal can pass the complete path from prepared assembly to a
constructed binary and an observed functional outcome. It distinguishes
two LLM roles, data identification and instruction transformation, and
compares zero-shot and two-shot requests on a fixed input corpus.
The controlled programs provide known outputs, while the original
payloads exercise larger and more varied layouts. These experimental
populations and endpoints differ from MAD; their success rates should
therefore be read within their respective protocols rather than as a
direct ranking of the systems.

\paragraph{Analysis and detection.}
Metamorphic detection studies include Hidden Markov
Models~\cite{wong2006hunting,desai2010highly}, behavior-oriented
recognition~\cite{identifyingmeth}, and genetic-algorithm-based
methods~\cite{methgenetic}. Encoding introduces another representation
change: investigations of SGN examine recognizable properties of its
decoder~\cite{sgnstrong}, while CodeXt studies recovery of hidden attack
code from memory dumps through selective symbolic
execution~\cite{codeExtraction}. These works motivate distinguishing
static file measurements from observations of execution and memory.
The scan results reported here characterize submitted raw files; the
functional tests answer a separate question about the preserved behavior.

\paragraph{Relationship to the original Zone paper.}
Our conference article introduced the PII design and evaluated native
transformations on 102 Windows payloads~\cite{zone_secrypt_2026}. The
present article extends that study with code--data identification,
LLM-assisted transformation, and assembly-wrapping integration.
Bounded symbolic and static analysis inform the data-preparation
stage~\cite{angr_cfg_docs}; assembly wrapping follows its existing
description and antecedents in overlapping
instructions~\cite{assembly_wrapping}. The added contribution is the
integration and evaluation of these paths, including the recovery study,
controlled tests, and completed original-corpus campaigns.
'''
conclusions=r'''
\section{Conclusions}\label{sec:conclusion3}\label{sec:extension_limits}
We have extended our SECRYPT 2026 study of Zone~\cite{zone_secrypt_2026}
from its original native transformations to a broader evaluation of
binary rewriting. The extension makes code--data identification and
supported reference handling explicit, separates the LLM roles of
classification and instruction transformation, and integrates the
existing assembly-wrapping technique on x64 and x86. These additions
address the preparation and evaluation of transformed programs alongside
the transformation itself.

The recovery results demonstrate a substantial improvement on inputs
that were difficult for the earlier pipeline. Working rate rises from
1.2\% to 80.2\% on the selected x64 cohort and from 14.9\% to 25.9\% on
x86. Replacing the retested inputs' rates while retaining historical
weights gives mean configuration rates of 82.6\% and 50.3\%, compared
with 55.6\% and 45.0\% historically. This combined summary places the
recovery results in the wider corpus; it does not represent a fresh
execution of every historical test. The gain is larger on x64, while
the residual x86 cases show that the improvement is architecture- and
input-dependent.

The controlled suites and original payloads provide complementary
evidence. Six annotated programs give known answers for data
identification, and 13 functional programs isolate individual programming
patterns. Their small, simple layouts explain why their high success
rates do not automatically extend to the larger corpus. On the 19
original data-handling inputs, symbolic and LLM proposals yield identical
final binaries in 16 cases and the same 17 successful functional outcomes.
This agreement shows that different intermediate proposals can lead to
the same accepted output under shared handling. It also keeps the
classifier's contribution distinct from that of the downstream pipeline.

The full-corpus campaigns expose the difference between producing a
binary and obtaining a working variant. Wrapping constructs 243 binaries
from 306 planned cases, of which 170 pass their functional tests. Every
constructed x64 wrapping output passes, whereas x86 functionality remains
partial. LLM transformation constructs 350 binaries across 816 conditions,
with 275 successful functional outcomes. These results identify
construction failures as a substantial part of the measured outcome;
reporting only accepted outputs would conceal that part of the process.
The recorded native x86 IBP result remains tied to its tested engine
version, separately from these later campaigns.

Zero-shot and two-shot prompting produce similar aggregate outcomes in
this experiment. The evidence supports no consistent advantage for the
additional examples under the tested settings. Static scans report no
malicious responses for the 207 distinct wrapping outputs and a mean
engine detection rate of 5.06\% across 322 nonempty LLM-output reports.
These observations describe the submitted raw files and complement the
functional results. Overall, the extension demonstrates improved
functional reliability and provides a more complete account of the
added transformation paths by reporting construction, execution,
diversity, and detection together.
'''
(root/'sections/related_work.tex').write_text(related.strip()+'\n',encoding='utf-8')
(root/'sections/conclusions.tex').write_text(conclusions.strip()+'\n',encoding='utf-8')

def prose_count(text):
    text=re.sub(r'\\begin\{(figure|table|lstlisting|algorithm)\}.*?\\end\{\1\}','',text,flags=re.S)
    return len(re.findall(r"\b[A-Za-z][A-Za-z'-]*\b",text))
old=(back/'main.tex').read_text(encoding='utf-8')
split='% Added material extends the original study retained above.'
report={'historical_region_words_before':prose_count(old.split(split)[0]),'historical_region_words_after':prose_count(s.split(split)[0]),'related_work_words':prose_count(related),'conclusions_words':prose_count(conclusions),'disclosure':'No competing interests, confirmed by user on 16 November 2026','future_work':'Awaiting discussion with author; not inserted','initial_page_note':'Removed; no such placement requirement in supplied invitation','new_experiments':False}
(root/'STRUCTURE_REVISION_20261116.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
