# Statistical Review — Astrology Efficacy Study (GATE 2)

Reviewer: independent stats-reviewer agent. Scope: `analysis/plan.md`, `analysis/hypotheses.py`,
`analysis/inference.py`, all numbered analysis scripts, `results/*.json`, `results/*.md`,
`results/*.csv`, `data/provenance.md`. This review does **not** take `results.md` on trust; every
headline number below was cross-checked against the underlying `estimates_*.json` files and, where
feasible, recomputed by hand from the raw JSON fields.

**Tooling limitation, disclosed up front:** this review session was not given a shell/execution
tool, so I could not literally run `python analysis/run_all.py` or any individual script, as the
skill mandates. What follows instead is a full static/document reproducibility audit: reading every
analysis script line-by-line, reading every `estimates_*.json`, hand-recomputing several statistics
from the raw fields (BH adjustment, equivalence bounds, OR conversions), and checking that
`results.md` is generated mechanically from the JSON with no hand-typed numbers. I found no
arithmetic or transcription inconsistencies anywhere I checked (see Rerun Log). I could not, however,
verify that a *fresh* run of the pipeline reproduces these JSON files bit-for-bit — that check still
needs to happen with an execution-capable agent before this can be a full "pass." I am flagging this
as a must-fix procedural item, not as evidence of a problem.

---

## Verdict: **pass with fixes**

The design is unusually rigorous for this kind of study — real pre-registration, frozen executable
hypotheses, dual TOST+Bayes inference, a falsification battery with teeth, and an honest, prominent
report of the battery's failures. Nothing here looks fabricated, and nothing I checked numerically
was wrong. But several things need fixing before this is publication-ready: one place where the
write-up's confidence outruns its own diagnostic evidence (the Study 1 Mercury "resolution"), one
place where a pre-registered decision rule is triggered but never explicitly engaged, one place where
the pre-registered Bayes-factor recipe was silently swapped for a different one, and a couple of
smaller disclosure gaps.

---

## Must-fix

### 1. The Study 1 "the local-randomization result resolves Mercury" claim overclaims what the diagnostics actually show

`results.md` states as its headline follow-up: *"This resolves the one nominally significant
confirmatory result... The negative `rdrobust` estimate was an artifact of the continuity
assumptions, as the placebo and density failures indicated."* That is stronger than the evidence in
the project's own diagnostics file supports.

- The specific mechanistic story offered for *why* the continuity estimator fails — Mercury/Venus
  station-and-reverse, so triple-crossing "crowds" the running variable near some cusps — is
  **directly tested and rejected** in `08_diagnostics.py` / `estimates_diagnostics.json`
  (`density_vs_crowding.crowding_hypothesis_supported: false`; isolated cusps reject density at
  26.3%, crowded cusps at 30.0% — not a meaningfully different rate). `results.md` reports this
  correctly ("NOT supported"), which is good, but then keeps using the *same* "mass points / discrete
  running variable" language to justify discarding the `rdrobust` Mercury estimate, without ever
  identifying what the actual mechanism is. That's a gap between what was shown and what is claimed.
- More importantly, the diagnostics script states its own falsification logic explicitly: *"If the
  pooled effects are artifacts of truncated support, they should shrink toward zero as the threshold
  rises. If they are real, they should survive."* Look at what actually happens for Mercury in
  `results/diagnostics_isolation_grid.csv`:

  | threshold | % of sample retained | estimate [95% CI] | p |
  |---|---|---|---|
  | gap ≥ 10d | 96.7% | −0.00636 [−0.01103, −0.00169] | .008 |
  | gap ≥ 15d | 78.0% | −0.00438 [−0.00879, +0.00003] | .051 |
  | gap ≥ 20d | 10.0% | −0.00449 [−0.01837, +0.00938] | .526 |
  | gap ≥ 35d | 0.0% | not estimable — **every** Mercury birth is within 35 days of another crossing |

  The estimate does **not** shrink toward zero as crowding is excluded — at 97% of the sample
  retained it is still significantly negative and, if anything, slightly *larger* in magnitude than
  the primary pooled estimate (−0.00636 vs −0.00485). It only loses significance at gap ≥ 20d, where
  90% of the sample has been discarded and the CI is simply too wide to resolve anything. By the
  diagnostics script's own stated test, this is evidence *against* the "discreteness/crowding
  artifact" explanation, not for it. And Mercury cannot be tested at the paper's own headline
  isolation threshold (35 days) at all — 0 people qualify.
