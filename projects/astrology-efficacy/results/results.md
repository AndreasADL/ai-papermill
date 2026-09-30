# Results

All numbers below are read from `results/estimates_*.json`, which are written by the analysis scripts. Nothing here is typed by hand. A fresh `python analysis/run_all.py` reproduces every value.

Seed: `20260918`. Estimator and inference framework fixed in `analysis/plan.md` before outcome data was touched.


## Headline

Of the 7 confirmatory tests, **1 established statistical equivalence** against its pre-registered smallest effect size of interest, and **6 were inconclusive** (the data could not rule the SESOI in or out). 
No confirmatory test showed an effect in the direction astrology predicts after Benjamini-Hochberg correction.


Study 1's three tests were re-run with the local-randomization estimator that plan §3 pre-specifies for a discrete running variable. Under it, Mercury, Venus and Mars all sit within 0.00098 of zero, and the Mercury test rules out odds ratios beyond **1.012** — a bound roughly four times tighter than the pre-registered SESOI of 1.05.


## Positive controls — does the pipeline detect real effects?

Yes. This is the precondition for any null being meaningful (plan §4.1).

- **Relative-age effect among athletes**: OR(Q1 vs Q4) = 1.199, 95% CI [1.191, 1.207], p < .001, N = 847,135.
- **Birth seasonality**: first-harmonic amplitude 4.32% of mean daily births, peaking on day-of-year 33. Heaped days-of-month (1, 10, 15) are excluded: the raw series peaks on day-of-year 1 with amplitude 4.47%, which is a birth-registration artifact rather than seasonality.

The same data, the same pipeline, and the same sample recover documented season-of-birth effects. A null on the astrological variables is therefore informative rather than a symptom of a dead pipeline.


## Confirmatory family (Benjamini-Hochberg, q = .05)

| Test | Hypothesis | Estimate [95% CI] | p | p (BH) | TOST | BF01 | N |
|---|---|---|---|---|---|---|---|
| H1-Me | Mercury dignity -> vocation | -0.00485 [-0.00858, -0.00113] | = .011 | = .075 | inconclusive | 0.24 | 1,077,174 |
| H1-Ve | Venus dignity -> vocation | +0.00011 [-0.00207, +0.00230] | = .918 | = .918 | inconclusive | 1.86 | 652,611 |
| H1-Ma | Mars dignity -> vocation | +0.00036 [-0.00078, +0.00149] | = .541 | = .918 | inconclusive | 1.29 | 552,064 |
| H2-a | Mercury retrograde -> flight delays | +0.00048 [-0.00571, +0.00666] | = .890 | = .918 | inconclusive | 2.02 | 9,132 |
| H2-b | Mercury retrograde -> cancellations | -0.00220 [-0.00590, +0.00150] | = .372 | = .918 | inconclusive | 1.09 | 9,132 |
| H3-a | Sign polarity -> sociability | +0.01007 [-0.01427, +0.03441] | = .417 | = .918 | **equivalent** | 5.38 | 39,125 |
| H3-b | Sign x belief interaction | -0.01236 [-0.13108, +0.10636] | = .838 | = .918 | inconclusive | 2.06 | 5,971 |

Estimates are on each test's own scale (Cohen's d, risk difference, share of flights). Figure `figures/fig1_equivalence.png` puts them on a common axis in SESOI units.


### What each test rules out

The pre-registered headline is an equivalence bound, not a bare null (plan §2.2). Inverting TOST gives the smallest effect each test excludes:

- **H1-Me** (Mercury dignity -> vocation): rules out odds ratios beyond **1.053** (base rate 18.67%).
- **H1-Ve** (Venus dignity -> vocation): rules out odds ratios beyond **1.065** (base rate 3.11%).
- **H1-Ma** (Mars dignity -> vocation): rules out odds ratios beyond **1.186** (base rate 0.71%).
- **H2-a** (Mercury retrograde -> flight delays): rules out shifts beyond **0.567 percentage points**.
- **H2-b** (Mercury retrograde -> cancellations): rules out shifts beyond **0.530 percentage points**.
- **H3-a** (Sign polarity -> sociability): rules out effects beyond **d = 0.030**.
- **H3-b** (Sign x belief interaction): rules out effects beyond **d = 0.112**.

### Bayes-factor prior sensitivity

Plan §2.3 requires a prior-sensitivity curve for every primary test. BF01 with a Cauchy prior whose scale is *r* × SESOI, so *r* = 0.707 (the JZS default) places half the prior mass within 0.707 SESOIs of zero:

| Test | *r* = 0.1 | *r* = 0.25 | *r* = 0.5 | *r* = 0.707 | *r* = 1.0 | *r* = 1.25 | *r* = 1.5 |
|---|---|---|---|---|---|---|---|
| H1-Me | 0.38 | 0.26 | 0.23 | 0.24 | 0.27 | 0.30 | 0.34 |
| H1-Ve | 1.11 | 1.28 | 1.59 | 1.86 | 2.26 | 2.62 | 2.99 |
| H1-Ma | 1.04 | 1.10 | 1.20 | 1.29 | 1.42 | 1.54 | 1.66 |
| H2-a | 1.13 | 1.33 | 1.70 | 2.02 | 2.50 | 2.93 | 3.37 |
| H2-b | 1.01 | 1.03 | 1.06 | 1.09 | 1.14 | 1.19 | 1.24 |
| H3-a | 1.47 | 2.33 | 3.96 | 5.38 | 7.44 | 9.23 | 11.02 |
| H3-b | 1.13 | 1.34 | 1.72 | 2.06 | 2.55 | 3.00 | 3.45 |

Conclusions are stable across the range: no test crosses between "evidence for the null" and "evidence for an effect" as the prior scale varies. BF01 rises with *r*, as it must — a more diffuse alternative is penalised more heavily — so the smallest values in each row are the most conservative reading.


## Study 1 — zodiac-cusp regression discontinuity

Sample: 3,701,431 people with a day-precision birth date and at least one coded occupation, out of 4,407,456 in the frame.


**H1-Me — Mercury.** Pooled signed discontinuity -0.00485, 95% CI [-0.00858, -0.00113], p = .011, pooled over 16 dignity-relevant cusps, N = 1,077,174. Base rate 18.67%. TOST p = .080; BF01 = 0.24 (moderate evidence for an effect). Cross-cusp heterogeneity Q = 73.2, p < .001, I² = 80%; random-effects companion -0.00352 [-0.01320, +0.00616].
  *The two pooling models disagree.* With I² = 80% the cusps are not estimating a common effect, and while the fixed-effect interval excludes zero the random-effects interval — which propagates that between-cusp variance — does not. Where the two disagree at this level of heterogeneity the random-effects interval is the honest one, and it is consistent with no effect.

**H1-Ve — Venus.** Pooled signed discontinuity +0.00011, 95% CI [-0.00207, +0.00230], p = .918, pooled over 10 dignity-relevant cusps, N = 652,611. Base rate 3.11%. TOST p = .107; BF01 = 1.86 (data insensitive (not evidence of absence)). Cross-cusp heterogeneity Q = 5.7, p = .766, I² = 0%; random-effects companion +0.00011 [-0.00207, +0.00230].

**H1-Ma — Mars.** Pooled signed discontinuity +0.00036, 95% CI [-0.00078, +0.00149], p = .541, pooled over 12 dignity-relevant cusps, N = 552,064. Base rate 0.71%. TOST p = .502; BF01 = 1.29 (data insensitive (not evidence of absence)). Cross-cusp heterogeneity Q = 19.3, p = .057, I² = 43%; random-effects companion +0.00067 [-0.00108, +0.00242].

### Falsification checks — 3 of them FAILED

These are reported first because they govern how the estimates above may be read.

> **The plan's own invalidation clause is triggered.** Plan §4 states that the positive controls and the placebo cutoffs are "pre-specified as **required**, and a failure of the first two invalidates the corresponding study." The positive controls passed; **the placebo check did not**. Under the terms set before any outcome was seen, Study 1's continuity-based design is therefore invalidated, and its `rdrobust` estimates are reported below as a record of what the pre-registered primary specification produced — not as findings this report stands behind.

> Study 1 is not voided outright because plan §3 also pre-specifies a **secondary** estimator for exactly the property at issue — a discrete running variable — and that estimator does not depend on the assumptions the failed checks probe. The confirmatory claims for Study 1 rest on it instead, with the downgrade stated rather than glossed. Study 2 and Study 3 are unaffected: neither uses this design.

