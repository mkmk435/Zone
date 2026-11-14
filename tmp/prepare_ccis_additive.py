from pathlib import Path
import re
import json
import hashlib

PROJECT=Path(r'C:\Users\ubu\Desktop\CCIS')
STAGE=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_additive_20261113')
original=(PROJECT/'backup_before_extension_20261113/main.tex').read_text(encoding='utf-8')
s=original
s=re.sub(r'\A.*?(?=\\documentclass)', '% Extended CCIS working manuscript: original study retained, extensions appended.\n% New results and x86 wrapping evaluation remain in progress.\n',s,flags=re.S)
s=s.replace(r'\usepackage{xcolor}',r'''\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{xurl}''')
s=s.replace(r'\usetikzlibrary{patterns,positioning}',r'\usetikzlibrary{patterns,positioning,arrows.meta}')
macros=r'''
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\definecolor{draftblue}{RGB}{24,73,114}
\newif\ifworkingdraft
\workingdrafttrue
\newcommand{\draftnote}[1]{\ifworkingdraft\par\smallskip\noindent
 {\color{draftblue}\small\textbf{Draft note.} #1}\par\smallskip\fi}
\newcommand{\pending}{\textit{pending}}
\newcommand{\dev}{\textit{in development}}
'''
s=s.replace(r'\begin{document}',macros+'\n'+r'\begin{document}',1)
s=s.replace(r'\title{Zone: Design and Empirical Assessment of Binary Metamorphism for Windows Payloads}',r'\title{Zone: Extending a bin2bin Metamorphic Engine with Code--Data Identification and LLM Assistance}')
s=s.replace(r'\titlerunning{Design and Empirical Assessment of Zone}',r'\titlerunning{Zone: An Extended bin2bin Metamorphic Engine}')
abstract=r'''\begin{abstract}
Zone is a binary-to-binary metamorphic engine for compact Windows x86
and x64 payloads. Its instruction substitution, insertion, and
control-flow transformations include the Position-Independent Instruction
representation introduced in the conference version of this work.
This extended article retains the original design and empirical study
of 102 inputs under fifteen configurations, assessed through static-scan
verdicts, functional checks, size, entropy, and similarity. The published
observations show that changes in detectability and functional
preservation must be evaluated separately. Building on the code--data
ambiguity identified in that study, we add a data-handling layer with
symbolic and heuristic identification and an alternative LLM-based
classification path. We also describe LLM-assisted assembly
transformation with zero-shot and two-shot conditions and integrate
assembly wrapping as an existing technique, with its x86 port under
development. A separate assessment protocol addresses classification
quality, construction success, working rate, static-scan measurements,
representation similarity, output diversity, and cost. The original
results provide the empirical foundation for the extension, while new
campaigns are identified independently. Conclusions remain bounded by
the input scope, observation protocol, and raw-binary scan setting.
\keywords{Binary Rewriting \and Metamorphic Code \and
Code--Data Identification \and Large Language Models \and Functional Preservation}
\end{abstract}
\draftnote{The original study and its detailed results are retained.
Additional experiments are in progress; their numerical results remain
pending. The x86 wrapping port is development work. Update the abstract
and conclusions with the verified extension findings before submission.}'''
s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:abstract,s,count=1,flags=re.S)
start=s.index(r'\paragraph{Relationship to the Conference Paper.}')
end=s.index('The scope is restricted',start)
contributions=r'''\paragraph{Relationship to the Conference Paper and Extensions.}
This article extends our SECRYPT 2026 study~\cite{zone_secrypt_2026}.
It retains the engine description, PII design, original experimental
protocol, detailed results, and comparison with Shikata Ga Nai as the
foundation of the extended investigation. Reused figures, tables,
listings, and the algorithm carry source citations. Additional sections
address the limitations identified by that study through:
\begin{itemize}
\item symbolic and heuristic code--data identification, an alternative
LLM-based classifier, and shared deterministic data handling;
\item LLM-assisted assembly transformation with zero-shot and two-shot
conditions, validation, and feedback;
\item integration and assessment of assembly wrapping, an existing
technique, with the x86 implementation under development;
\item additional evaluation of classification quality, build and
functional outcomes, static verdicts, similarity, diversity, and cost.
\end{itemize}
The extension complements the original experiments. Its methods and
results are identified separately so that the published findings remain
available for comparison and are not conflated with new measurements.

'''
s=s[:start]+contributions+s[end:]
oldroad='Section~\\ref{sec:background} introduces the transformations.'
start=s.index(oldroad)
end=s.index(r'\section{Background}',start)
s=s[:start]+r'''Sections~\ref{sec:background} and~\ref{sec:developing_meth} retain
the background and engine design. The original experiments and
representation measurements appear in Sections~\ref{sec:results}
and~\ref{sect:var_metrics}, followed by their limitations and the SGN
comparison (Sections~\ref{sec:limitations} and~\ref{sec:comparison}).
Sections~\ref{sec:code_data}, \ref{sec:llm}, and~\ref{sec:wrapping}
describe the additional methods. Sections~\ref{sec:methodology}
and~\ref{sec:extended_results} define and reserve the extended
assessment. Section~\ref{sect:related_work} discusses related work and
Section~\ref{sec:conclusion3} concludes.

'''+s[end:]
s=s.replace('This manuscript retains the payload-level scope of the conference paper~\\cite{zone_secrypt_2026};', 'The extended manuscript retains the payload-level scope of the conference paper~\\cite{zone_secrypt_2026};')
s=s.replace('The published workflow in Algorithm~\\ref{alg:zonealg} can be read as six stages:', 'The original workflow in Algorithm~\\ref{alg:zonealg} can be read as six stages. The additional analysis and transformation paths are described in Sections~\\ref{sec:code_data}--\\ref{sec:wrapping}.')
s=s.replace('% TODO-NEW-MATERIAL: Insert the new evaluation and its independently documented\n% protocol/results here, or introduce a separate section before the conclusion.','% Extended assessment follows the original results and SGN comparison.')
s=s.replace('Two implementation limitations were identified in the conference paper~\\cite{zone_secrypt_2026}:','The following limitations concern the original implementation and experiments~\\cite{zone_secrypt_2026}. Sections~\\ref{sec:code_data}--\\ref{sec:wrapping} describe subsequent work motivated by these observations; the residual limits of the added paths are discussed in Section~\\ref{sec:extension_limits}.')
baseline_note=r'''\draftnote{The detailed historical plots and their reported numerical
values are retained from the preparation manuscript. Some category/value
associations in the detection and working-rate plots, and the provenance
of the similarity metric, require reconciliation against the conference
version and archived records. These are baseline editorial checks,
not replacement experiments. See BASELINE_CHECKS.md.}
'''
s=s.replace(r'\section{Published Experimental Baseline}\label{sec:results}',r'\section{Published Experimental Baseline}\label{sec:results}'+'\n'+baseline_note)

