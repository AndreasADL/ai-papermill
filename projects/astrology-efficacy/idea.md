# Idea: Empirical tests of astrological prediction using public data

## Research question

Do astrological predictions have demonstrable empirical validity, and if not, **how large an
effect can be ruled out**?

Two distinct classes of astrological claim are tested separately, because they require different
identification strategies:

1. **Trait claims** — natal chart positions predict stable individual characteristics
   (temperament, aptitude, vocation).
2. **Event/forecast claims** — dated planetary configurations predict elevated rates of specific
   real-world events (Mercury retrograde → travel, communication, and contract disruption).

A third question addresses the **mechanism** behind belief persistence: are apparent sign–trait
correspondences produced by self-attribution among believers rather than by astrology?

## Why the naive design fails

The obvious study ("do sun signs differ on outcome Y?") is uninformative in both directions:

- **Confounded when positive.** Season of birth genuinely predicts schizophrenia risk, myopia,
  athletic success (relative age effects), and educational attainment (school entry cutoffs).
  A raw sun-sign difference is evidence of *seasonality*; astrology would take undeserved credit.
- **Uninformative when negative.** `p > .05` is not evidence of absence. The existing skeptical
  literature largely reports bare nulls without quantifying what was excluded.
- **Contaminated by self-attribution.** Van Rooij (1999) found sign-congruent self-description only
  among respondents with astrological knowledge. Survey designs conflate "astrology is true" with
  "believers conform to their sign."

Each of the three studies below is built to defeat one of these problems.

---

## Study 1 — Zodiac-cusp regression discontinuity (primary contribution)

**Design.** Sharp regression discontinuity at sign boundaries. A person born 20 September (Virgo)
and one born 24 September (Libra) share essentially identical season, photoperiod, maternal
conditions, and school cohort, but are assigned opposite temperaments by astrology. Sign assignment
at a cusp is as-good-as-random with respect to everything varying smoothly with birth date.

**Prediction.** If sign-based traits exist, outcomes jump discontinuously at the cusp. If only
seasonality exists, outcomes pass through the cusp smoothly.

- **Running variable:** days from exact solar ingress, computed *per birth year* from a real
  ephemeris (ingress dates drift ~1 day across years, so the cutoff moves — this rules out a
  fixed-calendar artifact and supplies within-day-of-year variation).
- **Unit:** individual notable person with day-precision date of birth.
- **Outcome:** occupation category (athlete, artist/musician, writer, politician, scientist,
  military), plus notability rank as a secondary outcome.
- **Beyond sun signs:** exact birth date also fixes **Mercury, Venus, and Mars** sign without
  requiring birth time. This permits tests of claims from actual astrological practice
  (Mars→athletes/soldiers, Venus→artists/musicians, Mercury→writers), not only pop sun-sign
  astrology, adding cutoffs and power.
- **Pooling:** 12 cutoffs pooled with **directionally signed** estimates; predicted jump direction
  per cusp is fixed in `analysis/plan.md` before outcome data is touched, so the pooled estimate
  cannot cancel to zero by construction.

## Study 2 — Mercury retrograde interrupted time series

**Design.** Interrupted time series / panel regression with an exogenous, deterministic,
publicly pre-announced treatment. Retrograde periods are computable to the second and caused by
nothing human, making reverse causation and selection impossible.

- **Treatment:** Mercury retrograde windows plus "shadow" periods (astrologers claim both;
  excluding shadows would be a strawman).
- **Outcome:** daily US flight delay and cancellation rates; market volatility as a second domain.
- **Identification:** retrograde recurs on a ~116-day cycle, only weakly aligned with the annual
  calendar — that misalignment separates it from seasonality.
- **Primary inference:** circular block permutation of the retrograde calendar (exact null, robust
  to unmodelled seasonality), alongside a fixed-effects regression with HAC standard errors.
- **Manipulation check:** search-interest data should show the salience spike is real even where the
  effect is not — supporting a secondary finding about selective attention.

## Study 3 — Survey test with belief moderation (mechanism)

**Design.** Cross-sectional survey analysis of the interaction, not the main effect. The GSS carries
respondent zodiac sign alongside horoscope-readership and astrology-credibility items and hundreds
of outcome variables.

- **Discriminating prediction:** if astrology is true, sign effects are *independent* of belief;
  if self-attribution drives them, sign effects appear *only* among believers.
- This tests two theories against each other rather than testing a null against nothing.

---

## Data (all free, no budget)

| Study | Source | Access |
|---|---|---|
| 1 | Wikidata (`P569` birth date w/ precision qualifier, `P106` occupation, sitelinks as notability) | SPARQL, keyless |
| 1 (cross-val) | Cross-verified database of notable people (Laouenan et al. 2022, *Sci Data*) | repository host to be confirmed by data-scout |
| 1, 2 | JPL DE440 ephemeris via `skyfield` | free download |
| 2 | BTS On-Time Performance; FRED volatility series | free |
| 3 | GSS cumulative data file (NORC) | free |

## Inference framework (user-approved)

- Directional hypotheses **codified from published astrological sources**, each cell attributed to a
  named reference, fixed before outcome data is touched.
- Null framed with **both** frequentist equivalence testing (TOST against a pre-specified SESOI)
  **and** Bayes factors with stated priors and a prior-sensitivity check.
- Headline result is an equivalence bound — "effects larger than X are ruled out" — not "no effect."

## Constraints and scope decisions (user-approved at intake)

- All three studies included; each is independently reportable if another fails at the data stage.
- **Associational language only.** Study 2's treatment is exogenous and permits stronger wording;
  Studies 1 and 3 do not.
- **Moon sign and Ascendant are out of scope** — they require birth *time*, which is not available
  in any free large-N source. Sun/Mercury/Venus/Mars sign is therefore a partial operationalization
  of the full-chart claim, to be stated plainly as a limitation rather than glossed over.
- Notable-people samples are not the general population; external validity limit, stated explicitly.

## Open items for Phase 1 scouting

- Wikidata: count of humans with day-precision `P569` and a codeable `P106`, by era; WDQS timeout
  chunking strategy; extent of date heaping (Jan 1, 1st/15th of month).
- Whether the Laouenan et al. notable-people file has a resolvable, openly licensed download.
- GSS: exact years `ZODIAC` was administered, its coding and derivation, and the realized crosstab N
  of `ZODIAC` × astrology-belief items — this determines whether Study 3's moderation test is
  powered or must degrade to main effects with a stated power limitation.
- BTS: whether daily-granularity on-time data is obtainable via direct file download rather than the
  form-driven interface; fallback to summary tables if not.
- Published ephemeris tables suitable as ground truth for validating computed ingress dates and
  retrograde windows.
