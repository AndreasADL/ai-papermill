---
name: analysis-plan
description: Write a preregistration-style analysis plan before any confirmatory analysis. Use after literature scan and data scouting, before touching outcome data. Output is the GATE 1 document the user approves.
---

# Analysis Plan (preregistration-style)

Write `analysis/plan.md` BEFORE running any model on the outcome. Structure:

## 1. Research question & hypotheses
- Numbered, directional where justified by literature (H1, H2…). Each with a one-line rationale citing `lit_review.md`.
- Explicitly separate confirmatory hypotheses from planned exploratory questions.

## 2. Data
- Dataset(s), N, unit of analysis, years. Inclusion/exclusion criteria (defined BEFORE looking at outcomes).
- Exact variable operationalizations: name in dataset, coding, transformations (e.g., log income), scale handling (sum vs. mean score, reliability via Cronbach's alpha if items available).

## 3. Missing data
- Expected mechanism, planned handling (complete cases if <5% missing; otherwise multiple imputation or explicit justification). Report sensitivity either way.

## 4. Statistical models
For each hypothesis: the exact model (e.g., "OLS: outcome ~ predictor + age + sex + education, HC3 robust SEs"; "Pearson r with Fisher CI"; "multilevel model, random intercept for country"). Specify:
- Estimator, covariates and why (confounders from literature, not outcome-driven selection)
- Effect size metric + 95% CI (r, standardized beta, Cohen's d, OR…)
- Inference criterion: alpha; multiple-comparison correction across hypotheses (Holm or FDR — state which)

## 5. Power / sensitivity
- If N is fixed by the dataset: sensitivity analysis — smallest effect detectable at 80% power (e.g., via `statsmodels.stats.power`). State whether literature-typical effects are detectable. If not, flag at GATE 1.

## 6. Assumption checks & contingencies
- Which diagnostics (linearity, heteroscedasticity, influential points, distributional checks) and pre-specified fallbacks (e.g., "if residuals heavy-tailed → Spearman + robust regression as sensitivity").

## 7. Robustness checks
- 2–4 planned: alternative operationalizations, subsets, added/removed covariates, alternative estimators.

## Rules
- No outcome-involving analysis before approval. Descriptives of predictors/demographics for planning are OK; anything involving the outcome is not.
- Any post-approval deviation goes in a "Deviations" section of plan.md with justification, and is labeled in results.
- At GATE 1, present the user a ≤15-line summary and ask for approval or edits.