# Reuse the newly written methods as additions, avoiding repetition of old examples.
data=(PROJECT/'sections/04_code_data.tex').read_text()
a=data.index('This distinction is important for strings')
b=data.index('The task also includes uncertainty.',a)
data=data[:a]+r'''The original inline-data failure in Table~\ref{tab:broken-payload}
and the immediate-operand example in Table~\ref{tab:functional-payload}
motivate this extension. Both examples and their interpretation remain
in Section~\ref{sec:limitations}; the added layer explicitly represents
candidate data and the references affected by rewriting.

'''+data[b:]
data=data.replace('The evaluation in Section~\\ref{sec:methodology}', 'The additional evaluation in Section~\\ref{sec:methodology}')
(STAGE/'sections/extension_code_data.tex').write_text(data,encoding='utf-8')
llm=(PROJECT/'sections/05_llm.tex').read_text()
(STAGE/'sections/extension_llm.tex').write_text(llm,encoding='utf-8')
wrapping=(PROJECT/'sections/06_wrapping.tex').read_text()
(STAGE/'sections/extension_wrapping.tex').write_text(wrapping,encoding='utf-8')

evaluation=r'''\section{Additional Experimental Methodology}\label{sec:methodology}
\subsection{Questions and Experimental Record}
The additional experiments complement the original fifteen-configuration
study. They examine (i) identification quality and agreement between
the two code--data paths, (ii) construction and functional outcomes
after data handling, (iii) architecture-specific wrapping outcomes,
and (iv) zero-shot versus two-shot LLM transformation. The original
corpus and its measurements remain those of
Sections~\ref{sec:results} and~\ref{sect:var_metrics}.

Each new campaign records distinct inputs, selection criteria,
architecture, configuration, repetitions, input/output hashes, and
engine version or snapshot. A subset selected for low historical
working rate is reported as a subset, not a new assessment of the
whole corpus. Model identifier, prompt examples, generation parameters,
retry policy, dependency versions, and cache status are retained where
applicable. A run is distinguished from attempts within that run and
from a reused artifact; run numbers do not imply controlled model seeds.

\subsection{Code--Data Quality and Downstream Outcomes}
Reference-based identification measures use independently annotated
data-byte offsets $G$ and predicted offsets $P$. With data as the
positive class, precision is $|P\cap G|/|P|$, recall is
$|P\cap G|/|G|$, and $F_1$ is their harmonic mean. Undefined cases and
unresolved reference bytes are identified explicitly. Interval-level
agreement complements byte scores, with the boundary or overlap rule
specified in the report. Raw candidates and accepted intervals are
assessed separately to distinguish classification from filtering.

Without independent annotations, the analysis is a case study of
agreement and downstream functionality. Agreement with the symbolic
method does not make that method ground truth, and byte-identical
outputs do not establish identical raw proposals. Analysis limits,
unresolved states, and computed versus cached runtimes accompany the
identification outcomes.

For $N$ planned cases, $B$ accepted binaries, and $W$ successful
functional checks, the additional assessment reports
\begin{equation}
\mathrm{BuildRate}=B/N,\qquad
\mathrm{WorkingRate}_{\mathrm{all}}=W/N,\qquad
\mathrm{WorkingRate}_{\mathrm{built}}=W/B.
\end{equation}
Counts accompany percentages. Unbuilt cases remain in the planned-case
denominator, and uncompleted tests remain distinct from completed
failures. The observable, harness version, architecture, and observation
window are stated. Connections, open ports, dialogs, and clean
termination provide different empirical checks rather than a general
proof of equivalence.

For LLM runs, initial acceptance and acceptance within the retry budget
are separated. If the functional verifier participates in output
selection, the pass rate on accepted outputs is conditional on that
selection. Exhausted and restarted runs, including their time and
cost, remain part of the record.

\subsection{Static Verdicts, Similarity, and Cost}
The published detection definition is retained for comparison. For a
completed file, $d_i=m_i/a_i$ is the malicious-verdict fraction, with
$m_i$ malicious verdicts and $a_i$ engines under the declared eligibility
rule. The new report also distinguishes the fraction of completed
files with any malicious verdict:
\begin{equation}
\overline d=\frac{1}{F}\sum_{i=1}^{F}d_i,\qquad
q=\frac{1}{F}\sum_{i=1}^{F}\mathbf{1}[m_i>0].
\end{equation}
Unsupported engines, errors, timeouts, scan dates, and pending analyses
are accounted for explicitly. Pending is not zero detection. Identical
hashes may reuse a scan while retaining their membership in several
experimental conditions. The aggregation states whether payloads,
runs, or distinct binaries receive equal weight.

The original size, entropy, and cosine measurements are retained in
Section~\ref{sect:var_metrics}. The additional LLM validation score uses
\texttt{SequenceMatcher} on normalized instruction signatures,
not cosine similarity~\cite{python_difflib}. Its matching-block ratio
is $2M/(u+v)$ for $M$ matched elements and sequence lengths $u,v$.
The NOP condition additionally removes recognized no-op operations;
a score of one under that representation does not imply byte identity.
The original file and the prepared intermediate representation are
distinguished as comparison references. Any new cosine measure states
its token vocabulary and whether comparisons are paired or pooled.
Wrapping measurements also identify the decoding view.

Distinct output hashes characterize exact diversity independently of
similarity. Size is reported as bytes and paired relative change.
Timing separates analysis, preparation, API calls, and local checks
where available. Costs include rejected attempts and state the tariff
snapshot and estimation rule. Repetitions of the same payload are
grouped for uncertainty analysis; small pilots retain case-level scope.

\subsection{Validity of the Extensions}\label{sec:extension_limits}
The original limitations remain relevant. Bounded exploration can
miss paths because of missing environment behavior or resource limits;
LLM and deterministic paths can share errors; and structural validation
does not establish full semantic preservation. Changes in the harness,
dependencies, input selection, or engine version can affect apparent
working-rate improvements. Historical and new scans also differ in
time and service conditions. Architecture-specific development,
especially x86 wrapping, is associated with its own frozen version
and assessment rather than inferred from x64 results.
\draftnote{Finalize input counts, repetitions, model configuration,
annotations, harness, scan eligibility, and aggregation from the completed
campaigns. Preserve the original measurements as the published comparison.}
'''
(STAGE/'sections/extension_methodology.tex').write_text(evaluation,encoding='utf-8')

