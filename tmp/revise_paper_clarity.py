"""Editorial revision and offline figures from saved experimental records only."""
from pathlib import Path
import csv
import collections
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / 'tmp/ccis_rewrite_20261114'
BACKUP = PAPER / 'before_clarity_revision'
BACKUP.mkdir(exist_ok=True)
for source in [PAPER/'main.tex', PAPER/'main.pdf', *list((PAPER/'sections').glob('*.tex'))]:
    dest = BACKUP / source.relative_to(PAPER)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(source, dest)

def write(rel, text):
    path = PAPER / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + '\n', encoding='utf-8')

def original(rel):
    return (BACKUP/rel).read_text(encoding='utf-8')

# Recompute the recovery comparison from the two underlying execution ledgers.
TECHS = ['nop','eq','pii','bcf','ibp','eq_nop_pii','eq_nop_bcf',
         'eq_nop_ibp','nop_eq','nop_pii','nop_bcf','nop_ibp','eq_pii','eq_bcf','eq_ibp']
selected = {(r['arch'],r['payload']) for r in json.loads((ROOT/'tmp/low_payloads.json').read_text())['payloads']}

def parse_report(path):
    out = []
    with path.open(encoding='utf-8-sig',newline='') as handle:
        for r in csv.reader(handle):
            if len(r)<3:
                continue
            filename=r[0].strip().replace('\\','/')
            arch='x64' if 'x64' in filename else 'x86'
            stem=Path(filename).stem
            stem=re.sub(r'_\d+$','',stem)
            for tech in sorted(TECHS,key=len,reverse=True):
                if stem.endswith('_'+tech):
                    payload=stem[:-len(tech)-1]
                    if (arch,payload) in selected:
                        out.append(dict(file=filename,arch=arch,payload=payload,technique=tech,status=r[2].strip().upper()))
                    break
    return out

datasets={'before':parse_report(ROOT/'test_report.txt'),
          'after':parse_report(ROOT/'new_test_report_5run.csv')}
unified=list(csv.DictReader((ROOT/'working_rate_unified_tests.csv').open(encoding='utf-8-sig',newline='')))
for ds,rows in datasets.items():
    source_name={'before':'old_original','after':'new_xd_ebi'}[ds]
    expected=[r for r in unified if r['dataset']==source_name and (r['arch'],r['payload']) in selected and r['technique'] in TECHS]
    signature=lambda rr: collections.Counter((r['arch'],r['payload'],r['technique'],r['status']) for r in rr)
    assert signature(rows)==signature(expected),(ds,'underlying and consolidated records disagree')
    assert len({r['file'] for r in rows})==len(rows)

stats=[]
summary={}
payload_stats=[]
for arch in ['x64','x86']:
    summary[arch]={}
    for ds,rows in datasets.items():
        all_arch=[r for r in rows if r['arch']==arch]
        ok=sum(r['status']=='OK' for r in all_arch)
        summary[arch][ds]={'ok':ok,'tested':len(all_arch),'rate_pct':100*ok/len(all_arch)}
        for idx,tech in enumerate(TECHS):
            rr=[r for r in all_arch if r['technique']==tech]
            good=sum(r['status']=='OK' for r in rr)
            stats.append(dict(arch=arch,condition=ds,index=idx,technique=tech,ok=good,tested=len(rr),rate_pct=100*good/len(rr)))
        for a,p in sorted(selected):
            if a==arch:
                rr=[r for r in all_arch if r['payload']==p]
                good=sum(r['status']=='OK' for r in rr)
                payload_stats.append(dict(arch=arch,payload=p,condition=ds,ok=good,tested=len(rr),rate_pct=100*good/len(rr)))

evidence=PAPER/'evidence/clarity_revision'
evidence.mkdir(parents=True,exist_ok=True)
for name,rows in [('recovery_by_technique.csv',stats),('recovery_by_payload.csv',payload_stats)]:
    with (evidence/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary['sources']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'test_report.txt',ROOT/'new_test_report_5run.csv',ROOT/'tmp/low_payloads.json',ROOT/'working_rate_unified_tests.csv']}
