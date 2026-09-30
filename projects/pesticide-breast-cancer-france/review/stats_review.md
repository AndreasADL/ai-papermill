# Statistical review — pesticide sales intensity and female breast cancer mortality, mainland France

Reviewer: independent stats-reviewer agent (GATE 2). Scope: `analysis/plan.md` vs.
`analysis/*.py` vs. `results/*`, per the `stats-review` skill checklist.

## Verdict: **pass with fixes**

The design, exclusions, and diagnostic battery closely follow the pre-registered plan;
all four logged deviations are legitimate, documented before the outcome-dependent
decision point, and correctly propagated through the robustness checks. The primary
finding is reported honestly as a non-significant, underpowered null with no causal or
"no association" language. However, the write-up's interpretation of the Moran's I
result materially understates a real threat to the validity of the spatial diagnostic,
and I could not execute a fresh `run_all.py` myself in this session (see Rerun log) — so
reproducibility is only verified by static cross-checks, not by an independent live run.

---

## Must fix

### 1. Moran's I / spatial-lag-error interpretation understates the outcome-smoothing confound
**Files**: `analysis/03_main_models.py` (`moran_diagnostic`, `spatial_models`),
`results/diagnostics.md`, `results/results.md` (E3 section, `analysis/run_all.py` lines
~192–203).

I = 0.83 (z = 12.45, p = .001) is extraordinarily high for an areal epidemiological
diagnostic — genuinely clustered disease-risk residuals in the literature typically fall
in the 0.2–0.5 range. Two further numbers in the same output make an *outcome-construction
artifact* the more parsimonious explanation than "true" unmodeled spatial confounding:
the spatial-error model's lambda = 0.969 (i.e., neighboring residuals are almost
perfectly predictive of each other) paired with a very low pseudo-R² (0.021) — a
combination consistent with the spatial-error term absorbing an artifact of the outcome's
*own* construction, not a substantive spatial process. The outcome
(`mortality_rate_std`) is explicitly documented in `data/candidates.md` (candidate 2A) as
a **"model-smoothed estimate, not raw registry counts"** (InVS/Francim spatiotemporal
modeled estimates, which typically borrow statistical strength across neighboring
areas/years). If the smoothing algorithm itself induces spatial correlation in the point
estimates, Moran's I on OLS residuals built from that outcome will be inflated
*mechanically*, independent of any true geographic clustering in breast-cancer risk — and
a spatial-lag/error model fit on top of it is not obviously a valid correction, because its
assumed data-generating process (a spatial autoregressive process on the true outcome)
does not match the actual mechanism (a smoothing algorithm applied at the estimation
stage).

The current write-up acknowledges this only in a single parenthetical clause — "OLS
standard errors likely understate true uncertainty due to spatial clustering in mortality
(**plausibly reflecting** the modeled/smoothed nature of the InVS/Francim mortality
estimates themselves)" — and then concludes this "reinforc[es] rather than overturn[s]
the primary null finding." That conclusion happens to be directionally fine (the spatial
models are still non-significant), but the framing implies the spatial adjustment is a
credible correction for real spatial confounding, when the more likely story is that a
sizeable share of I = 0.83 is a data-construction artifact that makes the spatial-lag/error
coefficients themselves of uncertain interpretability (garbage-in/garbage-out on the
spatial-weights side), not just a caveat about the OLS SEs.

**Concrete fix**: rewrite the E3 paragraph in `results/results.md` (produced by
`build_results_md()` in `run_all.py`) and the corresponding paragraph in
`results/diagnostics.md` to: (a) state plainly, not parenthetically, that I = 0.83 is far
above the range expected from genuine areal disease clustering; (b) cite lambda ≈ 0.97
alongside the low spatial-error pseudo-R² as corroborating evidence that the "spatial
process" being modeled is more likely the outcome's own smoothing than a real omitted
spatial confounder; (c) explicitly downgrade the spatial-lag/error coefficients from
"correction" language to "exploratory, model-dependent under an assumption that may not
match this outcome's actual construction"; (d) add this as an explicit limitation (not
just a robustness footnote) in the "Limitations and deviations" section, since it also
means the Moran's I diagnostic's significance should not be read as a strong causal-
inference concern about omitted spatial confounders in the traditional sense.

---

## Should fix

### 2. Partial-correlation CI is reported at only 2-decimal precision
**File**: `analysis/03_main_models.py`, `partial_correlation()` (lines 68–86).

`pg.partial_corr()`'s `CI95%` column is pre-rounded by pingouin to 2 decimals
(`ci_low = -0.11`, `ci_high = 0.3` in `results/estimates.json`), while every other
statistic in the same block (r = 0.1007, p = 0.3477) is reported to 4 decimals. Not a
correctness bug, but an inconsistent-precision artifact of relying on pingouin's rounded
output column. Fix: compute the Fisher-z CI manually (or extract at full precision) so
the partial-r CI has the same precision as the rest of the block.

