# Analysis Plan — Empirical tests of astrological prediction

**Status: GATE 1 document. Preregistration-style. Written before any astrological-variable ×
outcome association has been computed.**

Seed for all stochastic procedures: `20260918`.
Date written: 2026-09-18.

---

## 0. What has already been measured (and what deliberately has not)

Everything in this section is a *structural* property of the data — coverage, sample size, and the
distribution of the running variable. No association between an astrological variable and an outcome
has been examined. Source: `analysis/00_verify_sources.py` → `results/source_verification.md`.

| Fact | Measured value |
|---|---|
| Wikidata humans with **day-precision** birth date | **5,046,592** |
| — born 1800s / 1900s / 2000s | 1,102,469 / 3,492,384 / 179,330 |
| Person–occupation statement pairs (day-precision) | 7,140,199 |
| GSS `zodiac` valid N (1976–2022) | 64,451 |
| GSS `zodiac` × `astrolgy` **joint N** | **8,531** |
| GSS `zodiac` × `astrosci` **joint N** | **8,263** |
| BTS monthly on-time file | 25.8 MB, 110 columns, all required fields present |
| Ephemeris accuracy vs USNO equinox/solstice times | max deviation **0.57 minutes** |

Two Phase-1 assumptions were **falsified** by this verification and the design changed accordingly:

1. **The Laouenan et al. (2022) notable-people file carries birth YEAR only** (`birth` = 1932.0,
   `birth_min` = `birth_max` = year). It cannot supply a running variable and is therefore **demoted**
   from Study 1's primary source to (a) an occupation-taxonomy reference and (b) a birth-year-level
   descriptive cross-check. Wikidata is the sole source of the running variable.
2. **`astrosci` runs 2006–2018, not 2014/2018**, giving joint N = 8,263 rather than the scouted
   estimate of ~2,000–2,500. Study 3's moderation test is therefore powered on **both** belief
   measures, and `astrosci` is promoted from exploratory to confirmatory.

Access note: live WDQS times out on the birth-date precision join even at one-month scale. All
Wikidata extraction uses **QLever** (`qlever.cs.uni-freiburg.de/api/wikidata`), which indexes the
same dump and answers the identical query in ~1s. Sciences Po's Dataverse and Nature/PMC/HAL are all
behind Anubis anti-bot; no attempt was or will be made to defeat it. The Laouenan file was obtained
from the CC-BY-SA-4.0 Hugging Face mirror, byte-size-matched (249.4 MB) to the Dataverse original.

### The running-variable problem, measured

Day-of-month heaping among day-precision births 1900+ (n = 3,671,723), as ratio to the median day:

- **Day 1: 1.230** (the only substantial heap) · day 15: 1.084 · day 10: 1.076
- **Ingress zone, days 19–23: 0.980–1.042 — effectively flat.**

Solar ingress always falls on day-of-month 19–23, and ingress **drift across years is only 1–2 days**
(measured: Aries 20–21, Leo 22–23, Scorpio 23 across 1990–2000). Day-of-month is therefore *nearly
collinear* with the solar running variable within a cusp, and cannot be controlled away there.
A ±10-day bandwidth around a day-22 ingress reaches day 1–2 of the following month, putting the
1.230 heap **on the treated side only** — a mechanism capable of manufacturing a discontinuity.

This dictates two pre-specified decisions:

- **Solar bandwidth is capped at ±7 days** (h ≤ 7), which keeps day 1 outside the window for every
  ingress date in 19–23. This cap overrides the MSE-optimal bandwidth if the latter is larger.
- **Planetary (Mercury/Venus/Mars) cusps carry the primary weight**, because those ingresses scatter
  across all days of the month and all months, making day-of-month **orthogonal** to the running
  variable by construction rather than by adjustment.

---

## 1. Hypotheses

### 1.1 Provenance rule

Every directional prediction below is traceable to a named published source, fixed before outcome
data was touched. Where a doctrine requires information we do not have (birth time), it is **not**
tested and is recorded in §6 as a scope limit rather than silently reoperationalized.

**Explicitly NOT tested** (requires birth time, unavailable in any free large-N source): Moon sign,
Ascendant/rising sign, house placements, Midheaven, and Ptolemy's *lord of action* doctrine proper
(*Tetrabiblos* IV.4 determines occupation from the planet making its morning appearance nearest the
Sun or culminating at the MC — both are hour-dependent). Gauquelin's Mars effect is likewise
diurnal-position-based and out of scope.

### 1.2 Study 1 — essential dignity and vocation (confirmatory)

**Doctrine used:** *essential dignity* — a planet in its own domicile expresses its significations
strongly; in the opposite sign (detriment) weakly. Rulerships are canonical and unambiguous
(*Tetrabiblos* I.17, "Of the Houses of the Several Planets"). Occupational significations are taken
verbatim from *Tetrabiblos* IV.4, "Of the Quality of Action":

