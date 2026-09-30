# Analysis Plan (preregistration-style)

Study: Department-level agricultural pesticide use and female breast cancer mortality,
mainland France (ecological/correlational design).
Written: 2026-08-08, before any analysis touching outcome data.
Sources synthesized: `../idea.md`, `../literature/lit_review.md`, `../data/candidates.md`.

---

## 1. Research question & hypotheses

**Research question**: Is department-level agricultural pesticide sales intensity
associated with department-level age-standardized female breast cancer mortality in
mainland France, after adjusting for socioeconomic deprivation and urbanization/density?

### H1 (confirmatory, primary)
Department-level agricultural pesticide sales intensity (kg active substance / ha
utilized agricultural area, 2008–2014 average) is **positively associated** with
age-standardized female breast cancer mortality rate (2007–2014), adjusting for poverty
rate and population density.

*Rationale*: The xenoestrogen mechanism and individual-level biomarker meta-analyses
support plausibility (DDT/DDE sOR 1.15–2.24 depending on compound/design;
Ugalde-Resano et al. 2024). **However**, the literature scan's closest area-level design
analog — GIS residential-proximity to agricultural pesticide use, California Teachers
Study — found **null** results (HR 1.03–1.15, CIs crossing 1; Reynolds et al. 2004), and
no prior study of any kind has tested this specific France department-level pairing. H1
is therefore a genuine, not a foregone, test, and **a null result is pre-specified as
informative**, not a failed study — it would be consistent with the area-level design
literature and would fill a documented evidence gap either way.

### Exploratory questions (labeled exploratory in all outputs, not subject to the
confirmatory alpha)
- **E1**: Does the association direction/magnitude hold using purchase-based
  (buyer-postal-code) exposure (2013–2023) instead of distributor-sales-based exposure
  (2008–2014)?
- **E2**: Does the association direction hold in the ~20 FRANCIM registry departments
  using directly observed incidence (2018–2022) instead of modeled mortality? (Power
  analysis in §5 shows this subsample cannot support an independently powered test —
  evaluated for sign/direction consistency only.)
