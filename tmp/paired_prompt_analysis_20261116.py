"""Read-only statistical reanalysis of the 816 saved campaign outcomes."""
from pathlib import Path
import csv, collections, math, json, hashlib, argparse

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1],help='Supplement root containing evidence/completed_20261114/llm_cells.csv')
root=parser.parse_args().root
source=root/'evidence/completed_20261114/llm_cells.csv'
out=root/'evidence/structure_20261116'
out.mkdir(exist_ok=True)
rows=list(csv.DictReader(source.open(encoding='utf-8')))
assert len(rows)==816
assert {r['working'] for r in rows}=={'True','False'}
pairs=collections.defaultdict(dict)
for r in rows:
    key=(r['arch'],r['payload'],r['tech']); shot=int(r['shots'])
    assert shot not in pairs[key]
    pairs[key][shot]=r['working']=='True'
assert len(pairs)==408 and all(set(p)=={0,2} for p in pairs.values())
counts=collections.Counter((v[0],v[2]) for v in pairs.values())
b=counts[True,False];c=counts[False,True];n=b+c
mcnemar=min(1,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/2**n)
by_input=collections.defaultdict(list)
for key,p in pairs.items():by_input[key[:2]].append(int(p[0])-int(p[2]))
assert len(by_input)==102 and all(len(v)==4 for v in by_input.values())
differences={k:sum(v) for k,v in by_input.items()}
weights=[abs(d) for d in differences.values() if d]
distribution=collections.Counter({0:1})
for w in weights:
    updated=collections.Counter()
    for s,count in distribution.items():
        updated[s+w]+=count;updated[s-w]+=count
    distribution=updated
observed=sum(differences.values())
cluster_p=sum(count for s,count in distribution.items() if abs(s)>=abs(observed))/2**len(weights)
# Independent enumeration checks the small exact input-level distribution.
enumerated=[0]
for w in weights:enumerated=[s+sign*w for s in enumerated for sign in (-1,1)]
assert collections.Counter(enumerated)==distribution
assert sum(p[0] for p in pairs.values())==139
assert sum(p[2] for p in pairs.values())==136
with (out/'prompt_pairs.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['arch','payload','family','zero_shot_working','two_shot_working'])
    for key,p in sorted(pairs.items()):w.writerow([*key,int(p[0]),int(p[2])])
with (out/'prompt_payload_differences.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['arch','payload','zero_minus_two_working_count'])
    for key,d in sorted(differences.items()):w.writerow([*key,d])
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cells':816,'pairs':408,'inputs':102,'both_work':counts[True,True],'only_zero_shot_works':b,'only_two_shot_works':c,'neither_works':counts[False,False],'zero_shot_successes':139,'two_shot_successes':136,'exact_mcnemar_two_sided_p':mcnemar,'input_level_sign_flip_two_sided_p':cluster_p,'nonzero_input_differences':len(weights),'observed_zero_minus_two':observed,'input_difference_counts':dict(collections.Counter(differences.values())),'new_model_requests':False,'new_executions':False,'interpretation':'Exploratory comparison of recorded campaign outcomes; no equivalence or causal-effect claim.'}
(out/'prompt_paired_tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(out/'PAIRED_ANALYSIS.md').write_text('''# Exploratory paired prompting comparison

The saved 816 rows form 408 complete pairs keyed by architecture, input identity,
and transformation family. There are 102 inputs, each with four families and
two prompting conditions. The endpoint is the recorded overall working outcome,
including construction failures as unsuccessful planned cases; no cell was
omitted or newly generated. The completed campaign's retry protocol remains
unchanged. This is a secondary analysis, not a preregistered hypothesis test.

The 2x2 table is: both working 118; zero-shot only 21; two-shot only 18;
neither working 251. The observed success totals are 139 and 136. Under the
usual McNemar null, conditional on 39 discordant pairs, the count favoring
either condition is Binomial(39, 1/2). The exact two-sided p-value is
2 * sum_{k=0}^{18} choose(39,k) / 2^39 = 0.7492586247608415.
Its usual interpretation assumes independent pairs, which is questionable
when four families share one input.

As a sensitivity analysis, we swap the two prompting labels jointly for all
four families belonging to an input. For each input, d is the zero-shot minus
two-shot working count; the statistic is abs(sum(d)), observed as 3. There are
81 zeros, nine +1, six -1, three +2 and three -2 input differences. The exact
sign-flip distribution enumerates 2^21 assignments for nonzero differences;
zero differences do not affect it. The two-sided probability of a statistic
at least 3 is 0.7521781921386719. Dynamic programming and direct enumeration
give identical distributions. This check preserves within-input family
dependence, while assuming input-level exchangeability under the null.

Neither calculation establishes equality of the prompting conditions or
generalizes beyond the tested corpus and campaign. The requests do not share
controlled random streams, and the conditions were not described as a
randomized assignment over a population. Accordingly, both p-values are
reported as exploratory checks alongside the observed counts.
''',encoding='utf-8')
print(json.dumps(result,indent=2))