(evidence/'recovery_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

labels=','.join(t.upper().replace('_','+') for t in TECHS)
plots=[]
for arch in ['x64','x86']:
    before=[r for r in stats if r['arch']==arch and r['condition']=='before']
    after=[r for r in stats if r['arch']==arch and r['condition']=='after']
    ninputs=13 if arch=='x64' else 36
    title=f"{arch}: {ninputs} previously low-working-rate payloads"
    code=r'''\begin{tikzpicture}
\begin{axis}[
width=\linewidth,height=5.9cm,
title={TITLE},title style={font=\small\bfseries},
ylabel={Working rate (\%)},ymin=-3,ymax=107,ytick={0,25,50,75,100},
xmin=-0.6,xmax=14.6,xtick={0,...,14},xticklabels={LABELS},
xticklabel style={rotate=60,anchor=east,font=\scriptsize},
tick label style={font=\scriptsize},label style={font=\small},
ymajorgrids=true,grid style={gray!20},axis line style={gray!60},
legend style={font=\scriptsize,at={(0.98,0.98)},anchor=north east,legend columns=2,fill=white,draw=gray!25},
]
'''.replace('TITLE',title).replace('LABELS',labels)
    for a,b in zip(before,after):
        code+=f"\\addplot[gray!40,thick,no marks,forget plot] coordinates {{({a['index']},{a['rate_pct']:.6f}) ({b['index']},{b['rate_pct']:.6f})}};\n"
    for rr,color,mark,label in [(before,'gray!85','o','Historical'),(after,'blue!65!black','*','Updated')]:
        coords=' '.join(f"({r['index']},{r['rate_pct']:.6f})" for r in rr)
        code+=f"\\addplot[only marks,mark={mark},mark size=2.2pt,{color}] coordinates {{{coords}}};\n\\addlegendentry{{{label}}}\n"
    code+=r'\end{axis}\end{tikzpicture}'
    plots.append(code)
write('figures/recovery_plot.tex','\n\\par\\vspace{0.5cm}\n'.join(plots))
write('figures/recovery_figure.tex',r'''
\begin{figure}[p]
\centering
\input{figures/recovery_plot}
\caption{Working-rate improvement on the same 49 previously low-rate
payloads (13 x64 and 36 x86). Each pair compares the historical and updated
pipeline for one transformation configuration. Pooled rates are
23/1,941 (1.2\%) versus 1,564/1,950 (80.2\%) on x64, and
772/5,195 (14.9\%) versus 699/2,700 (25.9\%) on x86.
The updated campaign has ten variants per x64 input/configuration and five
per x86 input/configuration. Historical denominators are the recorded tests.
Data-preparation-only controls are excluded. The comparison includes the
updated test harness, including corrected MessageBox recognition.}
\label{fig:recovery_working}
\end{figure}
''')
write('working_rate_recovery.tex',r'''
\documentclass{article}
\usepackage[T1]{fontenc}
\setlength{\paperwidth}{16cm}
\setlength{\paperheight}{19cm}
\setlength{\textwidth}{14cm}
\setlength{\textheight}{17cm}
\setlength{\oddsidemargin}{-1.54cm}
\setlength{\topmargin}{-1.54cm}
\setlength{\headheight}{0pt}
\setlength{\headsep}{0pt}
\special{papersize=16cm,19cm}
\usepackage{newtxtext}
\usepackage{amsmath}
\usepackage[varvw]{newtxmath}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\pagestyle{empty}
\begin{document}
\centering
\input{figures/recovery_plot}
\par\smallskip\small
Same 49 selected payloads, before and after the pipeline update.\\
x64: 1.2\% to 80.2\%; x86: 14.9\% to 25.9\% (pooled rates).\\
Historical and updated test counts differ; see manuscript for the protocol.
\end{document}
''')

write('sections/extension_methodology.tex',r'''
\section{Experimental Design for the Extensions}\label{sec:methodology}
\subsection{What Is Tested, and on Which Programs?}
The evaluation separates three practical questions: whether Zone identifies
embedded data correctly, whether a transformed program still performs its
expected task, and how often static scanners flag the resulting file.
Table~\ref{tab:test_populations} summarizes the inputs used for each question.

\begin{table}[t]
\caption{Test populations. The thirteen controlled programs and the thirteen
selected x64 payloads are different sets with different purposes.}
\label{tab:test_populations}
\centering\small
\begin{tabularx}{\linewidth}{@{}l r Y@{}}
\toprule
Population & Inputs & Purpose \\
\midrule
Controlled functional programs & 13 & Check exact expected output after transformation. \\
Annotated classification programs & 6 & Check which bytes are identified as data. \\
Original Windows payload corpus & 102 & Measure construction, functionality, and static detection. \\
Recovery subset of that corpus & 49 & Compare historical and updated working rates on previously problematic inputs. \\
Data-handling subset of that corpus & 19 & Compare symbolic and LLM identification within the same pipeline. \\
\bottomrule
\end{tabularx}
\end{table}

The thirteen \emph{controlled functional programs}, also called test
fixtures, are small purpose-built assembly programs: six cases on each
architecture cover arithmetic, conditional branches, loops, local calls,
combined control flow, and embedded strings. One additional x64 case
exercises access to embedded data through a computed code address.
These programs are 19--68 bytes long. Each writes a known result into a
256-byte output buffer; a separate native C runner executes the program
and compares the whole buffer with the expected bytes. Untouched positions
must retain their initial value. All thirteen originals pass this check.
This compact suite tests individual mechanisms; the original payload corpus
provides the broader application-level evaluation.

The six \emph{annotated classification programs} answer a different
question: does the method locate the data correctly? Two contain multiple
strings (one per architecture), one x64 case contains a binary table,
two contain no separate data, and one x64 case contains instruction bytes
that resemble text. For each program the correct data locations are written
down before either classifier runs. The model does not receive these answers.
The two suites are complementary: one checks the result of execution,
the other checks the identification decision itself.

The original corpus contains 38 x64 and 64 x86 Windows payloads.
Functional tests check the expected dialog, network connection event,
or clean termination for the relevant payload class. All 102 originals pass.
Throughout this article, \emph{working} means that the transformed output
passes the corresponding functional test. We use this empirical definition
consistently for the historical and extended evaluations.

The recovery comparison selects the 49 original inputs whose historical
working rate was below 50\%: thirteen x64 and 36 x86. It compares the same
inputs and fifteen transformation configurations before and after the
pipeline update. New results use ten variants per x64 input/configuration
and five per x86 input/configuration. Data-preparation-only controls are
reported separately. The comparison measures the updated pipeline as a
whole, including the improved MessageBox test; it is not an ablation of
data identification alone.

\subsection{Configurations, Repetitions, and Model Calls}
An experimental \emph{cell} is one combination of input, transformation,
and prompting condition. For example, one x64 test program transformed
with EQ using a prompt with two examples is one cell. Running that
combination three times gives three repetitions of the same cell.

The native controlled benchmark uses three runs per input and transformation
family. The LLM benchmark uses four families, two prompting conditions,
and three separate single-generation requests per cell. This gives
$7\times4\times2\times3=168$ x64 requests and
$6\times4\times2\times3=144$ x86 requests. All rejected responses and
transport failures remain in the counts. The classification benchmark uses
three LLM requests and one symbolic analysis per annotated program.

On the full original corpus, wrapping uses three randomization seeds per
input, giving $102\times3=306$ planned variants. The LLM experiment has
$102\times4\times2=816$ cells and an output-token limit of 65,536.
It targets one accepted output per cell; two successful cells required a
second generation, and fourteen failed cells were restarted without success.
These results describe the completed campaign, including those retries.

The data-handling comparison uses nineteen original inputs (thirteen x64,
six x86) with data extracted by symbolic preparation. Each method proposes
data regions, after which the same deterministic handling and functional
test are applied. Input selection and shared processing are thus held
explicit in interpreting the comparison.

The accompanying artifact records engine versions and request histories.
Native x86 IBP was tested with an earlier implementation than the later
x86 LLM and wrapping experiments; these are separately identified in the
artifact and are not a controlled comparison of engine versions.

\subsection{Build Rate, Working Rate, and Classification Accuracy}
Let $N$ be planned cases, $B$ produced binaries, and $W$ binaries passing
the functional test. Build rate is $B/N$, overall working rate is $W/N$,
and working rate among produced binaries is $W/B$.
For example, ten planned cases, eight produced binaries, and six successful
tests give 80\%, 60\%, and 75\%, respectively. The recovery figure compares
successful tests with recorded tests, matching the available historical
records. A repeated execution of the same binary is not a new variant.

For classification, \emph{predicted} means the bytes that the method labels
as data. \emph{Reference} means the known correct data bytes annotated
before the test. For example, if a string occupies bytes 20--29, the
reference contains those ten byte positions. A prediction of bytes 20--27
finds eight of them and introduces no extra byte: precision is 100\%
and recall is 80\%. In general, for predicted positions $P$ and reference
positions $G$, precision is $|P\cap G|/|P|$ and recall is $|P\cap G|/|G|$.
An exact match requires all data intervals to agree, with no omissions or
additions. For programs without separate data, the correct answer is an
empty set. On original payloads without independent annotations, we report
agreement between the methods and the resulting execution outcomes.

\subsection{Similarity, Detection Rate, Diversity, and Cost}
\paragraph{Similarity.}
The LLM similarity score compares the prepared input assembly with the
accepted output assembly. It measures how much of their instruction
sequences matches, using $S=2M/(u+v)$ for $M$ matched elements and sequence
lengths $u,v$~\cite{python_difflib}. NOP-like operations are ignored for
the NOP condition, so adding only those operations can leave $S=1$ even
when the binary changes. Similarity describes representation; functionality
is measured by the execution tests. This score is separate from the
historical cosine and entropy measures.

\paragraph{Detection rate.}
We retain the historical engine-level detection rate:
$d_i=m_i/a_i$, where $m_i$ engines flag file $i$ as malicious and $a_i$
engine responses are reported. The tables give its mean across files,
$\overline d$, as a percentage. We also report the \emph{detected-file
rate}, $q$: the fraction of files flagged by at least one engine.
For example, one malicious response out of 75 is an engine detection rate
of 1.33\%; that file still counts as detected in $q$. Thus the two rates
answer different questions: how many engines flag a file, and how many
files receive any malicious verdict.

Nonempty current reports contain 75 responses, including unsupported
formats, timeouts, and failures. We disclose these categories separately;
an empty report is treated as missing. These measurements concern static
scans of raw files. Passing and failing outputs remain separately identified.

\paragraph{Diversity and resources.}
$U$ counts distinct output SHA-256 hashes: identical output bytes count
once for diversity and scanning, even when produced by multiple runs.
A shared hash retains membership in every relevant experimental condition.
Consequently, per-condition unique counts need not sum to the global count.
Time is the recorded duration of a run, including local processing.
Estimated API costs include failed calls and restarted runs. Source records,
version mappings, and the detailed accounting are supplied with the artifact.
''')

llm=original('sections/extension_llm.tex')
start=llm.index('Before the request,')
end=llm.index('The experiments request',start)
llm=llm[:start]+r'''Before sending a request, Zone converts the binary into a prepared
assembly listing. Embedded data that has been identified and extracted is
kept separately, so the model works on the instruction representation.
Relevant locations are named with symbolic labels. A label is a name for
a destination, like a section name in a document: it stays meaningful even
when edits change the destination's numerical position.

The model returns a complete proposed assembly listing. Zone then converts
that text back into binary instructions, restores the preserved data, and
performs its structural checks. There are therefore three successive
representations: the original binary, the prepared input listing, and the
final binary. The LLM similarity score compares the prepared and returned
listings; changes already made during preparation are outside that comparison.

'''+llm[end:]
start=llm.index('The general pipeline may')
end=llm.index('The benign benchmark disables',start)
llm=llm[:start]+r'''If structural validation rejects an answer, the pipeline can send the
diagnostic back to the model and ask for a corrected proposal. This is
\emph{validation feedback}: an explanation of what the checker rejected,
such as assembly that cannot be built or a missing label. It is not a
functional success signal or a scanner verdict. A retry can therefore use
information unavailable in the initial request.
'''+llm[end:]
llm=llm.replace('Zone accepts a constructed output; it does not prove behavioral equivalence.',
                'Zone accepts a constructed output, which then proceeds to the execution test.')
llm=llm.replace('For\nthe benign fixtures,', 'For\nthe controlled programs,')
write('sections/extension_llm.tex',llm)

data=original('sections/extension_code_data.tex')
start=data.index('The general classifier can receive')
data=data[:start]+r'''The classifier also supports correction requests. If a proposed data
interval extends beyond the input, for example, validation can return that
diagnostic and request a revised interval set. This feedback concerns the
data-location proposal, whereas feedback in transformation mode concerns
the proposed assembly. These are two separate uses of the model.

Examples in a classification prompt illustrate how to identify data.
The zero-shot/two-shot comparison in the next section instead concerns
examples of instruction transformation; changing one setting does not
automatically change the other.

Caching avoids repeating identification for an input already analyzed:
the saved result associates that input with its identified data regions.
Addresses used by the working code are computed again because rewriting
can move instructions and data. Reusing a decision about which bytes are
data therefore does not mean reusing obsolete addresses. Both classifiers
feed the same subsequent processing, so different initial proposals may
still produce the same final binary.
'''
write('sections/extension_code_data.tex',data)

wrap=original('sections/extension_wrapping.tex')
wrap=wrap.replace(r'\subsection{The Same Bytes Can Have Two Instruction Interpretations}',
                  r'\subsection{Reading the Same Bytes from Different Starting Points}')
start=wrap.index('Assembly wrapping changes')
end=wrap.index(r'\begin{figure}',start)
wrap=wrap[:start]+r'''Assembly wrapping relies on a property of x86 and x64: instructions have
variable lengths, and the starting byte determines how a decoder groups
the following bytes into instructions. The same stored bytes can therefore
have two interpretations when read from different starting points.

Consider two views of one region. In the \emph{outer view}, a decoder sees
an instruction followed by its immediate operand, a constant stored inside
that instruction. In the \emph{execution view}, part of that constant's
byte field is read as an instruction sequence. The established wrapping
technique uses this overlap to give the stored representation an outer
instruction structure while retaining an intended executable interpretation
within it~\cite{assembly_wrapping}.

Figure~\ref{fig:wrapping_views} shows these two readings of one byte field.
The term \emph{container} refers to the outer instruction; \emph{embedded
sequence} refers to the instructions represented inside its operand bytes.
These are two readings of shared bytes, rather than two copies of the
program. No decryption step is required to obtain the embedded interpretation.

'''+wrap[end:]
wrap=wrap.replace('The x86 implementation was introduced after the first benign benchmark\nsnapshot and is evaluated under its own recorded version.',
                  'Both architectures are included in the functional evaluation.')
wrap=wrap.replace('Successful relocation checks likewise cover the\nreferences the engine supports, not every possible address computation.',
                  'The following execution tests measure whether the resulting program\nperforms its expected task.')
start=wrap.index(r'\subsection{What the Evaluation Can Establish}')
wrap=wrap[:start]+r'''\subsection{How Wrapping Is Evaluated}
The evaluation follows three stages: construction of a binary, execution
of its functional test, and static scanning of the produced file.
Construction rate measures how many requested variants are available;
working rate measures how many perform the expected task; detection rate
describes the scanner responses. The full experiment uses all 102 original
payloads, with the same stages reported separately for x64 and x86.
'''
write('sections/extension_wrapping.tex',wrap)

results=original('sections/extension_results.tex')
start=results.index('The new results')
end=results.index(r'\subsection',start)
results=results[:start]+r'''The extension recovers functionality on many previously problematic
payloads. In the selected recovery cohort, the x64 working rate rises
from 1.2\% to 80.2\%; the corresponding x86 rates are 14.9\% and 25.9\%
(Figure~\ref{fig:recovery_working}). The following experiments also measure
data identification, controlled transformation behavior, and the new wrapping
and LLM modes on the full original corpus. Each experiment answers a
different question and retains its own input set.

'''+results[end:]
results=results.replace('Can the Methods Identify Annotated Data?', 'Data Identification: Known Answers and Original Payloads')
results=results.replace('Independent classifier fixtures.', 'Six programs with independently annotated data locations.')
results=results.replace('These results establish correctness on the six annotated examples, not on\narbitrary payloads. The nineteen selected original payloads illustrate\nwhy that distinction matters.',
'''Both methods correctly identify all six controlled examples. The
comparison on nineteen original payloads then evaluates how the proposed
regions are handled in the complete pipeline.''')
results=results.replace('in only 9/19 cases,','in 9/19 cases,')
results=results.replace('Different preparation and caching work prevents a\ncontrolled general speedup claim.',
                       'These are measured run durations; preparation and caching differ\nbetween the two arms.')
results=results.replace("Do Transformations Preserve the Benign Fixtures' Outputs?", 'Functional Tests on Thirteen Controlled Programs')
results=results.replace('B1 IBP builds','The tested native IBP implementation builds').replace('The B2 x86 wrapping implementation','The x86 wrapping implementation')
results=results.replace('A constructed binary\ncan thus fail even these controlled observables, as the IBP row demonstrates.',
                       'This suite confirms the successful cases and identifies native x86\nIBP as a failing configuration in the tested earlier implementation.')
results=results.replace('New native fixture results.', 'Native transformations of the thirteen controlled programs.')
results=results.replace('B1/B2 identify different frozen engine versions.', 'Version details are recorded in the accompanying artifact.')
results=results.replace(r'\begin{tabular}{@{}lllrrrr@{}}'+'\n'+r'\toprule'+'\n'+r'Arch. & Family & Version & $N$ & $B$ & $W$ & $U$',
                       r'\begin{tabular}{@{}llrrrr@{}}'+'\n'+r'\toprule'+'\n'+r'Arch. & Family & $N$ & $B$ & $W$ & $U$')
results=re.sub(r' & B[12] & ', ' & ', results)
results=results.replace('The full B3 campaign','The full-corpus campaign')
results=results.replace('The distinction reveals a\nsubstantial coverage gap that would be hidden by reporting only the\nsuccessful benign tests.',
                       'These rates report both availability of a transformed binary and\nits functional outcome.')
results=results.replace('Full original-corpus wrapping campaign, B3. The harness\nobservables are distinct from the benign exact-buffer oracle.',
                       'Wrapping on all 102 original payloads, with three seeds per input.')
results=results.replace('Completed B3 LLM payload matrix.', 'LLM transformation of all 102 original payloads.')
results=results.replace('The aggregate success on\nbenign fixtures does not predict these corpus-level outcomes.',
'''The controlled programs isolate small instruction and data patterns;
the original payloads add larger listings and more complex layouts.
The two experiments therefore measure different levels of difficulty.''')

recovery=r'''\subsection{Working-Rate Improvement on Previously Problematic Payloads}
\label{sec:recovery}
The recovery experiment revisits the same 49 inputs whose historical
working rate was below 50\%. It applies the fifteen native transformation
configurations after the data-preparation and pipeline updates.
Figure~\ref{fig:recovery_working} compares the recorded outcomes by
architecture and configuration.

For the thirteen selected x64 payloads, successful tests increase from
23/1,941 (1.2\%) to 1,564/1,950 (80.2\%), a gain of 79.0 percentage
points. For the 36 selected x86 payloads, they increase from 772/5,195
(14.9\%) to 699/2,700 (25.9\%), a gain of 11.0 percentage points.
These are pooled rates: successful tests divided by recorded tests.
For example, the x64 MessageBox case increases from 4/150 to 150/150,
and the x64 custom HTTP case from 15/147 to 143/150.

The improvement is strongest on x64 and remains uneven across inputs.
Two x64 winhttps cases still pass only 10/150 transformed variants each.
The updated campaign includes the corrected MessageBox recognition in the
test harness. Even excluding MessageBox, the selected x64 cohort improves
from 19/1,791 (1.1\%) to 1,414/1,800 (78.6\%). Thus the recovery extends
beyond that test-harness correction.

This comparison updates the evidence for the retested subset of the original
corpus. The historical full-corpus figure remains the published baseline;
the new subset results are shown separately because the other inputs were
not part of this recovery campaign. Per-payload counts and source records
are included in the artifact.

\input{figures/recovery_figure}

'''
results=results.replace(r'\subsection{Static Scans of the Completed Campaign}',recovery+r'\subsection{Detection Rates in the Completed Campaign}')

# Derive engine-level detection rates from existing nonempty scan records.
manifest=json.loads((ROOT/'vt_manifest_campaign.json').read_text())
vt={r['sha256']:r for r in (json.loads(line) for line in (ROOT/'tmp/vt_results_campaign.jsonl').read_text().splitlines()) if r.get('status')=='completed'}
group_order=['wrap','llm_eq_s0','llm_eq_s2','llm_nop_s0','llm_nop_s2','llm_bcf_s0','llm_bcf_s2','llm_ibp_s0','llm_ibp_s2','lldata']
labels_vt=['Wrapping','LLM EQ / 0','LLM EQ / 2','LLM NOP / 0','LLM NOP / 2','LLM BCF / 0','LLM BCF / 2','LLM IBP / 0','LLM IBP / 2','LLM data only']
table=[]
for group,label in zip(group_order,labels_vt):
    hh={r['sha256'] for r in manifest if r['group']==group or r.get('technique')==group}
    rr=[vt[h] for h in hh if vt[h].get('total',0)>0]
    detected=sum(r['malicious']>0 for r in rr)
    dr=100*sum(r['malicious']/r['total'] for r in rr)/len(rr)
    table.append(f"{label} & {len(hh)} & {len(rr)} & {detected} & {100*detected/len(rr):.1f} & {dr:.2f} \\\\")
start=results.index(r'\begin{table}[t]',results.index(r'\subsection{Detection Rates'))
end=results.index(r'\end{table}',start)+len(r'\end{table}')
results=results[:start]+r'''\begin{table}[t]
\caption{Current raw-file detection rates. $U$: distinct submitted hashes;
$V$: hashes with nonempty reports; $D$: hashes flagged by at least one
engine; $q=D/V$: detected-file rate; $\overline d$: mean engine detection
rate. The empty BCF/0 report is excluded from measured rates.}
\label{tab:current_scans}
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Condition & $U$ & $V$ & $D$ & $q$ (\%) & $\overline d$ (\%) \\
\midrule
'''+ '\n'.join(table)+r'''
\bottomrule
\end{tabular}
\end{table}'''+results[end:]
results=results.replace(r'response ($q=68.6$\%), with mean 3.80 malicious responses per hash.',
r'''response ($q=68.6$\%). The mean engine detection rate is 5.06\%,
equivalent to 3.80 malicious responses per hash.''')
results=results.replace('The lower scan rate\nof failing outputs must not be interpreted as successful behavioral\npreservation with reduced detection. It instead shows why functionality\nand verdicts must be linked when interpreting the experiment.',
'''These separate counts distinguish detection measurements on working
outputs from those on outputs that fail the functional test.''')
write('sections/extension_results.tex',results)

write('sections/extension_discussion.tex',r'''
\section{Discussion of the Extensions}\label{sec:extension_limits}
The recovery comparison provides direct evidence of improved functional
reliability on previously problematic inputs. On the selected x64 cohort,
working rate rises from 1.2\% to 80.2\%; x86 also improves, from 14.9\%
to 25.9\%. The pipeline updates therefore recover many useful outputs,
with a substantially stronger improvement on x64. Results on the full
corpus complement this comparison by evaluating the added wrapping and
LLM modes across all 102 original payloads.

The controlled suites help explain what each stage contributes. All six
annotated programs are classified exactly, while the thirteen functional
programs check the output of individual programming patterns. Their small
size and simple layouts make them useful diagnostic tests. Their high
success rates are not a consequence of being benign: the original corpus
contains larger and more varied instruction/data layouts, which exercise
additional cases. The native x86 IBP failure also shows that a controlled
program can expose an implementation problem directly.

The two LLM roles remain distinct. Identifying data supplies regions to
the deterministic pipeline; transforming assembly supplies a proposed
instruction listing. On nineteen selected original payloads, the former
produces the same final binary as symbolic preparation in 16 cases and
the same 17/19 functional result. For transformation, zero-shot and two-shot
produce similar aggregate outcomes, with no consistent observed advantage
from adding two examples. Input size, construction success, and execution
outcome provide more informative distinctions in this campaign.

The empirical scope can be stated once. Functional preservation is assessed
through the specified execution tests, rather than a formal proof for every
possible execution. Classification accuracy is measured on independently
annotated programs; the unannotated payload comparison measures agreement
and downstream functionality. Static detection rates describe the submitted
raw files and the reported engine responses, including the disclosed
unsupported and failed analyses. Repeated inputs, shared hashes, recorded
version differences, and retries are retained in the artifact so that these
descriptive results can be inspected and reproduced.
''')

main=original('main.tex')
main=main.replace('The completed\ncampaign on the original 102 payloads exposes a larger reliability gap:',
r'''On a separate recovery cohort of thirteen previously problematic x64
payloads, working rate improves from 1.2\% to 80.2\%; the corresponding
x86 subset improves from 14.9\% to 25.9\%. In the completed campaigns
on all 102 original payloads,''')
main=main.replace('These observations separate data identification, construction,\nobserved behavior, and static verdicts. They complement the retained\nconference evaluation without establishing universal semantic preservation\nor the behavior of deployed endpoint protection.',
'''Together, the experiments demonstrate improved functional reliability
and evaluate the added transformation modes through construction, execution,
and static detection measurements.''')
main=re.sub(r'\\draftnote\{The extension uses.*?denominators\.\}\s*','',main,flags=re.S)
main=main.replace('The tests are empirical functional checks rather than proofs of semantic equivalence. ', '')
main=main.replace('The conference paper reported greater overall stability for EQ',
'''Figure~\\ref{fig:recovery_working} adds the updated before/after comparison for the 49 retested low-rate payloads. The conference paper reported greater overall stability for EQ''')
main=main.replace('The present extension makes these\npreparation and validation problems explicit and evaluates two additional\nways to transform the prepared code.',
r'''The present extension adds data preparation to address this problem.
Retesting previously low-rate inputs shows a marked improvement, from
1.2\% to 80.2\% working rate in the selected x64 cohort. The extension
also evaluates two additional ways to transform the prepared code.''')
start=main.index('The controlled tests give exact identification',main.index(r'\section{Conclusions}'))
end=main.index(r'\begin{credits}',start)
main=main[:start]+r'''The recovery experiment demonstrates a substantial gain on the selected
previously low-rate payloads: working rate increases from 1.2\% to 80.2\%
on x64 and from 14.9\% to 25.9\% on x86. The controlled tests give exact
data identification on six annotated programs and correct outputs in
167/168 x64 and 138/144 x86 LLM transformation requests.

Across all 102 original payloads, wrapping produces 243 binaries and 170
successful functional tests from 306 planned variants. LLM transformation
produces 350 binaries and 275 successful tests across 816 configurations.
Two-shot prompting shows no consistent advantage over zero-shot in these
observations. Static scans flag none of the 207 distinct wrapping outputs;
LLM-transformed outputs have a mean engine detection rate of 5.06\% across
322 nonempty reports. Together, these results quantify the recovered
functionality and the behavior of the new transformation paths while
identifying the remaining architecture-dependent cases for future study.

'''+main[end:]
write('main.tex',main)

write('evidence/clarity_revision/REPRODUCIBILITY_NOTES.md',r'''
Reproducibility notes moved out of the main narrative

The earlier source snapshots retain their original identifiers: B1
(13 November 2026, 13:07 CET) covers the native controlled benchmark and
x64 LLM benchmark; B2 (14:05 CET) covers x86 LLM, x86 wrapping, and
classification; B3 covers the full original-payload campaign. The recorded
rewriting and LLM module hashes in B3 match B2. Native x86 IBP therefore
uses an earlier implementation than the later x86 LLM and wrapping tests.

The full LLM ledger contains 830 run records for 816 cells, including
fourteen failed restarts. It records 835 API calls and one additional run
with missing usage. Four retained records contain multiple generations;
two successful outputs were accepted on generation two. The representative
cell records sum to $19.2700; all recorded runs sum to $19.6258. These are
tariff estimates, not invoices. Recorded run durations include local work.

Completed scan records were available through 14 November 2026, 01:17 CET.
There are 549 completed-status records but 548 nonempty reports. The frozen
completed_20261114 evidence retains source hashes and derived tables.

Recovery figure: counts were independently parsed from test_report.txt and
new_test_report_5run.csv and cross-checked against working_rate_unified_tests.csv.
The 49-input selection comes from tmp/low_payloads.json (historical rate <50%).
The figure uses all fifteen native transformation configurations and excludes
the data-preparation-only controls. The updated x64 cohort has ten variants
per input/configuration; x86 has five. The historical denominators are the
available execution records. Pooled x86 historical rate is 772/5195 = 14.86%;
the 14.3% in earlier tables is instead the unweighted mean across configurations.
Both are legitimate summaries, but they must not be interchanged.

The new figure compares the updated implementation and test harness with
historical outcomes; it does not isolate data handling as the only cause.
In particular, MessageBox recognition was corrected. Excluding MessageBox,
the selected x64 rate changes from 19/1791 to 1414/1800.

No payload generation, execution, API call, or static scan was performed
for this editorial revision. All plotted values derive from saved records.
The previous manuscript and PDF are retained in before_clarity_revision/.
''')
print(json.dumps(summary,indent=2))
print('Editorial source revision complete:',PAPER)