results=r'''\section{Additional Experimental Results}\label{sec:extended_results}
The results below are additional to the full published study retained
in Sections~\ref{sec:results}--\ref{sec:comparison}. New campaign outcomes
will be associated with their own inputs, versions, and observation
protocol. They do not silently replace the historical measurements.

\subsection{Code--Data Identification and Functional Outcomes}
\draftnote{Insert the completed comparison, independent reference
annotations if available, candidate/accepted interval results, analysis
time, and functional outcomes after extraction. Keep selection and
architecture explicit.}
\begin{table}[t]
\caption{Additional code--data assessment; entries await finalized
experiments. Use agreement/case-study reporting if independent labels
are unavailable.}
\label{tab:new_data_results}
\centering\small
\begin{tabularx}{\linewidth}{@{}Yllll@{}}
\toprule
Method & Inputs & Precision$_D$ & Recall$_D$ & $F_{1,D}$ \\
\midrule
Symbolic/heuristic & \pending & \pending & \pending & \pending \\
LLM classification & \pending & \pending & \pending & \pending \\
\bottomrule
\end{tabularx}
\end{table}
The final analysis will separate a changed classification from a
changed acceptance decision or functional oracle. Any current
working-rate comparison with the original study will state changes
in corpus selection, preparation, and testing conditions.

\subsection{Assembly Wrapping}
\draftnote{Insert build counts, working rates, size, diversity, and
completed static scans. x86 remains development work until its version
and architecture-specific campaign are fixed.}
\begin{table}[t]
\caption{Additional wrapping outcomes. Report both planned-case and
constructed-output working rates; static results refer to completed scans.}
\label{tab:new_wrap_results}
\centering\small
\begin{tabularx}{\linewidth}{@{}Yllll@{}}
\toprule
Condition & $B/N$ & $W/N$ & $W/B$ & $\overline d$ \\
\midrule
x64 wrapping & \pending & \pending & \pending & \pending \\
x64 wrapping, combined & \pending & \pending & \pending & \pending \\
x86 wrapping & \multicolumn{4}{c}{\dev} \\
x86 wrapping, combined & \multicolumn{4}{c}{\dev} \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{LLM Transformation: Zero-Shot versus Two-Shot}
\draftnote{Insert the final input/run counts, initial and final acceptance,
functional outcomes, static verdicts, normalized sequence similarity,
output uniqueness, attempts, time, and estimated cost. Record the scope
of the pilot and the role of the generation-time verifier.}
\begin{table}[t]
\caption{Additional LLM transformation results. Similarity denotes
the normalized sequence score, distinct from the historical cosine
measure. Pending scans have no measured detection fraction.}
\label{tab:new_llm_results}
\centering\small
\begin{tabularx}{\linewidth}{@{}Yllll@{}}
\toprule
Family / shots & Runs & $W/N$ & $\overline d$ & Similarity \\
\midrule
EQ / 0 & \pending & \pending & \pending & \pending \\
EQ / 2 & \pending & \pending & \pending & \pending \\
NOP / 0 & \pending & \pending & \pending & \pending \\
NOP / 2 & \pending & \pending & \pending & \pending \\
BCF / 0 & \pending & \pending & \pending & \pending \\
BCF / 2 & \pending & \pending & \pending & \pending \\
IBP / 0 & \pending & \pending & \pending & \pending \\
IBP / 2 & \pending & \pending & \pending & \pending \\
\bottomrule
\end{tabularx}
\end{table}
The comparison will interpret representation changes alongside
construction and functional outcomes. Similarity alone does not
establish correctness, and accepted outputs do not characterize the
success rate of first attempts or exhausted runs.
'''
(STAGE/'sections/extension_results.tex').write_text(results,encoding='utf-8')

