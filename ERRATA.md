<div align="center">

# Errata board

**Every error found in AI Papermill's output, including the ones it caught itself.**

![open](https://img.shields.io/badge/open-8-d9534f?style=flat-square)
![caught before publication](https://img.shields.io/badge/caught_before_publication-15-5cb85c?style=flat-square)
![reported by readers](https://img.shields.io/badge/reported_by_readers-0-lightgrey?style=flat-square)

</div>

The papers in this repo were written by an AI pipeline and have **not been checked line by line by a human**. Errors are expected. This page exists so they get found, recorded, and fixed in the open instead of quietly disappearing.

Found something? [Open an erratum](../../issues/new?template=erratum.yml). Wrong numbers, overclaimed conclusions, bad citations, broken reproducibility and misleading wording all count.

---

## What goes wrong when you leave research to an AI

These patterns come from the entries below. The list will grow.

| Pattern | Example | Caught by |
|---|---|---|
| **The interpretation claims more than the diagnostics show** | Said a failed estimator had been "resolved" when its own diagnostic showed the opposite (A-01) | Reviewer agent |
| **The rules are followed in spirit, not to the letter** | A preregistered "stop" condition was triggered and then silently worked around (A-02) | Reviewer agent |
| **Silent method swaps** | The preregistered Bayes-factor recipe was replaced without logging the deviation (A-03) | Reviewer agent |
| **Computed but never reported** | A required sensitivity analysis existed only in a JSON file (A-04) | Reviewer agent |
| **Stale hand-written text next to generated numbers** | The results file says a variable was never extracted after it had been (A-12) | Human audit |
| **"Reproducible" asserted, not demonstrated** | Neither reviewer agent could execute code. Reproduction was checked by reading, not by re-running (A-14, P-07) | Reviewer agent (self-disclosed) |
| **Correct procedure, wrong unit of analysis** | A Beta-Binomial test over 159 M flights gave "overwhelming" evidence for a 0.036 pp difference. The pipeline caught and explained this itself | Pipeline, in the paper |

---

## Severity and status

**Severity:** 🔴 critical (changes a conclusion) · 🟠 major (materially misleading or unverified) · 🟡 minor (a real error that doesn't change a conclusion) · ⚪ wording

**Status:** ✅ fixed · 🟦 disclosed (not fixed, but stated in the paper) · ⬜ open

---

## Reported by readers

*None yet. That won't last; please help.*

| ID | Study | Where | What's wrong | Severity | Reported by | Status |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## Astrology: *Bounding the Empirical Validity of Astrological Prediction*

[Paper (PDF)](projects/astrology-efficacy/paper/manuscript.pdf) · [Stats review](projects/astrology-efficacy/review/stats_review.md)

### Open

| ID | Where | What's wrong | Severity | Found by | Status |
|---|---|---|---|---|---|
| A-12 | `results/results.md` (Gaps; balance table), `data/provenance.md` §1 | Both say citizenship (`P27`) was never extracted and the citizenship balance check could not run. It was extracted later by `02c_extract_citizenship.py`, and the manuscript correctly reports it (84.0% coverage, balanced). The stale sentence is hard-coded in `analysis/09_synthesis.py` (~L946, ~L976) rather than generated from `estimates_study1.json`, which breaks the "nothing typed by hand" claim. | 🟡 | Human audit, 2026-09-30 | ⬜ |
| A-13 | `analysis/run_all.py` | `02c_extract_citizenship.py` is not a pipeline stage. A fresh `run_all.py` skips the citizenship balance check (`05_study1_rdd.py` prints "SKIPPED"), so it does **not** reproduce every reported number, contrary to its docstring. | 🟡 | Human audit, 2026-09-30 | ⬜ |
| A-16 | `paper/manuscript.md`, Figure 1 | The summary figure plots Study 1's H1 rows using the continuity-based (`rdrobust`) estimates, which the paper declares invalidated a few paragraphs later. The confirmatory claims rest on the local-randomization estimator in Table 2. The caption doesn't say this, so a reader sees a significant, wrong-direction Mercury effect in the paper's main figure. | 🟡 | Human audit, 2026-09-30 | ⬜ |
| A-14 | Whole study | The reviewer agent had no shell and could not re-run the pipeline. It verified numbers by reading code and hand-recomputing, and explicitly said this "should not be treated as satisfied". No byte-for-byte reproduction from a clean checkout has been documented since. | 🟠 | Reviewer agent (self-disclosed) | ⬜ |
| A-10 | `results/sample_flow.md` | "People with ≥1 occupation: 3,714,005" is counted before the birth-year restriction, whereas the analysis N is 3,701,431. The code is consistent, but a reader will think it's a discrepancy. A clarifying comment in `03_clean.py` was requested and not added. | ⚪ | Reviewer agent | ⬜ |
| A-15 | `analysis/06_study2_its.py` | The Venus-retrograde placebo is stubbed as `"n/a"` and was never run. It would be a cheap extra falsification check for Study 2. | ⚪ | Reviewer agent | ⬜ |

### Caught by the pipeline and fixed before publication

| ID | Where | What was wrong | Severity | Resolution |
|---|---|---|---|---|
| A-01 | Study 1 headline | Claimed the local-randomization estimate "resolves" the Mercury result and that the `rdrobust` estimate "was an artifact". The project's own isolation-grid diagnostic did not show the predicted shrinkage toward zero, so the claim went further than the evidence. | 🟠 | ✅ Rewritten: "not a correction applied to the first … cause remains undiagnosed" |
| A-02 | Study 1 | The plan's clause "a failure of [placebo cutoffs] invalidates the corresponding study" was triggered (11.4% vs 5% rejection) and never explicitly engaged. | 🟠 | ✅ The paper now states that Study 1's primary design is invalidated under its own terms, and why the secondary estimator is used |
| A-03 | Inference, all tests | The plan specified a Beta-Binomial BF for proportions, but every test used the JZS-Cauchy normal-likelihood BF, and this was not logged as a deviation. | 🟠 | ✅ Logged as a deviation; Beta-Binomial reported as supplementary, with the pseudo-replication explanation |
| A-11 | `02_extract_wikidata.py` | The docstring claimed citizenship was extracted, but the SPARQL query never selected it. | 🟡 | ✅ Added `02c_extract_citizenship.py` and fixed the docstring (see A-12 and A-13 for leftovers) |
| A-04 | `results.md` | The prior-sensitivity curve required by the plan was computed but never reported. | 🟡 | ✅ Sensitivity table added |
| A-05 | Study 1, H1-Me | Fixed- and random-effects pooling disagree on significance (I² = 80%), which was buried. | 🟡 | ✅ Stated next to the estimate; the RE interval is called "the honest one" |
| A-06 | Study 2, cancellations | The SESOI for cancellations (0.1 pp) was chosen at analysis time without justification. | 🟡 | 🟦 Disclosed in Deviations; value unchanged |
| A-07 | Figure: Study 2 permutation null | Plotted an idealized Gaussian instead of the empirical permutation distribution. | 🟡 | ✅ Empirical histogram of 10,000 shifts. The suggested sensitivity check for ~107-day offsets is not documented |
| A-09 | Study 3 composite | Sociability score allowed a 1-item average. | 🟡 | ✅ Robustness check restricted to all 4 items (equivalence retained) |
| A-08 | `plan.md` vs `hypotheses.py` | Disagreed on the size of the confirmatory family (H1-Su dropped). | ⚪ | ✅ Dated corrigendum added to `plan.md` |

---

## Pesticides and breast cancer: *Agricultural Pesticide Sales Intensity and Female Breast Cancer Mortality*

[Paper (PDF)](projects/pesticide-breast-cancer-france/paper/manuscript.pdf) · [Stats review](projects/pesticide-breast-cancer-france/review/stats_review.md)

### Open

| ID | Where | What's wrong | Severity | Found by | Status |
|---|---|---|---|---|---|
| P-07 | Whole study | The reviewer agent could not execute code. The orchestrating agent ran `run_all.py` once without errors, but reproduction of identical numbers on a second clean run was not verified. | 🟠 | Reviewer agent (self-disclosed) | ⬜ |
| P-06 | `literature/references.bib` | References were retrieved from OpenAlex / Semantic Scholar / Crossref during the literature scan but, unlike the astrology study, were **not re-resolved afterwards** by a verification script. | 🟡 | Human audit, 2026-09-30 | ⬜ |

### Caught by the pipeline and fixed before publication

| ID | Where | What was wrong | Severity | Resolution |
|---|---|---|---|---|
| P-01 | E3 spatial analysis | Treated the spatial-lag/error models as a correction for spatial confounding. Moran's I = 0.83 with λ ≈ 0.97 and pseudo-R² = 0.02 points instead to an artifact of the outcome's model-smoothed construction. | 🟠 | ✅ Stated as an explicit limitation; spatial models downgraded to "should not be over-interpreted" |
| P-02 | Partial correlation | The 95% CI was reported at 2-decimal precision (pingouin pre-rounds). | 🟡 | ✅ Full-precision CI |
| P-03 | Statistics sentence | Two different p-values (.275 HC3 vs .348 classical) for "the same effect", unexplained. | ⚪ | ✅ Explanatory note added |
| P-04 | Deviation log | "Before touching outcome data" was stronger than the code guarantees: the outcome was already merged, just unused by the filter. | ⚪ | ✅ Reworded to "decided without reference to outcome values" |
| P-05 | `01_clean.py` | Stale code comment. | ⚪ | ✅ Removed |

---

<sub>Entries marked "Reviewer agent" are quoted or condensed from each study's <code>review/stats_review.md</code>. "Human audit" entries were found while preparing this repository for publication. A status of ✅ means the fix is visible in the published manuscript or code, not that it has been independently verified.</sub>
