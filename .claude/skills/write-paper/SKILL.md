---
name: write-paper
description: Write an APA-style manuscript from completed, reviewed analysis results. Use in the final phase, after the stats review has passed and GATE 2 approval.
---

# Write Paper

Produce `paper/manuscript.md` from `lit_review.md`, `plan.md`, `results.md`, and `stats_review.md`. Convert to docx if pandoc is available: `pandoc manuscript.md --citeproc --bibliography=../literature/references.bib -o manuscript.docx` (fallback: plain pandoc, references written out from references.bib).

## Structure (APA 7)
- **Title page**: descriptive title stating variables and population; note "Draft generated with AI assistance" (user can remove).
- **Abstract** (≤250 words): objective, method (design, N, data source), key results WITH numbers (effect size + CI), conclusion. No claims absent from Results.
- **Introduction**: funnel from broad to specific; every empirical claim cited from references.bib; end with numbered hypotheses verbatim from plan.md.
- **Method**: Data source & sample (provenance, years, exclusion flow with Ns — from results.md); Measures (operationalizations per plan.md, reliability where computed); Analysis plan (models, inference criteria; note analyses were pre-specified before outcome analysis; software versions from requirements.txt).
- **Results**: descriptives table first; then hypothesis by hypothesis with statistics sentences copied exactly from results.md — do not re-round or re-type numbers. Robustness summary. Clearly separated "Exploratory Analyses" subsection if applicable.
- **Discussion**: findings vs. literature; limitations (mandatory, honest: design cannot establish causation, measurement limits, generalizability, sensitivity limits, anything flagged in stats_review.md); future directions; brief conclusion.
- **References**: from references.bib only.

## Rules
- Every number traceable to `estimates.json`/`results.md`. Every citation present in `references.bib`. No new literature at this stage — if a claim needs an uncited source, cut the claim or rerun literature-scan.
- Associational language throughout for observational designs ("was associated with", not "led to"/"caused"/"increased").
- Exact p-values (p = .034) except p < .001. Effect sizes + 95% CIs in text, not just tables.
- Figures by reference (`![...](../results/figures/...)`) with APA-style captions.
- Tone: precise, hedged proportionate to evidence, no hype. Null/negative findings get equal prominence.