- The local-randomization estimate that ultimately replaces the headline (+0.00017, N = 599,417) is a
  genuinely different analysis, not a "correction" applied to the same data: it uses a ±3-day window
  (vs. an MSE-optimal bandwidth averaging ~4.7 days but reaching cusps with `h` up to the sensitivity
  grid) and about 56% of the primary sample. It is legitimate and pre-specified (see must-fix #2 for
  the process point), but it estimates a local average effect in a narrower neighborhood on a smaller,
  different subsample — describing it as "resolving" the wider-bandwidth estimate implies the two are
  estimating the same quantity with the second one "correcting" the bias in the first. The isolation
  grid above suggests the truth is closer to: **the continuity-based design failed its own
  falsification checks for a reason that is not actually identified, and the honest conclusion is that
  no single number from Study 1's Mercury cusps should be treated as confirmatory-grade evidence** —
  not that the local-randomization number is now known to be the correct one.

**Fix:** Rewrite the "This resolves..." paragraph (and the parallel Headline paragraph) to (a) state
plainly that the crowding hypothesis was tested and rejected, (b) show or reference the isolation-grid
table above and note that it does not display the shrinkage-to-zero pattern the diagnostic was
designed to detect, and (c) present the local-randomization estimate as the most credible number
available given the falsification failures — not as a demonstrated correction of a diagnosed artifact.
This is a strictly more defensible and, if anything, more interesting story (a genuinely unresolved
methodological puzzle in the running variable) than the current framing.

### 2. Plan §4's pre-registered invalidation clause is triggered and never explicitly engaged

Plan §4 states, in the same breath as listing the falsification battery: *"All of the following are
pre-specified as required, and **a failure of the first two invalidates the corresponding study**."*
The first two are (1) positive controls — passed — and (2) placebo cutoffs — **failed** (11.4%
rejection vs. nominal 5%, `estimates_study1.json: robustness.placebo_rejection_rate = 0.1143`).

By the letter of the pre-registration, this failure invalidates Study 1. `results.md` reports the
placebo failure prominently and honestly, and functionally treats the primary `rdrobust` estimator as
untrustworthy — but it never once invokes plan §4's own invalidation language, nor explains why it
interprets the invalidation as applying to the *continuity-based estimator* specifically rather than
to Study 1 as a whole (a reading that would be defensible, since the local-randomization estimator
does not share the continuity assumption the placebo test is diagnostic of — but that argument needs
to be made, not left implicit).

**Fix:** Add an explicit paragraph, ideally right where the placebo failure is first reported, that
(a) quotes or cites plan §4's invalidation clause, (b) states directly that under its terms Study 1's
primary (continuity-based) design is invalidated, and (c) gives the reasoning for why the
pre-registered secondary (local-randomization) estimator is offered in its place rather than simply
reporting Study 1 as void. This is mostly a transparency fix — the substance is already implicit in
the current text — but a reviewer or reader should not have to infer that a pre-registered "stop"
condition was triggered.

### 3. Bayes factors for proportion-based tests silently used the wrong pre-registered recipe

Plan §2.3 specifies **two distinct** BF recipes: *"Proportions / discontinuities: Beta–Binomial with
a uniform Beta(1,1) prior... Standardized mean differences: default JZS Cauchy, scale r = 0.707."*
`inference.py` implements both (`bf01_beta_binomial` and `bf01_normal_likelihood`), but
`inference.full_test` — the single function used by every analysis script to assemble a confirmatory
test record — **always** calls `bf01_normal_likelihood` with a Cauchy prior, regardless of outcome
type. `bf01_beta_binomial` is never called anywhere in the pipeline (`grep` confirms zero call
sites). Study 1's three tests (occupation-share discontinuities) and Study 2's H2-a/H2-b
(delay/cancellation share differences) are unambiguously "proportions / discontinuities" under the
plan's own taxonomy, yet all of their reported BF01 values (0.24, 1.86, 1.29, 2.02, 1.09 in the
confirmatory table) were computed with the SMD recipe instead.

