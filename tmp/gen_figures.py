import os

TECHS = ["nop", "eq", "pii", "bcf", "ibp",
         "eq_nop_pii", "eq_nop_bcf", "eq_nop_ibp",
         "nop_eq", "nop_pii", "nop_bcf", "nop_ibp",
         "eq_pii", "eq_bcf", "eq_ibp"]
LABELS = [t.replace("_", r"\_") for t in TECHS]

X86 = [48.3, 77.5, 38.8, 52.7, 51.7, 24.0, 43.9, 40.8, 48.1, 29.3, 45.8, 40.5, 28.0, 55.2, 50.6]
X64 = [65.5, 65.5, 60.3, 65.8, 65.8, 64.2, 1.1, 65.8, 66.0, 57.3, 0.3, 66.3, 57.3, 66.8, 66.0]
BEFORE = [26.2, 93.1, 38.5, 38.5, 24.6, 36.9, 37.7, 26.9, 27.7, 38.5, 36.9, 26.9, 38.5, 36.9, 23.1]
AFTER = [77.7, 100.0, 84.6, 80.8, 64.6, 63.8, 80.8, 53.1, 78.5, 65.4, 83.1, 54.6, 84.6, 84.6, 65.4]

PAYLOADS = [
    ("windows_x64_custom_reverse_https", "0.0 (0/149)", "94.0 (141/150)", "88.0 (132/150)"),
    ("windows_x64_custom_reverse_winhttp", "0.0 (0/149)", "6.7 (10/150)", "93.3 (140/150)"),
    ("windows_x64_custom_reverse_winhttps", "0.0 (0/150)", "6.7 (10/150)", "6.7 (10/150)"),
    ("windows_x64_meterpreter_reverse_http", "0.0 (0/149)", "4.7 (7/150)", "88.7 (133/150)"),
    ("windows_x64_meterpreter_reverse_https", "0.0 (0/149)", "6.7 (10/150)", "88.0 (132/150)"),
    ("windows_x64_meterpreter_reverse_winhttp", "0.0 (0/149)", "82.0 (123/150)", "88.0 (132/150)"),
    ("windows_x64_vncinject_reverse_http", "0.0 (0/150)", "2.7 (4/150)", "89.3 (134/150)"),
    ("windows_x64_vncinject_reverse_winhttp", "0.0 (0/150)", "6.7 (10/150)", "92.7 (139/150)"),
    ("windows_x64_vncinject_reverse_winhttps", "0.0 (0/150)", "6.7 (10/150)", "6.7 (10/150)"),
    ("windows_x64_meterpreter_reverse_winhttps", "1.3 (2/150)", "82.7 (124/150)", "76.7 (115/150)"),
    ("windows_x64_vncinject_reverse_https", "1.3 (2/149)", "6.7 (10/150)", "94.7 (142/150)"),
    ("windows_x64_messagebox", "2.7 (4/150)", "73.3 (110/150)", "72.0 (108/150)"),
    ("windows_x64_custom_reverse_http", "10.2 (15/147)", "98.0 (147/150)", "87.3 (131/150)"),
]

def coords(vals):
    return " ".join(f"({i},{v:.1f})" for i, v in enumerate(vals))

def nodes(vals, color, pos):
    out = []
    for i, v in enumerate(vals):
        out.append(f"\\node at (axis cs:{i},{v:.1f}) [{pos}, {color}, font=\\tiny] {{{v:.1f}\\%}};")
    return "\n".join(out)

def light(color):
    """orange -> orange!30, blue!70 -> blue!30, green!55!black -> green!30."""
    return color.split("!")[0] + "!30"

