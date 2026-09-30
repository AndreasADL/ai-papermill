# Literature Review — Empirical Tests of Astrological Prediction

Scope: supports the three-study design in `idea.md` (zodiac-cusp RDD, Mercury-retrograde ITS,
GSS belief-moderation survey). Sources: OpenAlex, Semantic Scholar, and Crossref APIs, queried
2026-09-18, plus one WebSearch used only to locate the correct title of Dean & Kelly (2003), which
was then independently confirmed in OpenAlex/Crossref. Full text was not read for any paper —
characterizations below are based on API-returned titles/metadata and AI-summarized abstract
content, which is noted wherever it matters. All 36 references with a resolvable DOI are in
`references.bib`; one paper referenced below (Dean & Kelly, 2003) has no DOI in any of the three
APIs and is therefore *not* in `references.bib`, per the no-invented-citation rule — see the note
at the end of §1.

---

## 1. Prior empirical tests of astrology

**Carlson (1985)** — double-blind natal-chart matching [Carlson, 1985, 10.1038/318419a0]. Confirmed
in OpenAlex and Crossref, DOI redirect spot-checked (302 → nature.com). Design: astrologers matched
natal charts to CPI personality profiles under blinding; astrologers' pre-registered success
criterion was not met, and match rates did not exceed chance. This is a bare non-significance
result — no equivalence bound or Bayes factor. N and exact design details beyond this were not
re-derived from the primary text (abstract/metadata only).

**Wyman & Vyse (2008)** [10.3200/genp.135.3.287-300] replicated Carlson's logic with NEO-FFI
profiles and computer-generated natal-chart interpretations; again, no evidence participants could
match their own chart to their profile above chance. Bare null again, no equivalence framing.

**Dean & Kelly (2003)** — "Is astrology relevant to consciousness and psi?", *Journal of
Consciousness Studies* 10(6-7):175-198. **Verification status:** confirmed to exist via OpenAlex
(ID `W2106724377`, 24 citations, correct year/venue/authors) and via a targeted WebSearch that
surfaced the exact citation and a Skeptical Inquirer summary. **However, no DOI is present in
OpenAlex or Crossref** — likely because Imprint Academic did not retroactively register DOIs for
JCS issues from that era.

**Status updated 2026-09-20: this paper is now IN `references.bib` (key `DeanKelly2003`) and is
cited in the manuscript.** It was originally excluded under a rule requiring a resolving DOI. That
exclusion was too strict: a missing DOI is a fact about a publisher's registration practices, not
evidence that a paper is fabricated, and the rule was discarding the single most relevant prior
study. The entry is instead verified two ways — against OpenAlex work `W2106724377` (title, year,
authors, venue, ISSN and volume all matching) and against publisher metadata from IngentaConnect
supplied by the user, which adds the issue number (6–7) and page range (175–198). The citation
checker (`analysis/10_verify_citations.py`) was extended to verify DOI-less entries against
OpenAlex by title and year, and reports them distinctly, so the weaker check is visible rather than
hidden. Based on the secondary summary (not the primary text): the study used the UK
National Child Development Study "time twins" — pairs of children born within minutes of each
other in the same UK week in March 1958 (N in the thousands) — and compared ~100+ variables
(ability, occupation, personality, physical traits) measured at ages 11, 16, and 23. It found no
increase in twin-similarity even among pairs born within 45, 30, or 15 minutes of each other,
despite increasingly similar natal charts at tighter windows. This is the strongest design in the
"prior tests" literature for our purposes (a dose-response test on chart similarity), but again
reports a bare null rather than a quantified equivalence bound. **We could not independently verify
the N, the exact variable list, or the sub-window analysis from a primary source; treat these
design details as provisional** pending full-text access, which is out of scope for this API-only
scan.