insert=r'''% Added material extends the original study retained above.
\input{sections/extension_code_data}
\input{sections/extension_llm}
\input{sections/extension_wrapping}
\input{sections/extension_methodology}
\input{sections/extension_results}

'''
s=s.replace(r'\section{Related Work}\label{sect:related_work}',insert+r'\section{Related Work}\label{sect:related_work}',1)
related=r'''
The extensions additionally connect data identification with bounded
symbolic and static analysis~\cite{angr_cfg_docs}, and distinguish LLM
classification from assembly transformation. Assembly wrapping is
attributed to its existing description and acknowledged antecedents
in overlapping instructions~\cite{assembly_wrapping}; its integration
into Zone is assessed as an implementation contribution. These new
directions build on the earlier payload-level study while preserving
its detailed results for comparison.

'''
s=s.replace(r'\section{Conclusions}\label{sec:conclusion3}',related+r'\section{Conclusions}\label{sec:conclusion3}',1)
start=s.index(r'\section{Conclusions}\label{sec:conclusion3}')
end=s.index(r'\begin{credits}',start)
conclusion=r'''\section{Conclusions}\label{sec:conclusion3}
Zone provides a binary-to-binary setting for studying metamorphic
transformation of compact Windows payloads. The original study of
102 inputs and fifteen configurations remains the empirical foundation
of this extended article. Its detection, functionality, size, entropy,
and similarity results expose different effects of rewriting:
lower raw-file malicious-verdict fractions coexist with substantial
variation in functional outcomes and representation overhead.
The PII design and the SGN comparison are retained within the scope
of those published experiments.

The extension develops the code--data limitation identified by that
study into an explicit identification and data-handling layer.
Symbolic and heuristic analysis and an LLM-based alternative feed
deterministic handling of accepted candidates. A separate LLM path
supports assembly transformation with zero-shot and two-shot
conditions, validation, and feedback. Integration of assembly wrapping
adds an existing technique to the engine; its x86 port remains under
development pending architecture-specific assessment.

The additional protocol separates classification quality, construction,
working rate, static verdicts, similarity, diversity, and cost. These
measurements extend rather than replace the original evaluation.
Their interpretation remains tied to the tested inputs, analysis
limits, functional observables, and scan conditions. Complete semantic
equivalence and general endpoint behavior require evidence beyond
those observations.
\draftnote{Add the principal completed extension findings here and in
the abstract. Keep the original findings and update the x86 status only
after its campaign is finalized.}

'''
s=s[:start]+conclusion+s[end:]
(STAGE/'main.tex').write_text(s,encoding='utf-8')

