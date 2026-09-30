# Studies

> [!WARNING]
> Everything in these folders was produced by an AI pipeline. The manuscripts are **not peer-reviewed** and **not fully human-verified**. Known problems are tracked on the [errata board](../ERRATA.md).

| Study | Question | Paper | Review verdict |
|---|---|---|---|
| [`astrology-efficacy`](astrology-efficacy/) | Do zodiac signs, planetary dignities or Mercury retrograde predict anything measurable? | [PDF](astrology-efficacy/paper/manuscript.pdf) · [Markdown](astrology-efficacy/paper/manuscript.md) | pass with fixes |
| [`pesticide-breast-cancer-france`](pesticide-breast-cancer-france/) | Is department-level pesticide sales intensity associated with breast cancer mortality in France? | [PDF](pesticide-breast-cancer-france/paper/manuscript.pdf) · [Markdown](pesticide-breast-cancer-france/paper/manuscript.md) | pass with fixes |

## Anatomy of a study folder

```
<slug>/
  idea.md               the question as asked, plus the scope clarified at intake
  literature/           lit_review.md, references.bib, papers.json (raw API hits)
  data/
    provenance.md       source, URL, access date, licence and transformations, per dataset
    candidates.md       datasets considered and rejected
  analysis/
    plan.md             preregistration, frozen at Gate 1
    run_all.py          single entry point that regenerates every number
    NN_*.py             numbered pipeline stages
  results/              results.md, figures/, tables and JSON estimates
  review/               stats_review.md from the independent reviewer agent (Gate 2)
  paper/                manuscript.md / .docx / .pdf
```

Suggested reading order: `idea.md` → `analysis/plan.md` → `review/stats_review.md` → `paper/manuscript.pdf`. Reading the plan before the paper is the quickest way to check that the pipeline did what it said it would.