### 3. Model-coefficient p (.2748, HC3-robust) vs. partial-correlation p (.3477, classical) differ and are unexplained
**File**: `results/results.md` "Statistics sentence" line.

Both numbers are individually correct (they come from different variance estimators —
HC3-robust Wald test for the regression coefficient vs. a classical Pearson-based test
inside `pg.partial_corr`), but presenting them side by side without a one-line note
inviting readers to wonder why "the same effect" has two different p-values in the same
sentence. Add a one-clause note (e.g., "partial-r p-value uses classical, non-HC3
inference and may differ slightly from the coefficient's robust p-value").

### 4. "Before touching outcome data" wording in the deviation log is stronger than what the code actually guarantees
**Files**: `analysis/plan.md` (Deviations §3), `analysis/01_clean.py` (steps 5 and 5b),
`results/results.md` (Limitations item 3).

I confirmed the exclusion rule itself is outcome-blind: `01_clean.py` step 5b filters
purely on `df["sau_ha"] < 10_000`, never referencing `mortality_rate_std`, so the
decision of *which* departments to drop cannot have been driven by their mortality
values — this is the substantively important guarantee, and it holds. However, by the
time step 5b runs, `mortality_rate_std` has already been merged into the same dataframe
(step 5 precedes 5b in the same script), so the literal phrase "before touching outcome
data" is not quite accurate — the outcome column is already in memory, just not used in
the filter condition. Recommend tightening the language in `plan.md`'s Deviations
section and `results.md`'s Limitations item 3 to something like "decided without
reference to outcome values" rather than "before touching outcome data," to avoid
overclaiming a stronger sequencing guarantee than the code provides. This is a wording
precision issue only — I found no evidence the exclusion was actually influenced by
outcome values.

### 5. Stale code comment
**File**: `analysis/01_clean.py` line 174 — the range-assertion comment "(Paris-region
depts are high)" for `pop_density` is stale now that Paris/Hauts-de-Seine/Seine-Saint-
Denis/Val-de-Marne are excluded upstream (step 5b). Cosmetic only.

---

## Plan adherence

Confirmed by direct comparison of `analysis/plan.md` (formula, estimator, exclusion
criteria, missing-data protocol, power/MDE framing, assumption-check battery, robustness
checks E1–E3) against `analysis/01_clean.py`, `03_main_models.py`, `04_robustness.py`:

- **H1 model**: exact formula match (`mortality_rate_std ~ log_pesticide_intensity +
  poverty_rate + log_pop_density`), HC3 SEs as specified, alpha = .05, no multiplicity
  correction (correct — H1 is the sole confirmatory hypothesis).
- **All four deviations** (RA2020 SAU vintage, 2020 poverty vintage, exclusion of
  Paris/92/93/94, Corsica 2A/2B unification) are logged in `plan.md`'s Deviations
  section and `data/provenance.md`, are substantively justified (documented API
  availability probes, a genuine natural gap in the SAU distribution), and are applied
  **consistently** across the primary model and both robustness subsamples (E1, E2) —
  I verified the same `NONAG_SAU_THRESHOLD = 10_000` constant is imported and reused in
  `04_robustness.py`, not silently redefined.
- **E1–E3 robustness checks**: all three implemented as specified (purchase-based
  exposure, linear exposure, FRANCIM E2 sign-only comparison, Moran's I + spatial
  contingency), and none are laundered into the confirmatory result — `robustness.md`'s
  own narrative explicitly says the one nominally-significant robustness check
  (purchase-based exposure, p = .040) is "reported here at face value, not treated as
  confirmatory."
- No exploratory result is presented as confirmatory anywhere in `results.md`.

## Statistical validity

- **Diagnostics actually run correctly**: Breusch-Pagan (LM = 17.46, p = .0006 →
  heteroskedastic, HC3 used regardless, as pre-specified), Shapiro-Wilk (W = .945,
  p = .0007 → non-normal, correctly triggers the Huber-T/Spearman contingency), VIF (all
  < 1.5, no multicollinearity), Cook's distance (5/91 flagged at the 4/n threshold,
  sensitivity refit reported *alongside*, not *instead of*, the primary estimate — I
  verified `4/91 = 0.04396` matches the reported threshold exactly).
- **Standardized beta cross-check**: I manually recomputed standardized beta from the
  raw coefficient and reported SDs (0.1585 × SD(log_pesticide_intensity=1.008) /
  SD(mortality=1.357) ≈ 0.118), which matches the reported 0.1177 to 3 decimals —
  internally consistent.
- **t = coef/SE cross-check**: 0.15846 / 0.14512 = 1.0920, matches reported t = 1.0920.
- **Power/MDE**: `compute_power()` is computed programmatically at the *achieved* N = 91
  (df_resid = 87), not copied from the plan's pre-analysis N ≈ 96 estimate — correct and
  more rigorous than the plan required. MDE partial r = 0.2876, rounds to the reported
  "0.288" everywhere it appears.