- **E3**: Is there significant spatial autocorrelation in mortality rates / model
  residuals (Moran's I)? If so, does a spatial-lag/error model change the pesticide
  coefficient's magnitude or significance relative to OLS?

---

## 2. Data

**Design**: single cross-section, unit = mainland French department.

**Primary analysis dataset** (N target ≈ 96 departments; exact N confirmed after
Phase 3 download — see Missing Data §3):

| Role | Variable | Source | Period | Operationalization |
|---|---|---|---|---|
| Outcome (Y) | `mortality_rate_std` | Santé publique France / Francim-InVS-HCL modeled estimates, Odissé dataset `cancer-incidence-et-mortalite-estimees-departement` (API-verified) | 2007–2014 pooled | Age-standardized (world std population) female breast cancer ("Sein") mortality rate per 100,000; filter `sexe="Femmes"`, `indic="Mortalité"`, `lib="Sein"` |
| Exposure (X) | `pesticide_intensity` | BNV-D `VENTE_DPT_SUBSTANCE` files (data.eaufrance.fr / data.gouv.fr, documentation-verified) ÷ Agreste RA2010 Surface Agricole Utilisée (documentation-verified) | Sales 2008–2014 | Sum of kg active substance sold, department, 2008–2014, divided by 7 (annualize) and by department SAU (ha) → **kg active substance / ha / year**. Log-transformed (natural log) as primary operationalization (agricultural intensity variables are conventionally right-skewed); untransformed linear version run as a robustness check (§7). |
| Confounder (C1) | `poverty_rate` | INSEE FiLoSoFi via Observatoire des Territoires, `taux-de-pauvrete-seuil-60-du-revenu-median` (documentation-verified) | Nearest available vintage to ~2012 (earliest FiLoSoFi vintage; matches outcome period better than later vintages) | % of population below 60% of median income, department level, used as-is (%) |
| Confounder (C2) | `pop_density` | INSEE via Observatoire des Territoires, `densite-de-population` (documentation-verified) | Nearest available vintage to outcome period | Inhabitants / km², log-transformed (natural log) — right-skewed, standard in urbanization literature |

**Inclusion criteria** (fixed before touching outcome values): all mainland French
departments (INSEE codes 01–95, including Corsica 2A/2B) with non-missing, non-suppressed
values for all four variables above in the specified period.

**Exclusion criteria**: overseas departments/regions (DOM: Guadeloupe, Martinique,
Guyane, Réunion, Mayotte) excluded — out of scope per `idea.md` ("mainland France"), and
several exposure/agricultural-context variables (SAU, agricultural pesticide-use
patterns) are not comparable to mainland agriculture. Any department with a
suppressed/secret-statistique BNV-D value (possible for departments with very few
distributors) excluded from the primary model and listed explicitly in
`data/provenance.md`.

**Robustness subsample** (E2, N ≈ 20): FRANCIM registry-covered departments, observed
incidence 2018–2022 (Odissé `cancer-incidence-observee-en-zone-registres-departement`,
API-verified), paired with BNV-D sales 2018–2022 and Agreste RA2020 SAU. Full registry
department list to be enumerated by a facet query in Phase 3 before this subsample is
finalized.

---

## 3. Missing data

**Expected mechanism**: Outcome (candidate 2A) is a modeled estimate with **no known
suppression** — full department coverage expected, so outcome-side missingness should be
~0%. Exposure (BNV-D) and confounders (INSEE) are the more likely sources of missingness,
via secret-statistique suppression (BNV-D, for low-distributor-count departments) or
department-code mismatches (e.g., Corsica 2A/2B vs. legacy code 20; Paris/petite
couronne codes in some INSEE series).

**Planned handling**:
- If total listwise missingness across the four analysis variables is **<5% of
  departments** (i.e., ≤4–5 of ~96): complete-case analysis, with excluded departments
  listed by name/code and reason in `data/provenance.md` and `results/results.md`.
- If **≥5%**: before proceeding, compare excluded vs. included departments on any
  available characteristic (e.g., region, population size) to informally assess whether
  exclusion looks systematic (MNAR-like, e.g. small rural departments suppressed more
  often) vs. haphazard. Report this comparison. Given the small predictor set (k=3),
  multiple imputation is the planned fallback if missingness looks non-trivial and
  plausibly MAR; if it looks MNAR (e.g., concentrated in a specific region or
  systematically low-population departments), imputation will not be used and the
  reduced-N complete-case result will be reported with this limitation stated explicitly
  — this is a judgment call to be surfaced at GATE 2 (stats review), not resolved
  silently.

---

## 4. Statistical models

### H1 primary model
**OLS multiple regression**:

```
mortality_rate_std ~ log(pesticide_intensity) + poverty_rate + log(pop_density)
```

- **Estimator**: OLS, HC3 heteroskedasticity-robust standard errors (baseline for all
  reported inference, given small-N department-level data with likely unequal variances
  across departments of very different population size).
- **Effect size**: standardized regression coefficient (beta) for
  `log(pesticide_intensity)`, with 95% CI; also reported as partial correlation *r* with
  Fisher-transformed 95% CI, for comparability with the correlational-literature effect
  sizes summarized in `lit_review.md`.
- **Inference criterion**: two-sided alpha = 0.05 on the pesticide coefficient. H1 is
  the sole confirmatory hypothesis, so **no multiple-comparison correction** is applied
  to it. E1–E3 are exploratory, reported with nominal (uncorrected) p-values for
  reference only, and labeled "exploratory" everywhere they appear.

### Spatial diagnostic (pre-specified, not optional — see literature §6.3)
- Build a department adjacency (queen contiguity) spatial weights matrix from a public
  department-boundary file (to be sourced in Phase 3, e.g. the `france-geojson`
  project / data.gouv.fr "contours-des-départements"), using `libpysal`/`esda` (not in
  the base environment — to be installed and pinned in `requirements.txt`).
- Compute **Moran's I** on H1 model residuals.
  - If **not significant** (p ≥ .05): OLS result stands as the final primary estimate.
  - If **significant** (p < .05): refit as a spatial-lag or spatial-error model
    (`libpysal`/`spreg`) and report both the OLS and spatial-adjusted pesticide
    coefficient side by side — this comparison is pre-specified, not a post-hoc
    fishing step.

---

## 5. Power / sensitivity

Computed via `statsmodels.stats.power.FTestPower` (partial F-test for one predictor in a
3-predictor multiple regression), run 2026-08-08:

- **Primary model, N ≈ 96, k = 3 predictors, residual df = 92**: at alpha = .05, power =
  .80, the minimum detectable effect is **Cohen's f² ≈ 0.085** (partial *r* ≈ **0.28**,
  partial R² ≈ 0.079) — a small-to-medium effect by Cohen's convention.