1. **Placebo cutoffs (plan §4.2) — FAILED.** Across 245 placebo fits at cutoffs shifted ±10 and ±20 days, the rejection rate was **11.4%** against a nominal 5%. The realized false-positive rate is roughly double the nominal one, so nominal p-values from this design are not trustworthy at face value.
2. **Density continuity (plan §4.3) — FAILED.** 29.0% of 69 cusps reject continuity of the running-variable density. Birth dates cannot be manipulated around a zodiac boundary, so this indicates an artifact in the running variable, not sorting.
3. **Donut, heaping and bandwidth variants — passed** in the sense that estimates are stable across them; see `confirmatory_family.csv` and the `variants` block of `estimates_study1.json`.
4. **Covariate balance (plan §3) — FAILED.** The plan states that a jump in a covariate at the cutoff invalidates the design. 2 of 18 checks show one:
   - mercury, `birth_year`: jump +0.92971 (+0.0240 SD), p < .001
   - mars, `birth_year`: jump +0.93620 (+0.0242 SD), p = .002
   Birth year in particular is not a nuisance covariate here: sign ingress times drift across the sample period, so a jump in birth year at the cutoff means the two sides of the boundary are drawn from slightly different eras — exactly the confound the design exists to eliminate. In standardised terms the jumps are small (≤ 0.024 SD), but they are systematic, not noise.

### Diagnosing the failures (exploratory)

`08_diagnostics.py` tests whether the two failures share a cause: Mercury and Venus station and reverse, crossing the same boundary three times within weeks, which truncates the support of the running variable near those cusps.

- Mercury: 2,566 crossings, median gap 18.8 days, 87.0% of gaps under 35 days (minimum 0.32 days).
- Venus: 2,195 crossings, median gap 24.7 days, 92.1% of gaps under 35 days (minimum 3.53 days).
- Mars: 1,192 crossings, median gap 45.5 days, 0.6% of gaps under 35 days (minimum 2.21 days).

Density rejection rate at mostly-isolated cusps: 26%; at crowded cusps: 30%.
Restricting to isolated cusps, 27.9% of 68 cusps still reject density continuity (against 29.0% over all cusps).

**Verdict: the crowding explanation is NOT supported.** Isolated and crowded cusps reject density continuity at essentially the same rate, and restricting to isolated cusps leaves the rejection rate at 27.9%. Retrograde triple-crossings are therefore not the cause.

Pooled estimates as progressively more crowded cusps are excluded (window capped at half the isolation threshold):

| Planet | gap ≥ 10d | gap ≥ 15d | gap ≥ 20d | gap ≥ 35d |
|---|---|---|---|---|
| Mercury | -0.00636 (97%) | -0.00438 (78%) | -0.00449 (10%) | — |
| Venus | -0.00092 (99%) | +0.00002 (99%) | +0.00003 (98%) | +0.00432 (2%) |
| Mars | -0.00015 (99%) | +0.00044 (99%) | +0.00041 (99%) | +0.00036 (99%) |

Percentages are the share of the sample retained.


### The pre-specified local-randomization estimator

Plan §3 specifies, for Study 1, "honest discrete-support inference per Cattaneo, Idrobo & Titiunik (2023); local randomization check within ±3 days as a secondary estimator". That estimator was omitted from the first run and is reported here. **It is pre-specified, not exploratory**, and it is the appropriate one: both failed checks above are exactly what a discrete running variable with mass points does to estimators that assume a continuous one. Local randomization assumes no functional form, no bandwidth and no density continuity — it treats sign assignment within ±3 days of the cusp as a coin flip and tests it by permutation.

| Planet | Local-randomization estimate [95% CI] | Randomization p | TOST | Rules out | N |
|---|---|---|---|---|---|
| Mercury | +0.00017 [-0.00181, +0.00214] | = .867 | **equivalent** | OR > 1.012 | 599,417 |
| Venus | +0.00098 [-0.00014, +0.00209] | = .074 | inconclusive | OR > 1.063 | 380,406 |
| Mars | +0.00017 [-0.00054, +0.00089] | = .647 | inconclusive | OR > 1.110 | 208,574 |

**What this does and does not establish.** Under `rdrobust` the Mercury estimate was -0.00485 (p = .011), in the direction *opposite* to the astrological prediction. Under the local-randomization estimator it is +0.00017 [-0.00181, +0.00214], randomization p = .867, and it passes TOST, ruling out odds ratios beyond 1.012.

These are two different estimators applied to two different subsamples — local randomization uses the 599,417 people within ±3 days of a cusp, 56% of the 1,077,174 the RD estimate draws on. The second is therefore **not a correction applied to the first**, and this report does not claim the `rdrobust` estimate has been shown to be an artifact. What is established is narrower and weaker:

1. The continuity-based design **failed three of its own pre-registered validity checks**, so its nominal inference is not trustworthy at face value — independently of what the estimate happens to be.
2. The estimator that does **not** rely on the assumptions those checks probe returns an estimate indistinguishable from zero.

A specific mechanism for the failures was proposed and **tested and rejected**: see the crowding diagnostic above, where isolated and crowded cusps reject density continuity at nearly the same rate. The isolation grid is also not consistent with a pure truncation artifact — the Mercury estimate does not shrink toward zero as crowded cusps are removed (it goes -0.00636 → -0.00438 → -0.00449 across the 10/15/20-day thresholds) — and Mercury has **no** cusps at all that are isolated by 35 days, so the headline isolation threshold cannot be evaluated for it.

The honest summary is that the local-randomization figure is the most credible number available for Mercury given that the primary design failed its own checks — not that the discrepancy between the two has been explained. The cause of the placebo over-rejection and the density discontinuities remains **undiagnosed**.


### Exploratory — the Sun

H1-Su was dropped from the confirmatory family at GATE 1 because Ptolemy *Tetrabiblos* IV.4 assigns occupational signification to Mercury, Venus and Mars only, and gives the Sun none (see `analysis/hypotheses.py`). Solar cusps were nonetheless estimated with the pre-registered h ≤ 7 cap: mean |t| across the 36 solar cusp × outcome fits was 0.74, consistent with noise.


## Study 2 — Mercury retrograde and daily event rates

Daily series: 9,132 days (2000-01-01 to 2024-12-31), 159,638,862 flights, 85 retrograde periods.

Primary inference is the circular block permutation of the whole retrograde calendar, which is exact under the null and robust to any seasonality the fixed effects miss.


**H2-a** — delay_share ~ retrograde. Regression (HAC lag 14) +0.00048 [-0.00571, +0.00666]; permutation p = .890 (10,000 shifts); TOST p = .076 → inconclusive; BF01 = 2.02 (data insensitive (not evidence of absence)). Base rate 19.30%.

**H2-b** — cancel_share ~ retrograde. Regression (HAC lag 14) -0.00220 [-0.00590, +0.00150]; permutation p = .372 (10,000 shifts); TOST p = .738 → inconclusive; BF01 = 1.09 (data insensitive (not evidence of absence)). Base rate 1.99%.

**H2-c** — delay_share ~ retrograde_shadow. Regression (HAC lag 14) +0.00308 [-0.00233, +0.00850]; permutation p = .286 (10,000 shifts); TOST p = .244 → inconclusive; BF01 = 1.49 (data insensitive (not evidence of absence)). Base rate 19.30%.

**H2-c-cancel** — cancel_share ~ retrograde_shadow. Regression (HAC lag 14) +0.00085 [-0.00275, +0.00444]; permutation p = .796 (10,000 shifts); TOST p = .467 → inconclusive; BF01 = 1.29 (data insensitive (not evidence of absence)). Base rate 1.99%.

**The Beta-Binomial recipe, and why it is not the primary Bayes factor.** Plan §2.3 prescribes a Beta-Binomial BF for proportions, which the flight outcomes are. Computed over all 159,638,862 flights it gives BF01 = 0.247 for delays and 0 for cancellations — apparently overwhelming evidence *against* the null. **That reading would be wrong**, and the numbers show why:
- Delays: 19.632% during retrograde vs 19.668% otherwise — a difference of -0.036 percentage points.
- Cancellations: 1.809% vs 1.994% — -0.186 percentage points, i.e. **fewer** cancellations during retrograde, the opposite of the prediction.

These differences are trivial in size and one is the wrong sign. The enormous Bayes factors come from pseudo-replication: the 2×2 table treats 159,638,862 flights as independent when the effective sample is 9,132 days, and it discards the day-of-week, holiday, month and year structure that the primary model conditions on. This is precisely why plan §3 makes the circular block permutation — which operates on days and preserves the calendar's block structure — the primary inference. The Beta-Binomial values are reported for completeness against §2.3 and should not be read as evidence for a retrograde effect. Robustness across priors (uniform / Jeffreys / Beta(2,2)) changes nothing: 0.247 / 0.308 / 0.261.


**H2-d (secondary)** — log(VIX) +0.00759 [-0.02856, +0.04375], permutation p = .875, N = 6,309 trading days.

## Study 3 — sun sign, sociability, and self-attribution

GSS cumulative file, 39,125 respondents with a valid sign and the sociability composite.