- **Moran's I / spatial contingency**: correctly triggered per the pre-specified rule
  (significant at p = .001 → spatial-lag/error refit run); see Must-fix #1 for the
  interpretation concern.
- No colliders/mediators controlled for; no continuous variable dichotomized without
  reason; no subgroup-vs-interaction conflation found.

## Interpretation

- **No causal language found.** I grepped `results/results.md` for causal phrasing
  ("causes", "leads to", "increases the risk") and found no instances beyond the word
  "because" used as a grammatical conjunction, not a causal claim about the exposure.
  Every substantive claim uses "associated with" / "association" throughout.
- **No "no effect"/"no association" language slippage.** The mandated framing — "no
  effect detected above partial r ≈ 0.288" — is the only such phrase used anywhere the
  null result is characterized (`results.md` line 78's power caveat, generated
  programmatically in `run_all.py`'s `power_caveat` block); I found no place where the
  non-significant H1 result is instead described as "no association" or "no effect"
  without that qualifier.
- The one nominally-significant alternative specification (purchase-based exposure,
  p = .040) is correctly *not* elevated to a headline finding.

## Missing data / sample construction

- Sample flow accounts fully: 98 Odisse records → 95 mainland (drop 3 DOM) → 91 after
  the SAU < 10,000 ha exclusion (drop 4: Paris/92/93/94) → 0 further missingness → final
  N = 91. Arithmetic checks out (95 − 4 = 91) and is asserted in code
  (`assert n1 == 95`).
- The SAU-threshold exclusion rule is outcome-blind by construction — see Should-fix #4
  for a wording-precision caveat on how this is described in the deviation log.

## Rerun log

**I could not execute `python analysis/run_all.py` myself in this review session** — the
tools available to me in this environment are read-only (Read/Grep/Glob/Write); no
command-execution tool was provided. This is a genuine limitation on this review's
reproducibility verification and should be weighed accordingly; it is not a substitute
for the mandatory rerun the skill specifies.

What I did instead, as the best available substitute:
1. Read `results/estimates.json` and `results/robustness.json` directly and confirmed
   every number quoted in `results/results.md` matches them exactly (expected, since
   `run_all.py`'s `build_results_md()` mechanically reads these JSON files rather than
   having numbers typed by hand — this check mainly rules out post-hoc manual editing of
   `results.md`, not computational correctness).
2. Independently hand-recomputed several statistics from first principles to check
   internal consistency rather than mere self-consistency of the pipeline's own outputs:
   t = coef/SE (1.0920, matches), standardized beta from raw coefficient × SD ratio
   (≈0.118, matches reported 0.1177), Cook's distance threshold 4/91 = 0.04396 (matches),
   N arithmetic (95 − 4 = 91, matches), and MDE partial r rounding (0.2876 → "0.288",
   matches every place it is quoted).
3. Read every analysis script (`00_download.py` through `05_figures.py`) end to end and
   confirmed the pipeline is deterministic (`SEED=42` set and reused consistently,
   including a documented reseed immediately before the Moran's I permutation test,
   which draws from the global NumPy RNG) and that `run_all.py` runs all six steps in
   the correct dependency order before assembling `results.md`.
4. I did **not** independently re-download raw data or re-run the regression from
   scratch. The task prompt states the calling agent already re-ran `run_all.py` once
   and confirmed it completes without error; I was not able to independently confirm
   that a *second* fresh run reproduces bit-identical numbers. I recommend the calling
   agent treat its own rerun (not this review) as the authoritative reproducibility
   check, and flag this gap explicitly rather than certify reproducibility on my
   authority alone.

No arithmetic inconsistency was found in any of the spot checks above.

## Overall assessment

This is a carefully executed, honestly reported ecological analysis. The plan's
confirmatory/exploratory boundary is respected throughout, all four deviations are
substantively justified and applied consistently across the primary and robustness
models, the assumption-check battery is complete and correctly gates its contingencies
(heavy-tailed residuals → Huber-T + Spearman; significant Moran's I → spatial-lag/error),
and the interpretation is scrupulously non-causal with the mandated power caveat applied
uniformly. The one substantive problem is that the write-up under-develops a real
threat to the Moran's I diagnostic's meaning — the outcome variable's own "model-smoothed"
construction is a more parsimonious explanation for I = 0.83 than genuine unmodeled
spatial confounding, and the current framing treats the spatial-lag/error comparison as
more informative about "true uncertainty" than the evidence (I = 0.83, lambda ≈ 0.97,
spatial-error pseudo-R² = 0.02) supports. This does not overturn the study's bottom line
(H1 remains a non-significant, underpowered null under every specification, including
the spatial ones), but the manuscript should not present the spatial-adjusted
coefficients as if they are a validated correction without this caveat. Fix Must-fix #1
before the paper draft, address the Should-fix items opportunistically, and the study is
ready for Phase 5.
