from pathlib import Path
import re,json
root=Path(r'C:\Users\ubu\Desktop\Zone\tmp\ccis_rewrite_20261114')
p=root/'main.tex'; s=p.read_text(encoding='utf-8')
s=s.replace('% Updated with completed benign and wrapping results; payload LLM/scans remain in progress.','% Revised explanations and completed payload campaign evidence, 14 November 2026.')
s=s.replace(r'\title{Zone: Extending a bin2bin Metamorphic Engine with Code--Data Identification and LLM Assistance}',r'\title{Zone: Code--Data Identification, LLM-Assisted Transformation, and Assembly Wrapping for Binary Rewriting}')
abstract=r'''\begin{abstract}
Rewriting a raw binary requires distinguishing instructions from embedded
data and preserving their references when the layout changes. Zone is a
binary-to-binary metamorphic engine for compact Windows x86 and x64
payloads. This extended study adds symbolic/heuristic and LLM-based data
identification, LLM-proposed instruction transformations, and integration
of assembly wrapping, an existing technique that gives stored bytes
different static and executed instruction interpretations. Six annotated
benign fixtures are identified exactly in 18 LLM and six symbolic runs.
On thirteen separate benign fixtures, LLM transformation yields correct
output buffers in 167/168 x64 and 138/144 x86 invocations. The completed
campaign on the original 102 payloads exposes a larger reliability gap:
wrapping constructs 243/306 variants, with 170 passing the functional
harness; LLM transformation constructs 350 outputs across 816 conditions,
with 275 passing. Current raw-file scans report no malicious verdicts for
207 distinct wrapping outputs and at least one malicious verdict for
221 of 322 evaluable LLM-transformed outputs; one additional LLM report
is empty. These observations separate data identification, construction,
observed behavior, and static verdicts. They complement the retained
conference evaluation without establishing universal semantic preservation
or the behavior of deployed endpoint protection.
\keywords{Binary Rewriting \and Metamorphic Code \and
Code--Data Identification \and Large Language Models \and Functional Preservation}
\end{abstract}'''
s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:abstract,s,count=1,flags=re.S)
s=re.sub(r'\\draftnote\{Results are frozen.*?cutoff\.\}',lambda m:r'''\draftnote{The extension uses the completed campaign logs available on
14 November 2026. The current manifest has 549 completed scan records;
548 contain engine responses and one is empty. Earlier experiments retain
their own versions and denominators.}''',s,count=1,flags=re.S)
start=s.index(r'\paragraph{Relationship to the Conference Paper and Extensions.}')
end=s.index('The scope is restricted',start)
intro=r'''\paragraph{Motivation and Contributions of the Extension.}
The conference study~\cite{zone_secrypt_2026} showed that changes to a
payload's representation can be accompanied by loss of functionality.
One concrete difficulty is embedded data: a disassembler may read a string
as instructions, after which a transformation changes the string instead
of code. Even when the bytes are preserved, moving them can invalidate
the instructions that refer to them. The present extension makes these
preparation and validation problems explicit and evaluates two additional
ways to transform the prepared code.

The contributions are:
\begin{itemize}
\item A data-preparation layer with alternative symbolic/heuristic and
LLM classifiers. It identifies candidate data regions and uses shared
deterministic handling to preserve supported data and references.
\item An LLM transformation path for EQ, NOP, BCF, and IBP, comparing
requests without examples and with two worked examples. Generated
assembly is checked before a separate functional assessment.
\item Integration of assembly wrapping for x64 and x86. This existing
technique changes instruction boundaries so that a static listing and
execution can interpret the same stored bytes differently.
\item A completed evaluation on annotated benign fixtures and the
original 102-payload corpus, reporting classification, build availability,
functional outcomes, static scans, output diversity, and recorded cost.
\end{itemize}

The article retains the original architecture, PII design, detailed
conference results, and comparison with Shikata Ga Nai as its foundation.
Reused figures, tables, listings, and the algorithm carry source citations.
The added methods and experiments are identified separately, making clear
which claims come from the conference study and which are supported by
the completed extension.

'''
s=s[:start]+intro+s[end:]
s=s.replace('and~\\ref{sec:extended_results} define and reserve the extended\nassessment. Section~\\ref{sect:related_work} discusses related work and\nSection~\\ref{sec:conclusion3} concludes.','and~\\ref{sec:extended_results} describe its design and completed results.\nSection~\\ref{sec:extension_limits} interprets their limitations,\nSection~\\ref{sect:related_work} discusses related work, and\nSection~\\ref{sec:conclusion3} concludes.')
s=s.replace(r'\input{sections/extension_results}',r'\input{sections/extension_results}'+'\n'+r'\input{sections/extension_discussion}')
start=s.index(r'\section{Conclusions}\label{sec:conclusion3}')
end=s.index(r'\begin{credits}',start)
s=s[:start]+r'''\section{Conclusions}\label{sec:conclusion3}
The extended Zone pipeline makes data identification and supported
reference handling explicit before instruction transformation. It offers
two distinct LLM roles---proposing data regions and proposing rewritten
assembly---and integrates assembly wrapping for both x64 and x86.
The original PII design and conference experiments remain the foundation
of this broader assessment.

The controlled tests give exact identification on six annotated fixtures
and correct buffers in 167/168 x64 and 138/144 x86 LLM invocations.
The completed original-corpus campaigns show the limits of extending
those results: wrapping passes 170/306 planned cases, while LLM
transformation passes 275/816 cells. Construction and execution failures
contribute differently across architectures. Two-shot prompting does not
show a consistent advantage over zero-shot in the observed outcomes.

None of the 207 submitted wrapping hashes receives a malicious verdict
in the current raw-file scans. For LLM transformation, 221/322 evaluable
hashes do, with one further empty scan report. Relating these measurements
to functionality is essential: LLM outputs that fail the harness have
substantially lower static detection than those that pass. The resulting
evidence supports separate assessment of classification, construction,
behavior, and representation; a favorable result at one stage cannot
stand in for success at the others.

''' + s[end:]
p.write_text(s,encoding='utf-8')
readme='''# Revisione del 14 novembre 2026

Le sezioni nuove sono state riscritte integralmente per spiegare il problema,
la tecnica, gli ingressi/uscite e poi la valutazione. La baseline storica e i
suoi oggetti LaTeX sono conservati. Sono aggiornati anche titolo, abstract,
contributi, organizzazione del paper e conclusioni.

## Contenuti

- Identificazione codice/dati: definizioni, esempio benigno, due classificatori
  alternativi, distinzione fra proposta, accettazione e gestione dei riferimenti.
- Trasformazione LLM: ruolo del modello distinto dalla classificazione; listing
  preparato, zero/two-shot, validazione e test esterno.
- Wrapping: spiegazione del meccanismo e delle due interpretazioni degli stessi
  byte, figura concettuale, integrazione x64/x86 e limiti.
- Metodologia, risultati e discussione riscritti; nuovo schema del flusso.
- Risultati completi: 816 celle LLM, 350 build, 275 test superati;
  wrapping 243/306 build e 170 test superati; scansioni correnti completate.

## Correzioni rispetto al riepilogo della campagna

L'audit diretto dei log trova 830 record di esecuzione per 816 celle, con
14 riprese di celle fallite (ancora fallite), 4 record con generazioni multiple,
835 chiamate API registrate e un record privo di usage. Due build accettati
hanno richiesto una seconda generazione. Non e quindi un esperimento uniforme
al primo tentativo. Il costo registrato completo e $19.6258; $19.2700 e il
sottoinsieme di un record rappresentativo per cella.

Il manifest VT ha 612 file e 549 hash con record completed, ma un report LLM
BCF/0 ha tutte le statistiche a zero. Le scansioni valutabili sono 548, di cui
322 LLM: 221/322 rilevati (68.6%), non 221/323 negativizzando il report vuoto.
Il wrapping ha 0/207 hash con risposte malicious. Le risposte unsupported,
timeout e failure rimangono esplicite. I 75 file LLM non funzionanti
corrispondono a 60 hash distinti (59 con report valutabile).

## Provenienza e riproducibilita

L'evidenza precedente rimane in evidence/. La nuova fotografia immutabile e
in evidence/completed_20261114/, con SOURCES.json, SUMMARY.json, CSV derivati
e copie dei log e dei sorgenti pertinenti. Le statistiche si ricavano da file
esistenti: nessuna generazione, esecuzione di payload o scansione e stata
avviata per questa revisione. La verifica di compilazione e impaginazione e
registrata in REVISION_AUDIT.json.

Per ricompilare: eseguire build.ps1 nella cartella CCIS.

Restano le verifiche storiche documentate in BASELINE_CHECKS.md e i campi
autoriali da completare prima della submission, inclusa la disclosure degli
interessi. Non sono stati inventati dati o dichiarazioni degli autori.
'''
(root/'README_REVISIONE.md').write_text(readme,encoding='utf-8')
(root/'EDITOR_DIFFERENCES.txt').write_text('''The extended manuscript retains the original architecture, PII design, detailed conference evaluation, figures, tables, listings, algorithm, and SGN comparison, with source attribution. The new sections have been rewritten around explicit problem statements, definitions, inputs and outputs, method explanations, and interpretation of evidence. Two conceptual figures explain the extended pipeline and the distinct instruction interpretations underlying assembly wrapping, which is attributed as an existing technique.

The completed extension includes thirteen benign functional fixtures, six independently annotated classification fixtures, wrapping across all 102 original payloads, a completed 816-cell LLM transformation matrix, and the nineteen-payload data-handling comparison. The current scan manifest has 549 completed records, of which 548 are nonempty and evaluable. Results distinguish planned cases, built outputs, passing executions, and distinct hashes. An audit exposes nonuniform retry histories and includes restarted failed runs in cost accounting. Earlier pilot and scan cohorts remain separate. Abstract, introductory contributions, conclusions, and discussion now reflect the completed results and the limited observables actually measured.
''',encoding='utf-8')
print('Updated main manuscript and revision notes')
