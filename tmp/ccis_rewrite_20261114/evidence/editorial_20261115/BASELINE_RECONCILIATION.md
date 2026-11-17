# Baseline reconciliation - 15 November 2026

The historical working-rate figure was already consolidated into Table 12.
The detection plot now uses the retained results.json records rather than
the inconsistent category/value associations in the preparation manuscript.
There are 15,021 records and 15,020 distinct normalized file paths. The latest
record is retained for the repeated path. Each file uses its own total_scans
denominator; groups are derived from the transformation suffix in its filename.
The eq_nop display category corresponds to files labelled nop_eq. Reference
lines give the arithmetic mean of the 15 configuration rates. This is a
reanalysis of historical records, not a new scan campaign. Historical SGN
comparisons remain explicitly reported conference results.

The available create_var.py analysis was inspected, not executed. Its
disassemble_file function emits insn.mnemonic only. The tokenizer's comments
mention operands, but none are supplied on this path. For each architecture,
the script concatenates original mnemonic listings and separately concatenates
listings within a configuration before computing cosine similarity. The text
and caption now describe corpus-level mnemonic-frequency vectors. The
published similarity values are retained; this revision does not rerun the
historical binary-analysis experiment.
