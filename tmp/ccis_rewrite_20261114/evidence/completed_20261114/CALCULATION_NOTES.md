# Derivation of the completed-campaign evidence

Source files are frozen under sources/ and SHA-256 checked against SOURCES.json.
The earlier benchmark evidence remains in the parent evidence directory.

## Functional outcomes

The LLM cell key is (architecture, payload name, technique, shots). There are
830 build-ledger records and 816 distinct keys. Fourteen keys have two records;
all fourteen have fail/fail status. Select the first record for each key,
preferring an accepted output if one exists. Join the 350 constructed outputs
to the external test ledger on the same key and verify identical SHA-256.
Count status OK as passing. Build and test counts are file/cell counts, whereas
diversity uses distinct built-output hashes. Restarted tests are not variants.

The all_run_cost column sums every recorded cost for a cell, including failed
restarts. Missing usage is missing, not proof that no API work was performed.
The full ledger sums to USD 19.625838237; the representative cell records sum
to USD 19.269954795. The four multigeneration records include two accepted
second-generation outputs and two failed third-generation runs.

llm_by_condition.csv aggregates the cell records by architecture/family/shots.
llm_cells.csv retains the cell status, functional outcome, hash, restart count,
and all-record cost. SUMMARY.json also includes architecture and shot unions.

## Scan results

Take the latest completed record for each manifest SHA-256. All 549 hashes
have such a record. Require sum(stats.values()) > 0 before treating a hash as
evaluable. One completed LLM BCF/0 record is empty; it is excluded from both
the numerator and denominator of scan means and detected-file fractions.
All 548 nonempty records contain 75 reported responses, including unsupported,
timeout, and failure responses. Those are not successful benign verdicts.

For each condition, deduplicate its manifest members by SHA-256 and join to the
scan records. A hash may remain in multiple conditions. The union of the eight
LLM transformation conditions has 323 hashes, 322 evaluable reports, and 221
hashes with at least one malicious response. The 350 files comprise 275 passing
files (263 distinct hashes) and 75 failing files (60 hashes, 59 evaluable).
The passing and failing hash sets are disjoint in this evidence.

q = hashes with at least one malicious response / evaluable hashes.
Mean malicious responses averages the malicious count over evaluable hashes.
Mean fraction averages malicious / sum(stats.values()) over evaluable hashes.
The current cohort is not pooled with historical or earlier pilot scans.

No model requests, payload executions, or scans were performed to derive
these manuscript tables.