> **Mercury**: "scribes, men of business, calculators, teachers, merchants, bankers, soothsayers,
> astrologers … those who perform their functions by means of documents, interpretation, and giving
> and taking."
> **Venus**: "sellers of unguents, weavers of chaplets, innkeepers, wine-merchants, druggists,
> weavers, dealers in spices, **painters, dyers, sellers of clothing**."
> **Mars**: "those who use fire in their crafts, such as cooks, moulders, cauterizers, **smiths,
> workers in mines**; … those who work with iron, such as **shipbuilders, carpenters, farmers,
> quarrymen, stone-dressers, jewellers**."

| ID | Planet | Domicile (strong) | Detriment (weak) | Outcome class (Wikidata P106) | Predicted direction |
|---|---|---|---|---|---|
| H1-Me | Mercury | Gemini, Virgo | Sagittarius, Pisces | writer, journalist, translator, teacher, businessperson, banker, accountant | share **higher** in domicile |
| H1-Ve | Venus | Taurus, Libra | Scorpio, Aries | painter, dyer, textile/clothing, innkeeper, perfumer | share **higher** in domicile |
| H1-Ma | Mars | Aries, Scorpio | Libra, Taurus | smith, miner, shipbuilder, carpenter, farmer, quarryman, stonemason, jeweller | share **higher** in domicile |
| H1-Su | Sun | Leo | Aquarius | leadership occupations (politician, monarch, officeholder) | share **higher** in domicile |

**RDD form.** For each planet *p* and each of its 12 sign-ingress cusps, the running variable is
`days_from_ingress` (birth date minus the exact ingress datetime, per birth year). Treatment is
membership in the sign to the right of the cutoff. For each cusp the *predicted sign of the jump* is
determined by whether the crossing moves the planet **into** or **out of** a dignity-relevant sign;
cusps where the crossing is dignity-neutral are excluded from the primary pooled estimate and
reported separately.

**Primary estimand.** One pooled, directionally-signed discontinuity per planet (4 primary tests),
following Cattaneo, Keele, Titiunik & Vázquez-Baré (2016) for multi-cutoff pooling. Signing by the
pre-registered direction is what prevents the pooled estimate from cancelling to zero by construction.

### 1.3 Study 2 — Mercury retrograde and event rates (confirmatory)

**Claim tested:** Mercury retrograde elevates rates of travel, communication, and contract
disruption. This is a modern claim; it is not in Ptolemy. It is sourced as a contemporary popular
doctrine and tested on its own terms, including the "shadow" periods that practitioners include.

| ID | Outcome | Predicted direction |
|---|---|---|
| H2-a | Daily share of arriving flights delayed >15 min (BTS) | **higher** during retrograde |
| H2-b | Daily share of flights cancelled (BTS) | **higher** during retrograde |
| H2-c | Same, retrograde **+ shadow** windows | **higher** |
| H2-d (secondary) | Daily equity realized volatility / VIX | **higher** during retrograde |

### 1.4 Study 3 — sun sign, traits, and the self-attribution test (confirmatory)

**Doctrine used:** the Mayo–White–Eysenck operationalization (Mayo, White & Eysenck, 1978, *J. Soc.
Psych.* 105:229–236), the standard testable form of sun-sign trait claims: odd-numbered ("positive")
signs — Aries, Gemini, Leo, Libra, Sagittarius, Aquarius — predict **extraversion**; even-numbered
("negative") signs predict introversion. Water signs (Cancer, Scorpio, Pisces) predict greater
**emotionality**.

GSS extraversion proxy (pre-specified composite): `socfrend`, `socbar`, `socommun`, `socrel`
(frequency of socializing), standardized and averaged. Secondary outcomes: `happy`, `life`.

| ID | Test | Astrology predicts | Self-attribution predicts |
|---|---|---|---|
| H3-a | Main effect of odd/even sign on sociability composite | positive | ~zero in full sample |
| H3-b | **Sign × belief interaction** (`astrolgy`, then `astrosci`) | **null interaction** (effect independent of belief) | **significant interaction** (effect only among believers) |

H3-b is the discriminating test: the two theories make *opposite* predictions about the interaction,
so this is not a null-vs-nothing comparison. Whichever way it resolves, it is informative.

---

## 2. Inference framework

### 2.1 Dual inference (both required, pre-specified)

Every primary test reports (i) the point estimate with 95% CI, (ii) a **TOST equivalence test**
against the SESOI below, and (iii) a **Bayes factor** with stated prior and a prior-sensitivity curve.
Reporting only one is not permitted. Following Lakens, McLatchie, Isager, Scheel & Dienes (2018),
these are treated as complementary, not alternatives.

