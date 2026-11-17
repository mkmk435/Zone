Supplementary accounting and measurement definitions - 15 November 2026

1. Overall working rate. For input i and configuration t, let n_it be its
historical recorded test count, r_it its historical rate, and r'_it the
updated rate when available. The reconstructed rate is sum_i(n_it*r'_it) /
sum_i(n_it), using r_it for inputs not retested. This holds the original
input weights constant even when updated trials have fewer repetitions.
No new execution count is invented: fractional weighted contributions are
statistical weights, not observed successful executions. Missing historical
input/configuration cells receive no imputed observation or positive result.
PII-containing historical configurations have incomplete input coverage;
the update preserves that reported population. The table's mean row is the
unweighted mean across the same 15 configurations. Exact contributions are
in overall_working_rate_contributions.csv. This is not a full rerun of 102
inputs and is not a claim that the retained historical outputs were regenerated.

2. Temperature. The frozen client used by all three engine snapshots defines
temperature=0.2 and sends it in the request body. The experiment drivers do
not override it. The CLI construction uses the same default in both
architectures and both LLM roles. Neither sampling seed nor top_p is sent.
Per-call run summaries do not independently echo provider-side sampling
configuration; the evidence establishes the submitted client configuration.

3. Similarity. The client's SequenceMatcher score remains in saved records
and the archived detailed controlled-benchmark tables. It compares prepared
and returned instruction listings and filters NOP-like operations in the
NOP condition. It is not renamed as cosine similarity. No new historical-
metric cosine/entropy campaign was performed in this editorial revision.

4. Scan completeness. The campaign contains 549 unique submitted hashes and
549 completed-status records. One BCF/0 LLM report has zero total responses
and is treated as missing, leaving 548 usable reports (322 LLM, 207 wrapping,
19 data-only). The missing hash is
4d7ddb053e7f2234c392c9f6ad3cf7d019941b99535c1b949ca2e315dcc4e007.
It is not classified as undetected. No new upload, reanalysis, or API call
was made in this revision. Its recorded functional test failed. Therefore
all 263 hashes belonging to functionally successful LLM outputs have reports.

5. Detection denominator. The mean DR uses malicious / total reported
responses, with 75 responses per nonempty report, matching the historical
denominator convention. Unsupported/timeouts/failures remain in that total.
For wrapping these categories are 3,090 / 132 / 29 across 15,525 responses.
Across all current groups they are 8,184 / 298 / 74. These are not benign
verdicts. The supplementary scan_overall.csv also retains detected-file rate
(q) and mean malicious-engine count; q is removed from the main table.

6. Data-only scans. The separate 19-output LLM-data group has 19 detected
hashes, mean 20.63 malicious responses and mean engine DR 27.51%. These scans
were already present, not repeated for this revision. They do not replace
the 350-output evaluation of the LLM transformation campaign on 102 inputs.

7. Earlier pilots. earlier_pilots.tex preserves the former section 12.7:
the earlier 220-hash cohort, 13 original controls, MessageBox pilot selection
policy, and historical artifact-availability audit. Those records are not
mixed into the completed campaign. controlled_benchmark_details.tex preserves
the previous native and per-shot LLM tables, including similarity and costs.

8. Scope of this revision. All changes are editorial or offline statistical
analyses of saved data. No rewriting engine was modified, and no payload was
generated or executed. The recorded native x86 IBP result is unchanged.