editors='''The SECRYPT 2026 conference paper, "On Automating the Obfuscation of Malware Payloads: Zone, a bin2bin Metamorphic Engine", is the foundation of this extended article. The revised manuscript retains the original engine description, Position-Independent Instruction design, experimental protocol and detailed evaluation on 102 Windows payloads, including detection, working rate, size, entropy, similarity, limitations, and comparison with Shikata Ga Nai. All seven original figures, six tables, four code listings, and the high-level algorithm are retained with source citations. The original publication is cited and included in the bibliography; title, abstract, and conclusions have been revised to cover both the original study and its extensions.

The added material introduces symbolic and heuristic code--data identification, an alternative LLM-based classifier, and shared deterministic data handling; describes LLM-assisted assembly transformation with zero-shot and two-shot conditions, validation, and feedback; and integrates assembly wrapping as an existing technique, with the x86 port currently under development. Separate additional methodology and results sections extend the original assessment with classification quality, construction success, conditional and planned-case working rates, static verdicts, representation similarity, diversity, time, and cost. The published evaluation remains intact and explicitly distinguished from the new campaigns. This is a working revision: new numerical results and x86 wrapping validation are still in progress, and this statement will be finalized with the completed assessment before submission.
'''
(STAGE/'EDITOR_DIFFERENCES.txt').write_text(editors,encoding='utf-8')
readme='''# Revisione CCIS additiva - 13 novembre 2026

Questa versione estende il manoscritto precedente conservandone il corpo scientifico e tutti i risultati dettagliati. Il PDF principale e `main.pdf`.

## Materiale originale mantenuto

`main.tex` conserva background, tecniche, architettura, PII e relativi listing, algoritmo, protocollo originale, detection rate, working rate, dimensione, entropia assembly/byte, cosine similarity, limiti, confronto SGN e related work. Sono presenti tutte le sette figure, sei tabelle, quattro listing e l'algoritmo della bozza originale, con citazione della fonte. I numeri storici non sono stati sostituiti con quelli dei test nuovi.

Titolo, abstract, contributi introduttivi e conclusioni sono aggiornati per descrivere studio originale ed estensione. Il requisito di evitare grandi blocchi copiati dalla conferenza resta da verificare rispetto al testo effettivamente pubblicato: qui la fonte mantenuta e la bozza CCIS preparatoria, non un confronto certificato con il full text della conferenza.

## Nuove sezioni attive

- `sections/extension_code_data.tex`: identificazione simbolica/euristica e LLM, gestione dei dati.
- `sections/extension_llm.tex`: morphing LLM, 0/2 shot, controlli e feedback.
- `sections/extension_wrapping.tex`: integrazione del metodo esistente e x86 in sviluppo.
- `sections/extension_methodology.tex`: metriche e protocollo aggiuntivi.
- `sections/extension_results.tex`: tabelle da completare e commento dei nuovi risultati.

L'ordine preserva prima lo studio originale e aggiunge poi le estensioni motivate dai suoi limiti. I vecchi moduli numerati 01--10 della revisione riorganizzata non sono piu inclusi da main.tex; la copia di quella revisione resta nel backup. Non usarli per modificare questa versione.

## Completamento

1. Inserire dati e interpretazioni dei nuovi esperimenti in `extension_results.tex` e fissare i metadati in `extension_methodology.tex`.
2. Tenere separati studio originale e nuove campagne, specialmente se campioni, harness o versioni differiscono.
3. Aggiornare insieme abstract, conclusioni e i due paragrafi di `EDITOR_DIFFERENCES.txt`.
4. Completare corresponding author e dichiarazione di interessi.
5. Dopo aver risolto tutte le note, impostare `\\workingdraftfalse` in main.tex. Le celle pending vanno completate o dichiarate non disponibili; nascondere le note non le compila.

`BASELINE_CHECKS.md` registra controlli aperti sulle associazioni delle vecchie figure e sulla provenienza della similarita. I risultati non sono stati eliminati per questi controlli. `REVISION_AUDIT.json` documenta la conservazione degli oggetti originali e il nuovo testo indicativo. Il 30% richiede contenuto scientifico sostanziale e non e certificato dal semplice conteggio delle parole; i risultati aggiuntivi sono ancora da completare.

## Compilazione

Eseguire `build.ps1` con PowerShell. Il progetto mantiene la classe LNCS e la bibliografia originale, ampliata con i riferimenti dei nuovi metodi. Gli strumenti e la cache TeX locali sono in `.tools/`.
'''
(STAGE/'README_REVISIONE.md').write_text(readme,encoding='utf-8')
checks='''# Controlli della baseline conservata

Tutti i risultati storici sono ripristinati dalla bozza preparatoria. Questa revisione additiva non cambia silenziosamente dati o percentuali pubblicati.

Prima della submission riconciliare con il PDF della conferenza e gli archivi originali:

- Nei grafici detection/working rate alcune associazioni categoria-valore nella coda delle configurazioni richiedono controllo. Esempio verificato: il LaTeX preparatorio assegna 66,8% a eq_pii x64, mentre test_report.txt da 216/377 = 57,3%; assegna 0,3% a nop_pii, mentre l'archivio da 212/370 = 57,3%. Il valore 1/375 = 0,3% appartiene a nop_bcf. Non trattare il disegno del grafico come verifica del dato.
- results.json contiene 15.021 record e 15.020 percorsi unici: una ripetizione e presente. Dichiarare deduplicazione e denominatore in un'eventuale rianalisi.
- La cosine similarity descritta come distribuzione di opcode va confrontata con lo script effettivamente usato: lo script create_var.py oggi presente tratta anche operandi e aggregazioni di corpus. SequenceMatcher nei test LLM e una metrica separata.
- Se si correggono le figure, identificare esplicitamente correzioni e rianalisi; conservare la distinzione dai test nuovi. Il codice storico e le sorgenti precedenti restano nei backup.

Questi controlli sono indicati anche da una nota blu nel PDF di lavoro. La conservazione dei risultati risponde alla natura di estensione del manoscritto; non ne certifica la correttezza numerica finale.
'''
(STAGE/'BASELINE_CHECKS.md').write_text(checks,encoding='utf-8')