**Hartmann, Reuter & Nyborg (2006)** [10.1016/j.paid.2005.11.017], *Personality and Individual
Differences* 40(7):1349-1362. Large-scale (idea.md states N>14,000; consistent with the paper's
description as "large-scale") test of date-of-birth-derived astrological variables against Big
Five personality and general intelligence. Reported null associations. Only the indexed
title/venue/metadata was reviewed via OpenAlex; the abstract text itself was not retrievable
verbatim through the API calls made in this session, so the specific effect-size point estimates
in the paper are not independently confirmed here — flagged as a gap.

**van Rooij (1999)** [10.2466/pr0.1999.84.2.541]. N=422 (308 women, 114 men); self-report ratings
on 96 astrology-derived traits. Central finding: sign-congruent self-description held **only**
among respondents with some astrological knowledge — direct empirical support for the
self-attribution mechanism that Study 3 is designed to isolate.

**Chico & Lorenzo-Seva (2006)** [10.2466/pr0.99.3.851-863]. Belief in Astrology Inventory,
validated in N=743 Spanish undergraduates; small but significant belief–extraversion correlation,
higher belief in women. Useful as an instrument-validation precedent (not a trait-accuracy test).

**Recent (2015+) large-N studies located:**
- **Edwards, March, Willoughby & Giannelis (2025)** [10.1027/1614-0001/a000434], N=8,553 US GSS
  respondents: intelligence is the strongest (negative) predictor of *belief* in astrology. This
  tests belief formation, not sign-trait accuracy — relevant to Study 3's mechanism question, not
  to Study 1's trait-accuracy question.
- **Andersson, Persson & Kajonius (2021)** [10.1016/j.paid.2021.111389], N=264: narcissism is the
  strongest predictor of astrological belief. Small N; belief, not accuracy.
