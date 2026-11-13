import csv, collections, json
from string import Template

ORDER = ["nop","eq","pii","bcf","ibp","eq_nop_pii","eq_nop_bcf","eq_nop_ibp",
         "nop_eq","eq_bcf","eq_ibp","eq_pii","nop_bcf","nop_ibp","nop_pii"]
LABELS = ["nop","eq","pii","bcf","ibp",
          r"eq\_nop\_pii", r"eq\_nop\_bcf", r"eq\_nop\_ibp",
          r"nop\_eq", r"eq\_bcf", r"eq\_ibp", r"eq\_pii",
          r"nop\_bcf", r"nop\_ibp", r"nop\_pii"]

low = json.load(open("tmp/low_payloads.json", encoding="utf-8"))["payloads"]
low_keys = {(r["arch"], r["payload"]) for r in low}

def load(dataset):
    stats = collections.defaultdict(lambda: [0, 0])
    for r in csv.DictReader(open("working_rate_unified_tests.csv", encoding="utf-8")):
        if r["dataset"] != dataset:
            continue
        key = (r["arch"], r["payload"], r["technique"])
        stats[key][1] += 1
        if r["status"] == "OK":
            stats[key][0] += 1
    return stats

new = load("new_xd_ebi")
old = load("old_original")

def rate(stats, arch, tech):
    ok = tot = 0
    for (a, b, t), v in stats.items():
        if a == arch and t == tech and (a, b) in low_keys:
            ok += v[0]
            tot += v[1]
    return (ok / tot * 100 if tot else 0.0), ok, tot

def series(stats, arch):
    return [rate(stats, arch, t) for t in ORDER]

def avg(vals):
    return sum(v[0] for v in vals) / len(vals)

def coords(vals):
    return " ".join(f"({i},{v[0]:.1f})" for i, v in enumerate(vals))

def nodes(vals, color, pos):
    out = []
    for i, v in enumerate(vals):
        out.append(f"\\node at (axis cs:{i},{v[0]:.1f}) [{pos}, {color}, font=\\tiny] "
                   f"{{{v[0]:.1f}\\%}};")
    return "\n".join(out)

x64_new = series(new, "x64")
x86_new = series(new, "x86")
x64_old = series(old, "x64")
x86_old = series(old, "x86")
a64n, a86n = avg(x64_new), avg(x86_new)
a64o, a86o = avg(x64_old), avg(x86_old)

common = {
    "labels": ", ".join(LABELS),
    "a64n": f"{a64n:.1f}", "a86n": f"{a86n:.1f}",
    "a64o": f"{a64o:.1f}", "a86o": f"{a86o:.1f}",
    "c64n": coords(x64_new), "c86n": coords(x86_new),
    "c64o": coords(x64_old), "c86o": coords(x86_old),
    "n64": nodes(x64_new, "orange", "above"),
    "n86": nodes(x86_new, "blue", "below"),
}

NEW = Template(r"""\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{axis}[
    width=\linewidth,
    height=0.7\linewidth,
    ylabel={Working rate (\%)},
    ymin=0, ymax=110,
    ytick={0,20,40,60,80,100},
    xtick={0,...,14},
    xticklabels={$labels},
    xticklabel style={rotate=45, anchor=east, font=\scriptsize},
    legend pos=north east,
    legend style={
        at={(1.02,1)},
        anchor=north west,
        font=\small,
        fill=white,
        fill opacity=0.85,
        draw opacity=1,
        text opacity=1
    },
    grid=major,
    grid style={dashed, gray!30},
    ymajorgrids=true,
    clip=false,
]

% Averages (unweighted mean over the 15 techniques)
\addplot[orange, dashed, thick, no marks, forget plot] coordinates {(0,$a64n) (14,$a64n)};
\addplot[blue!60, dashed, thick, no marks, forget plot] coordinates {(0,$a86n) (14,$a86n)};

% x64, new run (-xd -ebi + technique)
\addplot[only marks, mark=*, mark size=2pt, orange,
         mark options={fill=orange!25, draw=orange}]
    coordinates {$c64n};
\addlegendentry{x64 (new, 13 payload low)}
\addlegendimage{orange, dashed, thick}
\addlegendentry{x64 avg $a64n\%}

% x86, new run
\addplot[only marks, mark=*, mark size=2pt, blue,
         mark options={fill=blue!20, draw=blue}]
    coordinates {$c86n};
\addlegendentry{x86 (new, 36 payload low)}
\addlegendimage{blue!60, dashed, thick}
\addlegendentry{x86 avg $a86n\%}

$n64
$n86
\end{axis}
\end{tikzpicture}
\caption{Working rate by technique after regeneration with \texttt{-xd -ebi} on the
49 low-rate payloads (13 x64, 36 x86). x64: 10 runs per configuration; x86: 5 runs
per configuration. Dashed lines are the unweighted means over the 15 techniques.
Extraction only (no morphing) gives 100.0\% on x64 and 94.4\% on x86.}
\label{fig:working_rate_new}
\end{figure}
""")

