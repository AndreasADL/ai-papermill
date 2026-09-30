# Contributing

The most valuable contribution to this project is **finding what the AI got wrong**.

## Report an error

Open an [erratum issue](../../issues/new?template=erratum.yml). Please quote the claim, say what's wrong, and include evidence if you can. Accepted errata go on the [errata board](ERRATA.md) with credit, whether they are major or a single misleading word.

## Discuss methods

Disagreements about design choices, such as the SESOI, the estimator, or whether a dataset measures what it claims to, are welcome in GitHub Discussions. Many of them are judgement calls, not errors, and the board is for errors.

## Fixing things

- **Never hand-edit a number in a paper or results file.** Fix the script, re-run the study's `analysis/run_all.py` (or the affected stages with `--only`), and let the numbers regenerate.
- Keep the preregistration intact. Don't edit `analysis/plan.md` retroactively; add a dated corrigendum or a Deviations entry instead.
- Label anything not in the plan as **exploratory**.
- Link the erratum ID (e.g. `A-12`) in your PR, and update its status on the board.

## Propose a study

Open an issue describing the question, why it hasn't been studied rigorously, and which open dataset might answer it. The odder the better, as long as public data can plausibly test it.
