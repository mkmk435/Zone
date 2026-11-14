from pathlib import Path
root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
sections={}
sections['extension_code_data']=r'''\section{Code--Data Identification and Data-Preserving Rewriting}
\label{sec:code_data}
\subsection{Why Data Identification Comes Before Transformation}
A raw binary does not tell a rewriting tool which bytes are instructions
and which are data. A short program may contain both executable code and
an embedded string or lookup table. A disassembler translates bytes into
assembly instructions, but the ability to decode a byte sequence does not
establish that the processor will execute it. String bytes may also decode
as plausible instructions. Rewriting those apparent instructions can
therefore corrupt a value that the program subsequently reads.

This is the failure illustrated by the inline string in
Table~\ref{tab:broken-payload}. It differs from
Table~\ref{tab:functional-payload}, where the string is encoded inside an
instruction operand: there, the surrounding instruction must remain
intact. A useful identification method must distinguish these situations,
rather than marking every printable sequence as a separate data object.

The extension introduces a preparation stage with two responsibilities.
\emph{Identification} proposes where data occurs. \emph{Data handling}
decides which proposed objects the engine can retain through a layout
change, preserves their contents, and updates supported references
to their new locations. A reference is an instruction operand or address
calculation that points to a code or data location. Preserving a string's
bytes is insufficient if the program subsequently reads its old address.

Figure~\ref{fig:extended_pipeline} locates these responsibilities in the
extended engine. The symbolic/heuristic and LLM classifiers are alternative
ways to propose data regions. Separately, the transformation itself can be
implemented by the native engine or proposed by an LLM. Thus, using an LLM
to identify data does not imply using it to rewrite instructions.

\begin{figure}[t]
\centering
\begin{tikzpicture}[
  box/.style={draw,rounded corners=2pt,align=center,font=\small,
    minimum height=0.8cm,text width=4.0cm},
  arrow/.style={-{Latex[length=2mm]},thick}]
\node[box,text width=5.7cm] (input) at (0,0) {Raw binary and target architecture};
\node[box] (sym) at (-2.35,-1.3) {Symbolic exploration\\and static heuristics};
\node[box] (llm) at (2.35,-1.3) {LLM data classifier\\(proposes regions only)};
\node[box,text width=7.4cm] (data) at (0,-2.65) {Shared data handling: check candidate regions,\\preserve supported data and track references};
\node[box,text width=7.4cm] (trans) at (0,-4.0) {Transform code: native methods, assembly wrapping,\\or LLM-proposed EQ, NOP, BCF, or IBP};
\node[box,text width=7.4cm] (build) at (0,-5.3) {Finalize layout and references; check construction};
\node[box,text width=7.4cm] (test) at (0,-6.6) {Test the produced binary with an external harness};
\draw[arrow] (input) -- (sym);
\draw[arrow] (input) -- (llm);
\draw[arrow] (sym) -- (data);
\draw[arrow] (llm) -- (data);
\draw[arrow] (data) -- (trans);
\draw[arrow] (trans) -- (build);
\draw[arrow] (build) -- (test);
\node[font=\small,fill=white] at (0,-1.3) {or};
\end{tikzpicture}
\caption{Conceptual organization of the extensions. Identification chooses
candidate data regions; shared handling preserves supported objects during
rewriting. Successful construction is followed by a separate behavioral
test. Unsupported inputs can stop before a binary is produced.}
\label{fig:extended_pipeline}
\end{figure}

\subsection{What a Classification Result Means}
For an input of $n$ bytes, a proposed data region is an interval $[s,e)$:
it starts at offset $s$ from the beginning of the input and includes every
byte up to, but not including, $e$. For example, $[2,8)$ denotes six bytes.
An optional type describes a string encoding, such as ASCII or UTF-16LE,
or another data object. The output is a set of candidate intervals,
not a replacement binary.

Three stages must be distinguished: a classifier's proposed regions,
regions accepted by the engine's checks, and regions actually extracted
from the instruction stream. A correct proposal may still be unsupported
if its references cannot be updated. Conversely, different proposals can
produce the same binary when the shared checks retain the same objects.
The experiments compare annotations, accepted outputs, and final hashes
at their respective stages.

\subsection{Symbolic Exploration Combined with Static Heuristics}
The non-LLM method combines three sources of evidence. First, static
analysis recovers a control-flow graph (CFG): nodes represent basic blocks
of instructions and edges represent possible transfers of execution.
Zone uses angr's CFGFast analysis for this initial structure~\cite{angr_cfg_docs}.
Second, symbolic execution explores possible paths while representing
unknown register and memory values as symbolic expressions. This supplies
additional evidence about which instructions can be reached. Third,
pattern-based rules look for candidate strings and graph-inferred data.

An observed instruction protects its entire decoded byte span, not only
its starting address. This matters for variable-length instructions: an
interior byte should not become a data candidate merely because the
explorer recorded only the instruction's first byte. Newly observed entry
points can also support another graph-recovery pass. Printable candidates
that overlap observed code are excluded by the string heuristic; candidates
overlapping graph-recovered code need additional structural support.

Exploration is bounded by time, solver, and state limits. The initial state
does not reproduce every feature of a Windows process, including all
external API behavior. Consequently, an unvisited region is \emph{unknown},
not proven to be data. Reports retain the evidence category, stopping
reason, unresolved states, and errors. These distinctions prevent a
partial execution search from being presented as a complete partition of
the binary into code and data.

\subsection{LLM Identification and Shared Data Handling}
The alternative classifier receives the raw bytes in hexadecimal, a
linear disassembly, and candidate printable strings. Linear disassembly
means decoding instructions in byte order; its listing is evidence for the
model to assess, not a trusted annotation. The requested answer contains
structured data intervals. The model does not perform extraction or
rewrite the program in this mode.

Deterministic parsing rejects intervals outside the input, empty intervals,
and invalid overlaps. The engine then examines supported references and
applies its data-handling rules to a fresh working instance. Accepted data
contents are retained separately from the instruction representation;
supported references are finalized after transformation, when the new
locations are known. Integrity checks verify the preserved contents.
Architecture-specific addressing requires separate x64 and x86 handling.

For a benign example, consider a routine that copies the embedded strings
\texttt{alpha} and \texttt{beta} into an output buffer. Identification finds
the two string regions; handling preserves both strings and their links
to the copying code; transformation changes the instruction representation.
The final test checks that the intended strings reach the intended buffer
positions. Correct interval identification, successful reference handling,
and correct observed output are three distinct questions in this example.

The general classifier can receive validation feedback and make another
proposal. Its worked-example setting is independent of the zero-shot and
two-shot transformation conditions defined next. Cached identification can
reuse regions associated with an input identity, while references are
recomputed for the working representation. These shared steps also explain
why agreement between final binaries is not, by itself, a measure of the
LLM classifier's accuracy.
'''
sections['extension_llm']=r'''\section{LLM-Assisted Assembly Transformation}\label{sec:llm}
\subsection{What the Model Is Asked to Change}
In transformation mode, the LLM receives an assembly representation and
proposes a new instruction sequence intended to preserve the program's
behavior. This differs from Section~\ref{sec:code_data}, where its answer
contains only data locations. Zone supports four transformation requests:
equal code substitution (EQ) replaces instruction sequences; NOP insertion
adds operations intended to leave the relevant state unchanged; bogus
control flow (BCF) adds control-flow structure without changing the intended
outcome; and instruction block permutation (IBP) changes the placement of
blocks while retaining their execution relationships. These are the
families introduced in Section~\ref{sec:background}; the LLM proposes their
application rather than introducing a fifth family. PII and assembly
wrapping remain native engine operations.

Before the request, Zone prepares a \emph{canonical assembly listing}: a
working representation with symbolic labels for relevant locations and
the extracted data kept separately. Labels name locations without fixing
their final byte offsets, which will change when instruction lengths or
block positions change. The model returns the complete proposed code
listing. The deterministic pipeline then assembles it, restores the
preserved data representation, and validates the result. The original
binary, this prepared listing, and the final binary are therefore different
representations; a similarity score between listings does not measure
every change made since the original input.

The experiments request \texttt{deepseek-flash}. The locally recorded
version name comes from the client's alias table, rather than independent
provider confirmation, so the requested identifier is the reproducible
model designation available in these records.

\subsection{Prompting Conditions and Repeated Attempts}
A \emph{zero-shot} request describes the transformation and its constraints
without a worked example. A \emph{two-shot} request adds two examples of
input and transformed output. The number of shots thus counts examples
inside a prompt; it does not count generated variants or execution tests.
Each input, transformation family, and shot setting defines an experimental
\emph{cell}.

The general pipeline may send a rejected answer back with validation
feedback and request a correction. Such a later attempt has information
that was absent from the initial request. The benign benchmark disables
this mechanism and performs three separate, single-generation invocations
per cell, retaining every failure. The full-payload campaign instead
targets one output per cell, with some retries and restarted failed runs
present in the saved logs. Its results are reported as cell outcomes, not
as first-generation success rates. Section~\ref{sec:methodology} gives the
exact accounting for both protocols.

\subsection{From a Proposed Listing to an Assessed Output}
Validation checks whether the response can be assembled and decoded,
whether tracked control-flow targets remain consistent, whether preserved
data survives, and whether the requested transformation's structural
requirements are met. A response can fail at any of these stages, or be
truncated before it contains a complete listing. Passing them means that
Zone accepts a constructed output; it does not prove behavioral equivalence.

Functional assessment then uses an external \emph{test harness}, meaning
the program that launches a test and records its observable result. For
the benign fixtures, it compares a complete output buffer with the expected
bytes fixed before generation. For the original payloads, it checks the
class-specific observable described in Section~\ref{sec:methodology}.
Neither test selects generations within these two experiments. The earlier
MessageBox pilot did use its dialog check during generation and is therefore
kept separate. Saved records distinguish model requests, accepted outputs,
execution results, time, and estimated cost, allowing rejection and execution
failure to be analyzed independently.
'''
sections['extension_wrapping']=r'''\section{Assembly Wrapping: Mechanism and Integration}\label{sec:wrapping}
\subsection{The Same Bytes Can Have Two Instruction Interpretations}
Assembly wrapping changes how executable bytes are arranged and interpreted.
It uses the variable length of x86 and x64 instructions: decoding the same
bytes from different starting positions can produce different instruction
sequences. In the existing wrapping technique, bytes belonging to the
intended computation are placed within the immediate-operand field of a
larger instruction~\cite{assembly_wrapping}. An \emph{immediate operand} is
a constant stored directly in an instruction's encoding. A decoder starting
at the outer instruction reads that field as a constant; execution entering
the embedded sequence reads it as instructions instead.

Figure~\ref{fig:wrapping_views} illustrates the distinction without relying
on a particular encoding. The \emph{container} is the outer instruction
whose operand holds the embedded bytes. The execution path connects the
embedded sequences in their intended order, whereas a static listing
following the container boundaries shows a different instruction sequence.
The bytes need not be decrypted to obtain that second interpretation.
This is a representation technique based on overlapping instructions, not
a new form of encryption or a guarantee that an analyzer cannot recover
the executed code.

\begin{figure}[t]
\centering
\begin{tikzpicture}[font=\small]
\node[anchor=east] at (0,0.5) {Stored bytes};
\draw[fill=gray!15] (0.15,0.15) rectangle (2.7,0.85);
\draw[fill=blue!8] (2.7,0.15) rectangle (7.4,0.85);
\node at (1.425,0.5) {Outer opcode};
\node at (5.05,0.5) {Immediate-operand field};
\node[anchor=east] at (0,-0.65) {Outer view};
\node[draw,align=center,text width=6.9cm] at (3.775,-0.65)
  {One instruction containing a constant operand};
\node[anchor=east] at (0,-1.8) {Execution view};
\node[draw,fill=blue!8,align=center,text width=4.1cm] (inside)
  at (5.05,-1.8) {Embedded instruction sequence};
\draw[-{Latex[length=2mm]},thick] (2.7,0.15) -- (2.7,-1.8) -- (inside.west);
\end{tikzpicture}
\caption{Conceptual views of a wrapped region. Starting at the outer
opcode interprets the operand as a constant; entering the embedded
sequence interprets some of those same bytes as instructions.
The drawing is not to scale and omits inter-region control transfers.}
\label{fig:wrapping_views}
\end{figure}

\subsection{What Zone Adds and What the Transformation Requires}
The contribution of this work is the integration and assessment of an
existing technique, with implementations for both architectures. Zone
starts from a prepared instruction stream, groups supported instructions
into wrapped regions, preserves the required execution relationships, and
updates the supported location-dependent references after layout. Some
instructions or local layouts cannot be placed in the main container
representation; the implementation retains these in separate, unwrapped
regions. An output may therefore contain both wrapped and ordinary code.

The x86 and x64 implementations share this purpose but use different
encodings and addressing rules. In particular, the available immediate
operand has a different width, affecting which instruction groups fit.
The x86 implementation was introduced after the first benign benchmark
snapshot and is evaluated under its own recorded version.

Data preparation remains necessary. Wrapping does not determine whether
an apparent instruction is actually an embedded string or table. If that
earlier interpretation is wrong, construction may be refused or the output
may fail when executed. Successful relocation checks likewise cover the
references the engine supports, not every possible address computation.

\subsection{What the Evaluation Can Establish}
Three questions follow from this mechanism: can Zone construct an output
for the input, does that output pass its behavioral test, and what do static
scanners report for the produced bytes? These questions have different
denominators. A scan cannot evaluate an unbuilt output, and an absence of
malicious verdicts does not demonstrate that a constructed output works.
The following experiments therefore report build availability, functional
outcomes, and scan results separately, including the failures on the full
102-payload corpus rather than only the successful benign examples.
'''
for name,text in sections.items(): (root/'sections'/f'{name}.tex').write_text(text,encoding='utf-8')
print('Rewrote',', '.join(sections))