OLD = Template(r"""\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{axis}[
    width=\linewidth,
    height=0.7\linewidth,
    ylabel={Working rate (\%)},
    ymin=0, ymax=110,
    ytick={0,20,40,60,80,100},
    xtick={0,...,14},
    xticklabels={$labels},
    xticklabel style={rotate=45, anchor=east, font=\scriptsize},
    legend pos=north east,
    legend style={
        at={(1.02,1)},
        anchor=north west,
        font=\small,
        fill=white,
        fill opacity=0.85,
        draw opacity=1,
        text opacity=1
    },
    grid=major,
    grid style={dashed, gray!30},
    ymajorgrids=true,
    clip=false,
]

% Old averages
\addplot[orange!60, dotted, thick, no marks, forget plot] coordinates {(0,$a64o) (14,$a64o)};
\addplot[blue!40, dotted, thick, no marks, forget plot] coordinates {(0,$a86o) (14,$a86o)};
% New averages
\addplot[orange, dashed, thick, no marks, forget plot] coordinates {(0,$a64n) (14,$a64n)};
\addplot[blue!60, dashed, thick, no marks, forget plot] coordinates {(0,$a86n) (14,$a86n)};

% x64 old (no flags)
\addplot[only marks, mark=o, mark size=2.2pt, orange!70,
         mark options={fill=white, draw=orange!70}]
    coordinates {$c64o};
\addlegendentry{x64 old (no flags)}
% x64 new
\addplot[only marks, mark=*, mark size=2pt, orange,
         mark options={fill=orange!25, draw=orange}]
    coordinates {$c64n};
\addlegendentry{x64 new (\texttt{-xd -ebi})}
% x86 old
\addplot[only marks, mark=o, mark size=2.2pt, blue!60,
         mark options={fill=white, draw=blue!60}]
    coordinates {$c86o};
\addlegendentry{x86 old (no flags)}
% x86 new
\addplot[only marks, mark=*, mark size=2pt, blue,
         mark options={fill=blue!20, draw=blue}]
    coordinates {$c86n};
\addlegendentry{x86 new (\texttt{-xd -ebi})}

\addlegendimage{orange!60, dotted, thick}
\addlegendentry{x64 old avg $a64o\%}
\addlegendimage{orange, dashed, thick}
\addlegendentry{x64 new avg $a64n\%}
\addlegendimage{blue!40, dotted, thick}
\addlegendentry{x86 old avg $a86o\%}
\addlegendimage{blue!60, dashed, thick}
\addlegendentry{x86 new avg $a86n\%}

$n64
$n86
\end{axis}
\end{tikzpicture}
\caption{Old vs new working rate on the same 49 low-rate payloads (13 x64, 36 x86).
Old is the original \texttt{test\_report.txt} (no flags); new is \texttt{-xd -ebi}
plus each of the 15 technique configurations. Labels show the new values; dotted
lines are old unweighted means, dashed lines new unweighted means.
Extraction only (no morphing) gives 100.0\% on x64 and 94.4\% on x86.}
\label{fig:working_rate_old_vs_new}
\end{figure}
""")

open("working_rate_updated_snippet.tex", "w", encoding="utf-8").write(NEW.substitute(common))
open("working_rate_old_vs_new_snippet.tex", "w", encoding="utf-8").write(OLD.substitute(common))

standalone_pre = r"""\documentclass[11pt]{article}
\usepackage[margin=2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{tikz}
\usepackage{booktabs}
\begin{document}
"""
standalone_post = "\n\\end{document}\n"
open("working_rate_updated.tex", "w", encoding="utf-8").write(
    standalone_pre + NEW.substitute(common) + standalone_post)
open("working_rate_old_vs_new.tex", "w", encoding="utf-8").write(
    standalone_pre + OLD.substitute(common) + standalone_post)

# ---- LaTeX table version ----
table_rows = []
for i, t in enumerate(ORDER):
    on64 = x64_old[i][0]; nn64 = x64_new[i][0]
    on86 = x86_old[i][0]; nn86 = x86_new[i][0]
    table_rows.append(
        f"{LABELS[i]} & {on64:.1f}\\% & {nn64:.1f}\\% & {on86:.1f}\\% & "
        f"{nn86:.1f}\\% & {nn64-on64:+.1f} & {nn86-on86:+.1f} \\\\")
table_rows.append(r"\midrule")
table_rows.append(
    f"\\textbf{{Media}} & {a64o:.1f}\\% & {a64n:.1f}\\% & {a86o:.1f}\\% & "
    f"{a86n:.1f}\\% & {a64n-a64o:+.1f} & {a86n-a86o:+.1f} \\\\")

TABLE = r"""\begin{table}[htbp]
\centering
\caption{Working rate by technique on the 49 low-rate payloads: old (no flags)
vs new (\texttt{-xd -ebi} + technique). x64 has 13 payloads, x86 has 36.
The mean row is the unweighted mean over the 15 techniques.
Extraction only (no morphing) is 100.0\% on x64 and 94.4\% on x86.}
\label{tab:working_rate_updated}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{2}{c}{x64} & \multicolumn{2}{c}{x86} & \multicolumn{2}{c}{$\Delta$ (pp)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}
Tecnica & old & new & old & new & x64 & x86 \\
\midrule
""" + "\n".join(table_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
open("working_rate_updated_table_snippet.tex", "w", encoding="utf-8").write(TABLE)
open("working_rate_updated_table.tex", "w", encoding="utf-8").write(
    standalone_pre + TABLE + standalone_post)
print("written working_rate_updated_table.tex")

print("written working_rate_updated.tex, working_rate_old_vs_new.tex and snippets")
print("averages:", a64n, a86n, a64o, a86o)
