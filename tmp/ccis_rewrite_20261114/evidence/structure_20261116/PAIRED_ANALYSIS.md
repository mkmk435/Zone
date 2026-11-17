# Exploratory paired prompting comparison

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