- **Literature context**: this is a materially larger effect than the null-to-small
  hazard ratios found in the closest area-level design analog (Reynolds et al. 2004: HR
  1.03–1.15). **This means the study is underpowered to detect an effect as small as the
  closest comparable prior finding.** A non-significant H1 result must therefore be
  interpreted and reported as "no effect detected above partial *r* ≈ 0.28," not as
  evidence of no association — this caveat is mandatory in `results/results.md` and the
  manuscript's limitations section regardless of outcome.
- **E2 robustness subsample, N ≈ 20, residual df = 16**: minimum detectable partial *r*
  ≈ **0.575** (partial R² ≈ 0.33) — severely underpowered. Pre-specified: E2 will be
  reported and interpreted **only for sign/direction consistency** with the primary
  model's pesticide coefficient, never as an independently powered significance test.

---

## 6. Assumption checks & contingencies

- **Linearity**: partial-residual (added-variable) plot for `log(pesticide_intensity)`.
- **Homoscedasticity**: Breusch-Pagan test; HC3 SEs used as baseline regardless of
  result.
- **Normality of residuals**: Q-Q plot + Shapiro-Wilk (informative given N≈96, not
  decisive on its own).
- **Influential points**: Cook's distance and leverage; departments with Cook's D >
  4/n flagged and a sensitivity re-fit excluding them reported alongside (not
  substituted for) the primary result.
- **Multicollinearity**: VIF for all three predictors; flag if VIF > 5.
- **Spatial autocorrelation**: Moran's I on residuals, per §4 — pre-specified primary
  diagnostic, with the spatial-model contingency already specified above.
- **Heavy-tailed/non-normal residual contingency**: if Q-Q/Shapiro-Wilk indicate marked
  non-normality, report a robust-regression fit (`statsmodels` RLM, Huber's T) and a
  Spearman correlation on the raw bivariate pesticide–mortality relationship as
  sensitivity analyses alongside (not replacing) the primary OLS result.

---

## 7. Robustness checks

1. **Alternative exposure measure**: purchase-based (buyer-postal-code, 2013–2023)
   BNV-D exposure aggregated to department, vs. primary distributor-sales-based measure
   (2008–2014) — directly tests sensitivity to the documented sales-vs-use department
   mismatch caveat.
2. **Untransformed exposure**: linear (non-log) `pesticide_intensity` in place of the
   log-transformed primary specification, to confirm the log-transform choice is not
   driving the result.
3. **Outcome robustness (E2)**: FRANCIM observed incidence (2018–2022), ~20 registry
   departments, same confounder-adjusted model — sign/direction consistency check only,
   per the power analysis in §5.
4. **Spatial-model comparison (E3)**: OLS vs. spatial-lag/error coefficient comparison,
   reported whenever Moran's I is significant (§4/§6).

---

## Deviations

Logged during Phase 3 (data acquisition + analysis), 2026-08-08. Full technical
detail and evidence for each is in `data/provenance.md`; each is also surfaced in
`results/results.md`'s "Limitations and deviations" section.

### 1. SAU normalizer: RA2020 used instead of RA2010

SS2 specified RA2010 (2010 agricultural census) as the better-time-aligned SAU
vintage for the 2007-2014 mortality period. The documentation-verified source
(`observatoire-des-territoires.gouv.fr/surface-agricole-utilisee-sau`) currently
exposes only the RA2020 vintage through its confirmed-working download API
(`indic=sau2020`); direct probes of the same API with candidate RA2010 indicator
names (`sau2010`, `sau10`, `sau_2010`) all returned 404, and the RA2010-specific
data.gouv.fr dataset found by search did not resolve to a working department-level
export in reasonable effort. RA2020 is used for both the primary model and the E2
robustness subsample (which already specified RA2020). Justification for proceeding
rather than stopping: SAU is a slow-changing, structural land-use variable at
department grain (a vintage mismatch was already anticipated as a real limitation in
`data/candidates.md`); using the one confirmed-accessible vintage consistently is
preferable to fabricating or hand-deriving an RA2010 figure.

### 2. Poverty rate: 2020 vintage used instead of ~2012

SS2/SS3 targeted "nearest available vintage to ~2012" (the earliest FiLoSoFi
vintage). The confirmed-working Observatoire des Territoires department-level
endpoint for `filosofi`/`tx_pauv_60` currently serves only 2020 and 2021 vintages.
INSEE's own direct FiLoSoFi downloads for ~2012-2016 (`insee.fr/fr/statistiques/1895078`,
`.../4190004`) are commune-level only ("base-cc-filosofi-*"), with no ready-made
department aggregate; computing one would require an independent population-weighted
aggregation across communes (including commune-level secret-statistique handling)
that this pipeline does not attempt, to avoid introducing an unaudited derived
statistic. 2020 (earliest available via the confirmed working department-level
endpoint) is used instead — an 8-year gap from the mortality period (2007-2014)
rather than the originally targeted ~0-2 year gap. Flagged explicitly as a
limitation in `results/results.md`; poverty rate's role is a confounder, not the
tested predictor, which somewhat limits (but does not eliminate) the impact of this
gap.