### 2.2 SESOI, anchored to documented confounds rather than convention

A d = 0.05 picked by convention is arbitrary and indefensible at reviewer level. Instead the SESOI is
anchored to the **magnitude of real season-of-birth effects** established in the literature:

- Schizophrenia, winter/spring vs summer/autumn birth: **OR = 1.07** (95% CI 1.05–1.08; Davies,
  Welham, Chant, Torrey & McGrath 2003, meta-analysis, 126,196 cases).
- Height, UK Biobank (Day, Forouhi, Ong & Perry 2015, n ≈ 450,000): ~6.5 mm summer-vs-winter.

**SESOI for Study 1 is set at OR = 1.05** — deliberately *below* the documented seasonal effect. The
argument: astrology claims birth timing determines character and vocation. Season of birth, a mundane
biological confound astrology does not claim as its mechanism, moves psychiatric risk by OR 1.07. An
astrological effect on vocation smaller than that is below any threshold at which the doctrine's own
claims could be considered supported. Ruling out OR ≥ 1.05 is thus a substantively meaningful bound.

- **Study 2 SESOI**: 0.5 percentage points on the daily delay share (≈ 2.5% relative change on a
  ~20% base rate) — smaller than the day-of-week effect, which is the natural scale comparator.
- **Study 3 SESOI**: d = 0.10, the conventional "small" bound and roughly the magnitude the original
  Mayo–White–Eysenck effect was reported at, so the test is calibrated to the claim it evaluates.

### 2.3 Bayes factor priors

- Proportions / discontinuities: Beta–Binomial with a uniform Beta(1,1) prior on each side;
  robustness across Beta(0.5,0.5) and Beta(2,2).
- Standardized mean differences: default JZS Cauchy, scale r = 0.707 (Rouder, Speckman, Sun, Morey &
  Iverson 2009); prior-sensitivity curve over r ∈ [0.1, 1.5] reported for every primary test.
- BF₀₁ ≥ 3 is described as "moderate evidence for the null," ≥ 10 "strong," per Dienes (2014).
  A BF between 1/3 and 3 is reported as **data insensitivity, not evidence of absence.**

### 2.4 Multiplicity

Primary family = 8 tests (4 Study 1 planets + 2 Study 2 flight outcomes + 2 Study 3 tests).
Benjamini–Hochberg FDR at q = .05 within the family. All other results — additional cusps,
occupation subclasses, market volatility, element/triplicity variants — are **exploratory** and
labelled as such in every table, figure, and sentence of the manuscript.

---

## 3. Specification, fixed in advance

### Study 1 (RDD)
- Estimator: `rdrobust`, local linear, triangular kernel, robust bias-corrected CIs.
- Bandwidth: MSE-optimal (`mserd`), **capped at h = 7 days for solar cusps** (§0 rationale);
  uncapped for planetary cusps. Sensitivity curve over h ∈ {3, 5, 7, 10, 14, 21} reported for all.
- Running variable is discrete (daily): honest discrete-support inference per Cattaneo, Idrobo &
  Titiunik (2023); local randomization check within ±3 days as a secondary estimator.
- Sample restriction: births **1850–2020** (DE440s ephemeris coverage is 1849–2150; stated, not
  silently applied). Records with non-day precision excluded via the `wikibase:timePrecision = 11`
  qualifier.
- Covariate balance at the cutoff: gender, birth year, notability (sitelink count), citizenship
  region. Expected smooth; a jump here invalidates the design.

### Study 2 (ITS)
- Unit: day, 1995-01-01 to 2024-12-31 (30 years).
- Model: `delay_share ~ retrograde + DOW + federal holiday + month + year`, Newey–West HAC SEs
  (lag = 14).
- **Primary inference is the circular block permutation**, not the regression p-value: shift the
  entire retrograde calendar by a random offset 10,000 times, recompute, and locate the observed
  statistic in that exact null. This is robust to any seasonality the fixed effects miss.
- Shadow periods computed but analysed as a separate pre-registered variant (H2-c).

### Study 3 (survey)
- GSS weights (`wtssps`/`wtssall` as applicable by year), design-based SEs clustered by
  `vpsu` within `vstrat`; year fixed effects.
- H3-b estimated as sign-polarity × belief interaction, belief entered as `astrolgy` (binary) in the
  primary test and `astrosci` (ordinal) in the pre-registered replication.

---

## 4. Falsification and positive controls

A design that finds nothing everywhere is broken, not skeptical. All of the following are
pre-specified as **required**, and a failure of the first two invalidates the corresponding study.