- **Helgertz & Scott (2020)** [10.1186/s41118-020-00103-5], *Genus*: uses full-population Swedish
  register data (1968-2001) to test whether astrologically "compatible" sun-sign couples marry more
  or divorce less. **This is the best genuine large-N (population-scale), pre-registered-style
  trait/compatibility test we found**, and it still reports a bare null ("fail to provide any
  consistent evidence") rather than an equivalence bound.

**Meta-analyses of astrology tests — CORRECTED 2026-09-20.** The original scan reported that none
were found, on the basis that a dedicated OpenAlex query ("astrology meta-analysis empirical test")
returned no on-topic results in the top 10. **That conclusion was wrong.** Dean & Kelly (2003)
contains a meta-analysis of more than forty controlled studies of astrologer performance, finding
that astrologers do not exceed chance even on comparatively basic tasks including the prediction of
extraversion, and that astrologers claiming psychic ability perform no better than those who do
not. The meta-analysis was missed because the paper is indexed without an abstract or a DOI and its
title does not contain the word "meta-analysis". The lesson is that a title/metadata-only search
strategy will miss syntheses that are embedded in papers not framed as reviews.

What survives of the original claim is narrower and still holds: **no astrology meta-analysis
reports a quantified equivalence bound.** Dean & Kelly conclude qualitatively that astrological
influences, if they exist, "would seem to be very weak or very rare" — which is a stronger and more
careful statement than a bare *p* > .05, but is still not an effect size that has been excluded.

**The documented gap:** across every trait-accuracy paper located (Carlson 1985, Wyman & Vyse
2008, Dean & Kelly 2003 [caveated], Hartmann et al. 2006, Helgertz & Scott 2020), the reported
result is a bare non-significant p-value or a qualitative "no consistent evidence" statement.
**None of them quantify what effect size is ruled out** (no TOST/SESOI, no Bayes factor). This is
exactly the contribution gap the idea.md inference framework (equivalence bound + Bayes factor)
is designed to fill.

---

## 2. The season-of-birth confound

This section establishes that season/month-of-birth effects on real outcomes are well-documented,
smooth, and large enough in some domains to matter — which is the mechanism Study 1's RDD is
designed to net out by comparing across a sharp sign-cutoff rather than across season generally.

**Psychiatric outcomes (schizophrenia):**
- **Davies, Welham, Chant, Torrey & McGrath (2003)** [10.1093/oxfordjournals.schbul.a007030],
  *Schizophrenia Bulletin*: meta-analysis of 27 Northern Hemisphere studies (126,196 patients vs.
  86.6M general-population births). Pooled **OR = 1.07 (95% CI 1.05–1.08)** for winter/spring vs.
  summer/autumn birth; effect magnitude correlates with latitude (r=0.271, p<.005); ~3.3%
  attributable risk.
- **McGrath & Welham (1999)** [10.1016/s0920-9964(98)00139-x]: Southern Hemisphere companion
  meta-analysis, broadly mirrored (calendar-shifted) pattern — evidence against a fixed-calendar
  artifact and for a genuine seasonal/biological mechanism.
- **Mortensen et al. (1999)** [10.1056/nejm199902253400803], NEJM: Danish population register,
  1.75M persons / 2,669 cases; risk highest for Feb–Mar births, lowest Aug–Sep; effect independent
  of family history; ~5.5% population-attributable risk.

**Relative age effects — sport selection:**
- **Smith, Weir, Till, Romann & Cobley (2018)** [10.1007/s40279-018-0890-8], *Sports Medicine*:
  systematic review/meta-analysis across female sport contexts; magnitude is sport-context
  dependent but the underlying birth-quarter selection skew is a robust, repeatedly replicated
  phenomenon.
- **Bjørndal, Luteberget, Till & Holm (2018)** [10.1371/journal.pone.0209288], *PLoS ONE*: 657
  Norwegian handball players; birth-quartile odds ratios for international-team selection ranging
  **1.9–8.3**.

**Relative age effects — education / school-entry cutoffs:**
- **McEwan & Shapiro (2008)** [10.1353/jhr.2008.0021], *Journal of Human Resources*: RDD on exact
  birth dates around a Chilean school-entry cutoff. One year of delay lowers first-grade repetition
  by ~2pp and raises 4th/8th-grade scores by >0.3 SD. **Methodologically important as a precedent
  for exact-birth-date RDD**, independent of the astrology application.
- **Cornelissen & Dustmann (2019)** [10.1257/pol.20170641], *AEJ: Economic Policy*: English
  school-entry-rule RDD; cognitive benefits at age 7 mostly dissipate by 11, noncognitive benefits
  persist.

**Multi-outcome UK Biobank evidence (height, puberty, education):**
- **Day, Forouhi, Ong & Perry (2015)** [10.1016/j.heliyon.2015.e00031], *Heliyon*: ~450,000 UK
  Biobank participants. Summer-born adults are taller than winter-born by **~6.5mm (P=8×10⁻⁹)**;
  season of birth is also independently associated with birth weight, pubertal timing, and
  educational attainment. This is the single most useful confound paper located: huge N, multiple
  outcomes, smooth-in-birth-date pattern — exactly the kind of effect our RDD is built to
  distinguish from a genuine cusp discontinuity.

**Longevity:**
- **Gavrilov & Gavrilova (2011)** [10.4061/2011/104616], *Journal of Aging Research*: 1,574
  validated US centenarians (b. 1880–1895) vs. 10,885 shorter-lived siblings and 1,083 spouses,
  family-based design; Sept–Nov birth associated with higher odds of reaching age 100 than March
  birth, with a similar pattern in spouses (arguing against a purely genetic explanation).

**Myopia — gap.** We ran a dedicated search ("season of birth myopia," "month of birth myopia
school children," "relative age effect myopia class cohort") and did **not** surface a verifiable,
on-topic record via OpenAlex in the top results returned. This is a genuine search gap, not a
claim that no such literature exists — a more targeted follow-up (e.g., searching specific known
authors, or using PubMed/Semantic Scholar with different term combinations) would be needed before
citing a season-of-birth/myopia effect size in the paper. **We are not including a myopia citation
in this review**, in keeping with the rule against filling gaps with unverified claims.

**Bottom line for Study 1:** the season-of-birth confound is real, multi-domain, and — critically —
smooth in birth date (Day et al. 2015; Mortensen et al. 1999 show gradual monthly gradients, not
jumps). This directly supports the RDD logic: a smooth confound predicts a smooth outcome function
through the cusp, so a discontinuous jump at the zodiac boundary cannot be attributed to
seasonality.

---

## 3. Mercury retrograde empirical tests

**Direct tests found:**
- **Qi, Wang & Zhang (2022)** [10.2139/ssrn.4074620], SSRN preprint (not peer-reviewed): "Cultural
  Beliefs and Equity Prices: Evidence from Astrological Belief in Mercury Retrograde." Full
  abstract text was not retrievable through the API metadata calls made; authors are affiliated
  with CSU Long Beach, Jinan University/UNSW, and CUHK-Shenzhen. **Status must be reported plainly
  as an unreviewed preprint**, not a validated finding.
- **Konak & Özkahveci (2022)** [10.33437/ksusbd.1133074]: EGARCH volatility modeling of Mercury
  retrograde windows (2008–2021) against BRICS + Turkish equity indices. Mixed/weak results
  (positive, significant effect for China and South Africa indices; negative and non-significant
  for Turkey, Brazil, Russia, India); BIST 100 findings consistent with weak-form market
  efficiency. **No permutation or exact-null approach was used** — standard GARCH-family
  significance testing only.
- Several additional Mercury-retrograde/astro-finance papers were found in non-mainstream or
  practitioner-oriented venues (e.g., Indonesian and Turkish engineering/finance journals using
  "Astronacci," deep-learning, or backtesting approaches). These were **excluded from the formal
  reference list** as too methodologically thin (no significance testing, backtesting without
  out-of-sample validation, or predatory-adjacent venues) to serve as evidence either way. Their
  existence is noted here only to flag that the astro-finance literature is dominated by
  low-rigor venues, which is itself a relevant observation for framing Study 2's contribution.

**IT incidents / transport / accident rates — gap.** A dedicated search ("Mercury retrograde
accidents IT incidents transportation") returned **zero on-topic results** in OpenAlex. We found
no peer-reviewed literature at all testing Mercury retrograde against IT outages, flight delays, or
accident rates. **This appears to be a genuine, near-total gap in the literature** — Study 2's
flight-delay outcome is close to novel territory empirically, not merely under-replicated.

**Methodological parallels (lunar-phase / calendar-anomaly finance literature):** these are useful
design templates even though they are not about Mercury retrograde specifically.
- **Yuan, Zheng & Zhu (2006)** [10.1016/j.jempfin.2005.06.001], *Journal of Empirical Finance*:
  full/new-moon effects on stock returns, tested via regression with standard controls across
  international markets.
- **Keef & Khaled (2010)** [10.1016/j.jempfin.2010.11.002]: panel-data extension testing
  persistence of lunar effects internationally, controlling for GDP/demographic covariates.

**On permutation/exact-null designs specifically:** none of the Mercury-retrograde papers located
used a permutation or exact-null approach; they all rely on standard parametric significance
testing (regression, GARCH/EGARCH). **Study 2's planned circular block permutation of the
retrograde calendar therefore appears to be methodologically novel relative to the existing
Mercury-retrograde literature**, at least among the papers discoverable via these three APIs.

---

## 4. RDD methodology citations

- **Calonico, Cattaneo & Titiunik (2014, Econometrica)** [10.3982/ecta11757] — the core
  robust bias-corrected RD inference result (DOI resolution spot-checked, 302 → Wiley).
- **Calonico, Cattaneo & Titiunik (2014, Stata Journal)** [10.1177/1536867x1401400413] — companion
  `rdrobust`/`rdbwselect`/`rdplot` software paper.
- **McCrary (2008)** [10.1016/j.jeconom.2007.05.005] — original density-based manipulation
  ("no-sorting-at-the-cutoff") test.
- **Cattaneo, Jansson & Ma (2018)** [10.1177/1536867x1801800115] — modern local-polynomial
  density-discontinuity manipulation test (`rddensity`), improving on McCrary (2008); directly
  applicable to testing whether recorded birth dates cluster suspiciously near our 12 zodiac
  cutoffs (e.g., date heaping noted as an open item in idea.md).
- **Cattaneo, Keele, Titiunik & Vázquez-Baré (2016)** [10.1086/686802], *Journal of Politics* —
  formal treatment of RD designs with cutoffs that vary across units; derives the correct
  interpretation of the pooled effect and shows that naive score normalization can waste
  information. **Directly relevant to how we pool the 12 zodiac-cusp estimates.**
- **Cattaneo, Idrobo & Titiunik (2023)** [10.48550/arxiv.2301.08958] — practitioner-oriented
  extension guide, including multiple cutoffs and discrete running variables (our running variable,
  days from ingress, is inherently discrete/day-granular).
- **Imbens & Lemieux (2007)** [10.3386/w13039] — general RD practitioner's guide, useful for
  validity-condition framing in the methods section.

---

## 5. Null-result inference methodology

**Frequentist equivalence testing (TOST/SESOI):**
- **Lakens (2017)** [10.1177/1948550617697177] — core TOST + SESOI primer (DOI resolution
  spot-checked, 302 → SAGE).
- **Lakens, Scheel & Isager (2018)** [10.1177/2515245918770963] — tutorial-level treatment.
- **Lakens, McLatchie, Isager, Scheel & Dienes (2018)** [10.1093/geronb/gby065] — argues
  equivalence tests and Bayes factors are complementary, directly supporting our dual-inference
  plan (TOST **and** Bayes factor, not either/or).

**Bayes factors for evidence of absence:**
- **Rouder, Speckman, Sun, Morey & Iverson (2009)** [10.3758/pbr.16.2.225] — foundational default
  Bayesian t-test (JZS Bayes factor).
- **Dienes (2014)** [10.3389/fpsyg.2014.00781] — practical guidance distinguishing data
  insensitivity from genuine evidence against a theory.
- **Keysers, Gazzola & Wagenmakers (2020)** [10.1038/s41593-020-0660-4] — applied guidance,
  including prior-sensitivity checks, for establishing evidence of absence.
- **Schad, Betancourt & Vasishth (2017)** [10.3758/s13423-017-1230-y] — Bayes factor design
  analysis for planning studies likely to yield compelling (not ambiguous) evidence, relevant to
  the sample-size/sensitivity planning step in `analysis/plan.md`.

---

## Novelty check: has anyone already done this?

Two targeted searches were run specifically to test the novelty claims in `idea.md`:

1. **"Regression discontinuity zodiac astrology cusp"** (OpenAlex) → **zero results.**
2. **"Mars Venus Mercury sign planetary astrology occupation large sample"** (OpenAlex) → no
   on-topic results; closest match was an unrelated art-history paper on planetary transits as
   creative muses.

Within the coverage of OpenAlex/Semantic Scholar/Crossref, **we found no prior work using a
regression-discontinuity design at zodiac sign boundaries, and no prior large-N test using
Mercury/Venus/Mars sign (rather than sun sign) as the astrological predictor.** This supports, but
does not conclusively prove, the novelty claims for Study 1 — absence of evidence in three
keyless APIs is not proof of absence in the wider literature (e.g., non-indexed astrology-research
venues, or papers using different terminology than searched). We recommend treating "no prior RDD
at zodiac cusps" as a claim of the form "not found in OpenAlex/S2/Crossref as of 2026-09-18,"
rather than an absolute claim of first priority.

The closest **existing near-miss designs** are: Helgertz & Scott (2020) (population-register scale,
but a simple sun-sign-pair comparison, not an RDD); McEwan & Shapiro (2008) and Cornelissen &
Dustmann (2019) (exact-birth-date RDD methodology, but applied to school-entry policy cutoffs, not
zodiac cutoffs — these are the methodological ancestors of our design, not competitors to it).

---

## Gap and contribution

**What genuinely appears new here** (based on the coverage of the three APIs searched):

1. **A regression-discontinuity design at zodiac sign cusps** — no prior work found. The
   McEwan-Shapiro/Cornelissen-Dustmann exact-birth-date RDD tradition is well established in the
   education-economics literature, but it has apparently never been pointed at zodiac cutoffs
   specifically, despite zodiac cutoffs being an unusually clean natural experiment (as-good-as-
   random assignment, no policy endogeneity, no strategic manipulation incentive).
2. **Testing Mercury/Venus/Mars sign rather than only sun sign**, using exact birth date without
   birth time — no prior large-N precedent found. This operationalizes claims from actual
   astrological practice (not just pop sun-sign astrology) and adds statistical power via
   additional cutoffs.
3. **Quantifying, rather than merely reporting, the null** for trait-accuracy claims (TOST against
   a pre-specified SESOI + Bayes factor with stated priors and a prior-sensitivity check). Every
   trait-accuracy paper reviewed in §1 — including the two strongest ones, Dean & Kelly (2003) and
   Helgertz & Scott (2020) — reports a bare non-significant result or a qualitative "no consistent
   evidence" statement, not an equivalence bound. This gap is consistent across 50+ years of the
   literature (1985–2020) and is the clearest, best-supported contribution claim of the three.
4. **A permutation/exact-null design for Mercury retrograde**, exploiting the ~116-day cycle's
   misalignment with the calendar year. No Mercury-retrograde paper located used permutation
   inference; all used standard parametric tests. Combined with the near-total absence of any
   IT-incident/accident-rate literature on Mercury retrograde, Study 2's flight-delay analysis is
   close to unexplored empirical territory, not merely methodologically improved territory.

**What is NOT new, and should not be oversold:**
- The core idea that a bare sun-sign difference is confounded by season of birth is already
  implicit in the skeptical literature and explicit in the season-of-birth confound literature
  (§2); we are not the first to note this tension, only the first (within what we could verify) to
  build a design that structurally removes it via a within-day-of-year discontinuity.
- The self-attribution mechanism for Study 3 (belief moderates sign-congruent self-description) is
  an already-published finding [van Rooij, 1999, 10.2466/pr0.1999.84.2.541], not a new discovery —
  Study 3 extends it to a much larger, nationally representative sample (GSS) and a wider battery
  of outcome variables, and pits the "astrology is true" and "self-attribution" hypotheses directly
  against each other, but the underlying mechanism claim itself is a replication-with-more-power,
  not a novel theoretical contribution.
- Financial-astrology and lunar-effect testing on markets is a moderately populated (if low-rigor)
  niche literature; Study 2 is not the first to test Mercury retrograde against markets, only
  (apparently) the first to bring permutation inference to it and the first to test flight-delay/
  transport outcomes at all.

## Overall literature quality note

The literature is not uniformly thin, but it is uneven: the astrology-specific empirical tests
(§1, §3) are mostly single small-to-moderate studies (Carlson N unspecified here, van Rooij N=422,
Chico & Lorenzo-Seva N=743, Andersson et al. N=264) with a couple of large-N exceptions (Hartmann
et al. N>14,000; Helgertz & Scott population-scale; Edwards et al. N=8,553 for belief, not
accuracy). There is no meta-analysis of astrology-accuracy tests indexed in OpenAlex. By contrast,
the season-of-birth confound literature (§2) and the RDD/inference methodology literature (§4-5)
are both mature, highly cited, and internally consistent. The imbalance itself supports the framing
in `idea.md`: the astrology-testing literature is small and methodologically weak on the inference
side (bare nulls throughout), while the tools needed to do better (RDD, TOST, Bayes factors) are
mature and well-validated elsewhere — the contribution is importing rigor, not discovering new
astronomy or psychology.