def objects(text,env):
    return re.findall(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}',text,re.S)
retention={}
for env in ['figure','table','lstlisting','algorithm']:
    a=objects(original,env);b=objects(s,env)
    retention[env]={'original_count':len(a),'retained_count':sum(x in b for x in a),'unchanged_objects':all(x in b for x in a)}
    assert retention[env]['unchanged_objects']
newtext='\n'.join(p.read_text() for p in (STAGE/'sections').glob('*.tex'))
def tokens(t):
    for env in ['figure','table','lstlisting','algorithm']:
        t=re.sub(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}','',t,flags=re.S)
    return len(re.findall(r'\b[A-Za-z][A-Za-z-]*\b',t))
audit={'revision':'additive correction; detailed original study retained',
 'basis':'backup_before_extension_20261113/main.tex (CCIS preparation draft)',
 'previous_project_main_sha256':hashlib.sha256((PROJECT/'main.tex').read_bytes()).hexdigest(),
 'retained_objects':retention,'original_prose_tokens_indicative':tokens(original),
 'added_section_tokens_indicative':tokens(newtext),
 'new_material_status':'methods written; numerical campaigns pending; x86 wrapping in development',
 'thirty_percent':'indicative token counts do not certify substantive novelty; finalize with completed new evidence',
 'known_baseline_checks':'BASELINE_CHECKS.md; numerical series preserved unchanged',
 'editor_statement_paragraphs':len([p for p in editors.split('\n\n') if p.strip()])}
(STAGE/'REVISION_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps(audit,indent=2))