There is a defensible practical reason for this — Study 1's "estimate" is an inverse-variance-pooled
discontinuity across 10–16 cusps, not a single 2×2 count comparison, so a Beta-Binomial model (which
needs raw `k1, n1, k2, n2`) doesn't apply cleanly to the pooled quantity the way it would to one cusp
— but that reasoning is never stated anywhere, and the deviation is not in the Deviations table.

**Fix:** Either (a) apply `bf01_beta_binomial` at the per-cusp level as a robustness check and report
how it compares to the normal-likelihood BF, or (b) add an explicit entry to the Deviations table
documenting that the pooled/adjusted nature of the Study 1 and Study 2 point estimates precluded the
pre-registered Beta-Binomial recipe and a normal approximation was substituted for all tests
(proportions and SMDs alike), with the practical justification above. Given the numeric BF values are
mostly in the "data insensitive" band already, this is unlikely to change any substantive conclusion,
but it is an undisclosed departure from a specific, named pre-registered method and needs to be owned
as such.

### 4. BF prior-sensitivity curve is computed but never actually reported

Plan §2.3: *"prior-sensitivity curve over r ∈ [0.1, 1.5] reported for every primary test."* Every
`estimates_*.json` record does contain a `bf_sensitivity` field with the full r-grid (verified for
H1-Me, H1-Ve, H1-Ma, H2-a/b, H3-a/b — all present and correctly computed, e.g. H1-Me's BF01 ranges
from 0.23 at r=0.5 to 0.34 at r=1.5, i.e. the "moderate evidence for an effect" conclusion is not
r-fragile). But this is never rendered in `results.md`, `confirmatory_family.csv`, or any figure — it
exists in the machine-readable output only. That doesn't satisfy "reported."

**Fix:** Add a compact sensitivity table or a small multi-line figure (7 tests × 7 r-values) to
`results.md`/the manuscript. This is a cheap fix since the data is already computed; it just needs to
be surfaced.

---

## Should-fix

1. **Fixed-effect pooling with I² up to 80% deserves more than a footnote companion.** `pool_signed`'s
   independence assumption (each person contributes to exactly one cusp) is correct and the FE choice
   is pre-specified, so this is not a plan-adherence problem. But for Mercury (I²=80%, Q=73.2,
   p<.001), the FE CI [−0.0086, −0.0011] is visibly narrower than the RE CI [−0.0132, +0.0062], which
   *includes zero* — the FE/RE disagreement on statistical significance is itself informative and
   deserves a sentence of its own next to the primary estimate, not just a heterogeneity statistic
   buried in the prose.