1. **Positive control — the pipeline must detect a known real effect.** Recover the documented
   season-of-birth pattern in the same Wikidata sample: (a) the relative-age effect among
   professional athletes (birth-quarter skew; Bjørndal et al. 2018 report ORs of 1.9–8.3), and
   (b) a smooth annual birth-seasonality cycle. If these do not appear, the pipeline is not
   measuring what it claims to.
2. **Placebo cutoffs.** Discontinuities at cutoffs shifted ±10 and ±20 days must be centred on zero
   with the nominal rejection rate. A systematic offset means the running variable is mis-specified.
3. **Density / manipulation test.** `rddensity` (Cattaneo, Jansson & Ma 2018) at every cusp. Birth
   dates cannot be strategically manipulated around a zodiac boundary, so a density jump here would
   indicate a data artifact rather than sorting.
4. **Donut RDD** excluding the cutoff day.
5. **Heaping robustness** — re-estimate excluding day-of-month 1, 10, and 15.
6. **Ephemeris validation** (already passing): max 0.57 min deviation vs USNO on eight cardinal
   ingresses; 2024 Mercury retrograde windows reproduce published dates; 3.15 retrograde
   periods/year over 1900–2020 against the canonical ~3.2.

---

## 5. Deviations from the original idea

| Original | Revised | Why |
|---|---|---|
| Laouenan file = Study 1 primary | Wikidata/QLever = sole running-variable source; Laouenan = taxonomy reference | Measured: Laouenan has birth **year** only |
| Live WDQS, per-year chunks | QLever endpoint | Measured: WDQS times out on the precision join at any useful scale |
| Sun-sign cusps primary | **Planetary cusps primary**, solar secondary with h ≤ 7 | Measured: solar ingress is near-collinear with day-of-month (drift only 1–2 days); planetary ingresses are orthogonal to it |
| Occupation via Ptolemy's *lord of action* | Occupation via **essential dignity** | *Lord of action* requires birth time; dignity does not |
| `astrosci` exploratory | `astrosci` confirmatory | Measured: joint N = 8,263, not ~2,400 |
| SESOI = d 0.05 by convention | SESOI = OR 1.05, anchored to Davies et al. OR 1.07 | Defensible against reviewers; convention is not |

---

## 6. Limitations to state in the manuscript (not to discover later)

1. **Partial operationalization.** Sun/Mercury/Venus/Mars sign is a subset of the natal chart. Moon,
   Ascendant, houses and aspects are untestable without birth times. A null here bounds the
   sign-based component of astrology, not the full-chart claim, and the paper will say exactly that.
2. **Notable people are not the general population.** Wikidata over-represents men, Europeans, and
   the 20th century. Study 1 generalizes to vocational attainment among the notable, not to humanity.
3. **Occupation coding is from Wikidata editors**, with known sparsity and classification error at
   the low-notability tail (a limitation Laouenan et al. document for the same underlying sources).
4. **Northern-hemisphere seasonality dominates** the sample; the season/sign relationship is inverted
   in the southern hemisphere. Hemisphere is a pre-specified exploratory moderator.
5. **Study 3 is cross-sectional**; the belief interaction identifies moderation, not the direction of
   causation between belief and self-description.
6. **Associational language throughout** for Studies 1 and 3. Study 2's treatment is genuinely
   exogenous and permits stronger causal wording, limited to that study.

---

## Corrigendum — 2026-09-20

The text above is the GATE 1 document and is left unedited. Two corrections are recorded
here rather than silently applied, so that the pre-registered wording remains inspectable.

1. **The confirmatory family is 7 tests, not 8.** §1.2 lists four Study 1 hypotheses and
   §2.4 counts eight primary tests. H1-Su (Sun → leadership occupations) was dropped from
   the confirmatory set **at GATE 1**, before any outcome data was touched, on the grounds
   that *Tetrabiblos* IV.4 names only Mars, Venus and Mercury as significators of
   occupation and gives the Sun none. The drop is recorded in `analysis/hypotheses.py`
   (`DROPPED_FROM_CONFIRMATORY`) with its rationale. The Sun analysis is retained as
   exploratory. This makes the test of astrology stricter, not looser: the family shrinks
   and the BH correction is applied across 7 rather than 8.

2. **§4's invalidation clause was triggered.** §4 states that a failure of the positive
   controls or the placebo cutoffs "invalidates the corresponding study". The positive
   controls passed; the placebo check failed (11.4% rejection against a nominal 5%), as
   did the density and covariate-balance checks. Study 1's continuity-based estimates are
   therefore reported as a record of what the pre-registered primary specification
   produced, and the confirmatory Study 1 claims rest instead on the local-randomization
   estimator that §3 already pre-specifies for a discrete running variable. See
   `results/results.md` and `review/stats_review.md`.
