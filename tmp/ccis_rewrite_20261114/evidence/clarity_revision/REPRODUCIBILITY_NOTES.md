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