**H3-a (main effect).** d = +0.0101, 95% CI [-0.0143, +0.0344], p = .417, N = 39,125 (6,337 PSU clusters). TOST against d = 0.1: p < .001 → **equivalent**. BF01 = 5.38 (moderate evidence for the null).


**H3-b (sign × belief interaction — the discriminating test).** Interaction d = -0.0124, 95% CI [-0.1311, +0.1064], p = .838, N = 5,971. TOST p = .074 → **inconclusive**. BF01 = 2.06 (data insensitive (not evidence of absence)).
  - simple slope, believers (read horoscopes): d = +0.0093 [-0.0760, +0.0946], N = 2,919
  - simple slope, non-believers: d = +0.0220 [-0.0623, +0.1064], N = 3,052

**This test is inconclusive and must not be reported as support for either theory.** The plan (§2.3) fixes in advance that a Bayes factor between 1/3 and 3 is data insensitivity, not evidence of absence; BF01 = 2.06 falls in that band. The realized N is 5,971 rather than the 8,531 the GATE 1 plan projected, because the sociability items and the belief items sit on different GSS ballot rotations — a deviation logged below.

Pre-registered replication on `astrosci`: interaction +0.0487 [-0.0525, +0.1498], p = .346, N = 5,791 — also inconclusive.


## Deviations from the GATE 1 plan

| Planned | Actual | Why |
|---|---|---|
| H1-Su in the confirmatory family (8 tests) | dropped to exploratory (7 tests) | *Tetrabiblos* IV.4 gives the Sun no occupational signification; logged in `hypotheses.py` at GATE 1 |
| Study 1 sample not explicitly restricted | restricted to people with ≥1 coded occupation | otherwise the outcome partly measures Wikidata completeness; unrestricted sample reported as a robustness variant |
| `rdrobust` default variance | HC1 | the outcome is binary and the nearest-neighbour estimator is built for continuous outcomes; HC1 measured marginally conservative |
| Study 3 moderation N ≈ 8,531 | 5,971 | sociability and belief items are on different GSS ballot rotations |
| Covariate balance incl. citizenship region | gender, birth year, notability only | `P27` was never extracted by `02_extract_wikidata.py` despite its docstring; see Gaps |
| Study 2 span 1995-01 to 2024-12 | 2000-01-01 to 2024-12-31 | BTS PREZIP returns 404 before 2000-01 |
| Fixed-effect pooling only | fixed-effect (pre-registered) plus a random-effects companion | cross-cusp heterogeneity is large (I² up to 80%), so a fixed-effect CI alone would overstate precision |
| Local-randomization estimator within ±3 days (plan §3) | omitted from the first run; added in `08_diagnostics.py` | pre-specified and decisive here — it is the estimator appropriate to a discrete running variable, and the confirmatory Study 1 claims now rest on it |
| Beta-Binomial Bayes factor for proportions (plan §2.3) | JZS-Cauchy Savage-Dickey used as the primary BF for all seven tests; Beta-Binomial reported only as a supplementary check on the Study 2 flight proportions | the plan prescribes Beta-Binomial for "proportions/discontinuities", but Study 1's estimand is a *pooled, directionally-signed* discontinuity across 16 cusps, which is not a single 2×2 table; a Cauchy prior on the pooled estimate scale is the closest faithful implementation. Study 2's outcomes *are* single proportions, so the prescribed recipe is reported there |
| No SESOI specified for the cancellation outcome | set at 0.1 pp, the delay SESOI scaled by the ratio of base rates (~2% vs ~19%) | decided at analysis time, not pre-registered; stated so the reader can discount it |
| plan.md §1.2/§2.4 still say "4 primary tests"/"8 tests" | the confirmatory family is 7 | H1-Su was dropped at GATE 1 in `hypotheses.py`; `plan.md` was not updated to match. A dated corrigendum has been appended to `plan.md` rather than editing the pre-registered text |

## Gaps and known limitations of this run

- **Citizenship region was not extracted**, so that pre-registered balance covariate is missing. The docstring of `02_extract_wikidata.py` claims it is pulled; the SPARQL query does not pull it. Re-running that stage with `P27` added would close this.
- The placebo and density failures mean Study 1's nominal inference is optimistic. The equivalence bounds it reports should be read as approximate, and the one nominally significant result (H1-Me) is most plausibly an artifact — its −10-day placebo is the same size as the real cusp effect.
- Moon sign, Ascendant, houses and aspects remain untestable without birth times (plan §6.1). A null here bounds the sign-based component of astrology only.