def axis_block(series, avg_a, avg_b, legend_a, legend_b, colors, ymax=105):
    a_name, a_vals, a_pos = series[0]
    b_name, b_vals, b_pos = series[1]
    ca, cb = colors
    return f"""\\begin{{axis}}[
    width=\\linewidth,
    height=0.7\\linewidth,
    ylabel={{Working rate (\\%)}},
    ymin=0, ymax={ymax},
    ytick={{0,20,40,60,80,100}},
    xtick={{0,...,14}},
    xticklabels={{{", ".join(LABELS)}}},
    xticklabel style={{rotate=45, anchor=east, font=\\scriptsize}},
    legend pos=north east,
    legend style={{
        font=\\small,
        fill=white,
        fill opacity=0.85,
        draw opacity=1,
        text opacity=1
    }},
    grid=major,
    grid style={{dashed, gray!30}},
    ymajorgrids=true,
]
% medie (sotto i punti)
\\addplot[{ca}, dashed, thick, no marks, forget plot] coordinates {{(0,{avg_a:.1f}) (14,{avg_a:.1f})}};
\\addplot[{cb}, dashed, thick, no marks, forget plot] coordinates {{(0,{avg_b:.1f}) (14,{avg_b:.1f})}};

\\addplot[only marks, mark=*, mark size=2pt, draw={ca}, mark options={{fill={light(ca)}}}]
    coordinates {{{coords(a_vals)}}};
\\addlegendentry{{{legend_a}}}

\\addplot[only marks, mark=*, mark size=2pt, draw={cb}, mark options={{fill={light(cb)}}}]
    coordinates {{{coords(b_vals)}}};
\\addlegendentry{{{legend_b}}}

\\addlegendimage{{{ca}, dashed, thick}}
\\addlegendentry{{media {legend_a}: {avg_a:.1f}\\%}}
\\addlegendimage{{{cb}, dashed, thick}}
\\addlegendentry{{media {legend_b}: {avg_b:.1f}\\%}}

{nodes(a_vals, ca, a_pos)}
{nodes(b_vals, cb, b_pos)}
\\end{{axis}}"""

fig1 = axis_block(
    [("x64", X64, "above"), ("x86", X86, "below")],
    55.6, 45.4,
    "x64 (tutti i payload)", "x86 (tutti i payload)",
    ("orange", "blue!70"),
)
fig2 = axis_block(
    [("after", AFTER, "above"), ("before", BEFORE, "below")],
    74.8, 36.7,
    "x64: post -xd -ebi + getpc", "x64: post -xd -ebi",
    ("green!55!black", "red!75"),
)

def pct(s):
    return float(s.split()[0])

table_rows = "\n".join(
    f"\\texttt{{{n.replace('_', chr(92)+'_')}}} & {o} & {p} & {a} & {pct(a)-pct(p):+.1f} \\\\"
    for n, o, p, a in PAYLOADS
)
table_rows += "\n\\midrule\n"
table_rows += ("\\textbf{Totale (13)} & 1.2 (23/1941) & 36.7 (716/1950) & "
               "74.8 (1458/1950) & +38.1 \\\\")

tex = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{pgfplots}
\usepackage{graphicx}
\usepackage{booktabs}
\pgfplotsset{compat=1.18}

\begin{document}

%% =====================================================================
%% Figure 1: dataset originale, x86 vs x64
%% =====================================================================
\begin{figure}[htbp]
\centering
\scalebox{0.95}{
\begin{tikzpicture}
""" + fig1 + r"""
\end{tikzpicture}
}
\caption{Working Rate Comparison (x86 vs x64), dataset originale
         \texttt{test\_report.txt}.}
\label{fig:working_rate_original}
\end{figure}

%% =====================================================================
%% Figure 2: 13 payload x64, prima vs dopo la fix getpc
%% =====================================================================
\begin{figure}[htbp]
\centering
\scalebox{0.95}{
\begin{tikzpicture}
""" + fig2 + r"""
\end{tikzpicture}
}
\caption{Working rate x64 sui 13 payload a basso rate: confronto tra il run
         \texttt{-xd -ebi} e il run \texttt{-xd -ebi} + fix getpc.}
\label{fig:working_rate_getpc}
\end{figure}

%% =====================================================================
%% Tabella riassuntiva per payload
%% =====================================================================
\begin{table}[htbp]
\centering
\small
\caption{Working rate per payload (13 payload x64). \emph{Originale} = nessun
         flag; \emph{Post \texttt{-xd -ebi}} = capstone 5.0.0.post1 con
         \texttt{-xd -ebi} (prima della fix getpc); \emph{Post \texttt{-xd -ebi}
         + getpc} = run aggiornato. Tra parentesi OK/test.}
\label{tab:working_rate_payloads}
\begin{tabular}{lrrrr}
\toprule
Payload & Originale & Post \texttt{-xd -ebi} & Post \texttt{-xd -ebi} + getpc & $\Delta$ \\
\midrule
""" + table_rows + r"""
\bottomrule
\end{tabular}
\end{table}

\end{document}
"""

open("working_rate_figures.tex", "w", encoding="utf-8").write(tex)
print("written working_rate_figures.tex")

# (preview PNG opzionale non generato: matplotlib non e' installato)