### 3. Non-agricultural department exclusion (Paris, Hauts-de-Seine, Seine-Saint-Denis,
   Val-de-Marne)

Not anticipated by SS2, which only specified excluding "suppressed/missing" BNV-D
values. Building `pesticide_intensity` (kg active substance / ha SAU / year) revealed
that four inner-Paris-region departments — 75 (Paris, SAU = 1 ha), 92 (Hauts-de-Seine,
5 ha), 93 (Seine-Saint-Denis, 526 ha), 94 (Val-de-Marne, 1,039 ha) — have SAU so close
to zero that dividing nonzero recorded BNV-D sales by it produces implausible
"intensity" values (up to ~21,000 kg/ha/year, vs. a next-highest genuine value of
~19.8 kg/ha/year). This is a direct instance of the sales-recorded-at-distributor's-
department caveat already documented in `data/candidates.md` (national wholesalers'
head offices are disproportionately located in the Paris region) — not agricultural
pesticide intensity. There is a large, clean natural gap in the SAU distribution (1 /
5 / 526 / 1,039 ha for these four vs. 19,689 ha for the next-smallest, genuinely
rural, department), so a fixed threshold of SAU < 10,000 ha — set from this gap,
without reference to outcome (mortality) values — excludes exactly these four
departments and nothing else. Note on sequencing: the outcome column is already
merged into the working dataframe by this point in `01_clean.py` (step 5 precedes
step 5b), so the guarantee is that the exclusion *rule* never reads
`mortality_rate_std` — not that the outcome was physically absent from memory. This
is a data-quality exclusion decided at the
exposure/normalizer stage, consistent with the "plan before peeking" rule (CLAUDE.md
rule 2). Final N = 91 (of 95 mainland departments) as a result.

### 4. Corsica department-code unification

Not really a "deviation" in the substantive sense (no data content is changed by
choice), but logged for completeness: the outcome (Odisse) reports Corsica as a
single unified code `20`, while BNV-D, the three Observatoire des Territoires
confounder/normalizer files, and the department geojson all use the modern split
`2A`/`2B`. `01_clean.py`/`_common.py` aggregate `2A`+`2B` into `20` for every
non-outcome source (sum for extensive quantities — BNV-D kg, SAU hectares; simple
unweighted mean for intensive/rate quantities — poverty rate, population density).
Affects exactly 1 of 91 final analysis departments; the unweighted-mean
approximation for the two rate confounders is a minor, documented simplification.