---

## Exploratory results

Everything in this section was **not** pre-registered and is labelled exploratory wherever it appears, per plan §2.4.

- **Water signs and emotionality (Study 3).** The GSS has no emotionality scale; `happy` is a weak proxy. b = +0.0002, p = .982, N = 59,871.
- **Omnibus test of all 12 signs on sociability.** F(11, ·) = 0.85, p = .586, N = 39,125.
- **Solar cusps (Study 1).** mean |t| = 0.74 across 36 fits.

### Tropical vs sidereal vs the actual sky (exploratory)

Ptolemy defines the signs from the equinoctial and solstitial points (*Tetrabiblos* I.10–11) — the **tropical** zodiac, which is what the confirmatory analysis used. But in his era precession had not yet separated the tropical signs from the constellations they are named after, so the text cannot discriminate between them. They are now ~24° apart, which makes this an empirical question. Three zodiacs were compared, holding the hypotheses in `hypotheses.py` fixed and varying only where the boundaries fall:

- **Tropical** — equal 30° signs from the vernal equinox.
- **Sidereal** — equal 30° signs anchored to a star. The ayanamsa is computed from Spica's actual apparent position, not from a table: 21.756° in 1850 rising to 24.128° in 2020. At J2000 the computed value is 23.8494° against the published Lahiri 23.8531° — a difference of 0.22 arcminutes, far below the one-day resolution of the birth data.
- **IAU constellations** — the real, unequal boundaries (Delporte 1930, B1875), including **Ophiuchus**, an ecliptic constellation with no astrological sign at all. Ophiuchus forms one side of the nearest cusp for 11.3% of Mercury births; those cusps carry no dignity prediction and are excluded from pooling.

Estimated with the local-randomization estimator, for the reason established above.

| Planet | Zodiac | Estimate [95% CI] | Randomization p | Rules out | N |
|---|---|---|---|---|---|
| Mercury | tropical | +0.00017 [-0.00181, +0.00214] | = .867 | OR > 1.012 | 599,417 |
| Mercury | sidereal | +0.00016 [-0.00180, +0.00213] | = .873 | OR > 1.012 | 604,326 |
| Mercury | iau | +0.00071 [-0.00112, +0.00255] | = .442 | OR > 1.015 | 706,875 |
| Venus | tropical | +0.00098 [-0.00014, +0.00209] | = .074 | OR > 1.063 | 380,406 |
| Venus | sidereal | -0.00066 [-0.00174, +0.00043] | = .244 | OR > 1.052 | 384,881 |
| Venus | iau | -0.00064 [-0.00167, +0.00038] | = .228 | OR > 1.050 | 441,874 |
| Mars | tropical | +0.00017 [-0.00054, +0.00089] | = .647 | OR > 1.110 | 208,574 |
| Mars | sidereal | -0.00043 [-0.00115, +0.00029] | = .235 | OR > 1.147 | 207,355 |
| Mars | iau | -0.00081 [-0.00148, -0.00014] | = .020 | OR > 1.196 | 244,725 |

**No zodiac outperforms the others.** Across all 9 zodiac × planet tests, 1 reached p < .05 against 0.5 expected by chance — and the pre-registered placebo battery rejects at 11.4% on cutoffs that are known to be meaningless, which is the rate any 'winner' here would have to beat. The single test below .05 (Mars under IAU boundaries) is in the direction **opposite** to the astrological prediction, so it is not support for the sidereal or constellational reading either.

A caution that applies specifically to this comparison: sidereal cusps sit ~24° from tropical ones, which for the Sun is ~24 days — close to the ±20-day placebo cutoffs of plan §4.2. A sidereal or constellational 'win' is therefore about as likely to be noise as signal, which is why each zodiac is reported against the placebo rate rather than ranked against the others in isolation. See `figures/fig8_zodiac_variants.png`.
- **Isolated-cusp re-estimation (Study 1).** See the diagnostics table above; this is a post-hoc response to a failed pre-registered check, and is exploratory by construction.

## Figures

- `figures/fig1_equivalence.png`
- `figures/fig2_study1_forest.png`
- `figures/fig3_study1_placebo.png`
- `figures/fig4_study1_mercury_rd.png`
- `figures/fig5_study2_permutation.png`
- `figures/fig6_study3_signs.png`
- `figures/fig7_estimator_comparison.png`
- `figures/fig8_zodiac_variants.png`