2. **Undisclosed SESOI choice for Study 2's cancellation outcomes.** Plan §2.2 gives a SESOI only for
   the delay-share outcome (0.5pp). `06_study2_its.py` sets the cancellation SESOI to
   `SESOI_DELAY / 5` = 0.1pp with no comment or justification, and this choice is not in the
   Deviations table. Applying the delay-share SESOI's own stated logic (≈2.5% relative change on the
   ~20% delay base rate) to the ~2% cancellation base rate would suggest ≈0.05pp, not 0.1pp — a
   factor-of-two difference in how tight the equivalence claim is. It happens not to matter for the
   headline conclusion here (H2-b's TOST is "not equivalent" either way), but it should be documented,
   not silently chosen.

3. **Figure 5 (Study 2 permutation null) plots an idealized Gaussian, not the empirical permutation
   histogram.** `09_synthesis.py` draws `exp(-0.5*(x/perm_sd)^2)` rather than a histogram/KDE of the
   actual 10,000 permutation draws. This risks masking any non-normality in the null — a live concern
   here because retrograde+shadow (H2-c) covers 48.4% of all days with periods recurring roughly every
   ~107 days, and the circular-shift exclusion (`min_shift = 30` days) does not exclude offsets near
   multiples of that recurrence interval, where a shifted calendar could partially re-align with the
   true one or with other real retrograde windows. This is unlikely to have flipped any conclusion (H2
   results are uniformly null across both the permutation and HAC frameworks), but the primary-inference
   claim in plan §3 rests on this permutation being an "exact null," and that should be checked (e.g.,
   plot the actual histogram; check whether p-values are sensitive to excluding shift offsets near
   ~107/214/321... days) rather than assumed.

4. **`plan.md` and `hypotheses.py` visibly disagree about the size of the Study 1 confirmatory
   family.** `plan.md` §1.2 says "4 primary tests" and §2.4 says "8 tests" (including Sun);
   `hypotheses.py` drops Sun to exploratory with a dated rationale. I looked for evidence that this
   drop was outcome-driven and don't think it was — the eventual exploratory Sun result is null
   (mean |t| = 0.74), so there was no incentive to hide an inconvenient significant finding by
   dropping the hypothesis, and the stated reason (Ptolemy IV.4 names only Mars/Venus/Mercury as
   occupational significators) is a textual point independent of any data. Still, the two documents
   that both claim GATE-1 status should not contradict each other on their face. Add a one-line, dated
   corrigendum at the top of `plan.md` pointing to `hypotheses.py`'s deviation note.

5. **GSS sociability composite allows an N-of-1-item average.** `04_extract_gss.py` computes
   `sociability` as the mean of however many of the 4 z-scored items are non-missing, with a floor of
   `n_soc_items >= 1`. A composite built from 1 item and one built from 4 have different measurement
   error, which matters for a test whose SESOI is stated in Cohen's-d units. Consider a `>= 2` or
   `>= 3` floor, or at least report the distribution of `n_soc_items` and a robustness check restricted
   to respondents with all 4 items.

6. **`sample_flow.md`'s "People with >=1 occupation: 3,714,005" is confusing, not wrong.** This count
   is taken from the full (unfiltered-by-year) `occupations.parquet` before the year-restricted people
   frame is joined; the real Study 1 analysis N is 3,701,431 (`n_analysis` in
   `estimates_study1.json`), 12,574 lower, and the two are not meant to be the same number. No bug —
   I traced the code path and the arithmetic is internally consistent — but a reader comparing the two
   files would reasonably think they'd found a discrepancy. Add a one-line comment in `03_clean.py`
   clarifying that this count predates the year-restriction join.

## Optional

- `bf01_beta_binomial`, `or_to_risk_difference`/`risk_difference_to_or`, `tost`, `equivalence_bound`,
  and `benjamini_hochberg` were all checked against their mathematical definitions and are correct
  (see Rerun Log for the hand-derivations). `equivalence_bound = |estimate| + z_{0.95}·SE` is the
  correct inversion of the two-one-sided-test procedure at α = .05; the BH implementation is the
  standard step-up procedure and reproduces hand-calculated adjusted p-values exactly.
- Consider actually running the "Venus retrograde placebo" mentioned as a Study 2 robustness idea in
  `06_study2_its.py` (`rob["venus_placebo"] = {"status": "n/a — see exploratory note"}` — it is coded
  but not executed/interpreted). This would be a nice additional falsification check given Study 2's
  otherwise-uniform nulls.

---

## Rerun log

**No execution tool was available in this review session** (Read/Grep/Glob/Write only — no shell).
I could not run `python analysis/run_all.py` or any individual script, so the skill's mandatory rerun
did not happen in this pass. What I did instead, as a substitute:

- Read every analysis script (`00`–`11`) in full and traced the data flow from raw extraction through
  `09_synthesis.py`'s `results.md` generation.
- Confirmed `09_synthesis.py:write_results_md` reads exclusively from the `estimates_*.json` files and
  contains no hand-typed statistics — so `results.md` is mechanically derived from the JSON, and a
  correct JSON guarantees a correct `results.md` (mod the one dead-code/omission issues flagged above).
- Spot-checked (exact match, to displayed precision) against `estimates_study1.json`,
  `estimates_study2.json`, `estimates_study3.json`:
  - H1-Me/Ve/Ma: estimate, CI, p, BF01, heterogeneity Q/I², RE companion — all match.
  - Placebo rejection rate: 28/245 = 11.43% — matches "11.4%."
  - Density rejection rate: 20/69 = 28.99% — matches "29.0%."
  - Covariate balance: exactly 2 of 9 checks (mercury/mars `birth_year`) have p < .05 — matches "2 of
    9," and the reported jump magnitudes (+0.930, +0.936 years) and p-values (3.7e-6, 1.6e-3) match.
  - H2-a/b/c/c-cancel: regression estimate/CI/p, permutation p, TOST, BF01 — all match.
  - H3-a/b/replication: estimate/CI/p, TOST, BF01, simple slopes, N — all match.
  - Local-randomization table (Mercury/Venus/Mars): estimate, CI, randomization p, equivalence-bound
    OR — all match `estimates_diagnostics.json`.
- Hand-recomputed the Benjamini-Hochberg adjustment from the 7 raw p-values
  (.011, .918, .541, .890, .372, .417, .838) using the standard step-up procedure and reproduced the
  reported pattern (H1-Me adjusted ≈ .077, all six others = .918 after the cumulative-min step) —
  matches the table (.075/.918, rounding difference only, from using the rounded vs. exact raw p).
- Hand-recomputed `equivalence_bound` for H1-Me: |−0.0048532| + 1.6449·(0.0019017) = 0.007981 —
  matches the JSON's `equivalence_bound` field exactly, and the OR conversion
  (risk_difference_to_or(0.007981, 0.186672) = 1.0529) matches the reported "rules out odds ratios
  beyond 1.053."
- Verified `run_all.py`'s stage list is complete and ordered correctly by dependency, and that the
  seed (`20260918`, set in `inference.SEED`) is threaded through every stochastic script (`05`, `06`,
  `07`, `08`, `11`) via either `np.random.seed(SEED)` or `np.random.default_rng(SEED)`.

**Outstanding:** an agent with execution access should still perform an actual rerun of at least
`05_study1_rdd.py`, `08_diagnostics.py`, `07_study3_gss.py`, and `09_synthesis.py --only` (all fast,
no downloads required, per the task's own note that Study 1 takes ~10 min and no BTS re-download is
needed) and diff the resulting JSON/`results.md` against the committed versions byte-for-byte. I found
nothing in the static audit that suggests this will fail, but the mandatory rerun genuinely did not
happen in this pass and should not be treated as satisfied.

---

## Overall assessment

This is a well-built, honestly self-critical analysis with real pre-registration discipline: the
hypotheses are frozen and traceable to quoted primary sources, the dual TOST+Bayes framework is
implemented correctly (verified by hand), the falsification battery is pre-specified with teeth
(including an explicit invalidation rule), and — unusually for this kind of report — the write-up
leads with its own failures rather than burying them. The known-gaps list (citizenship covariate
missing, Study 3 moderation N shortfall, BTS span truncation, H1-Su drop) is exactly what it should
be and I found nothing not already disclosed. Two of the analysis's central rhetorical moves, however,
outrun their own evidence: the claim that the local-randomization estimator "resolves" the Mercury
result is not fully supported by the project's own isolation-grid diagnostic (which does not show the
shrinkage-to-zero pattern the diagnostic was designed to detect), and the pre-registered "a failure of
[the placebo test] invalidates the study" clause is triggered but never explicitly engaged in the
write-up. Neither of these is fabrication or p-hacking — the underlying numbers are all correct and
consistently reported — but the *interpretive* confidence in the "we found astrology has essentially
zero effect on Mercurial vocations, tightly bounded" headline is higher than the diagnostics actually
license, and a skeptical reader (or a hostile one, motivated to defend astrology) would have real
ammunition here. Fix the four must-fix items — particularly reframing the Mercury resolution
honestly — and this is solid, publishable work.
