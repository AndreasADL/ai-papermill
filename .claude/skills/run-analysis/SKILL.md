---
name: run-analysis
description: Execute the approved analysis plan as reproducible Python scripts with assumption checks, effect sizes, and publication-quality figures. Use in the analysis phase after GATE 1 approval.
---

# Run Analysis

Execute `analysis/plan.md` exactly. All code in numbered scripts under `analysis/`, orchestrated by `run_all.py`. A fresh run must reproduce every reported number.

## Script conventions
- `00_download.py` → `data/raw/`; `01_clean.py` → `data/processed/analysis_df.parquet`; `02_descriptives.py`; `03_main_models.py`; `04_robustness.py`; `05_figures.py`.
- Top of every script: `SEED = 42`, set for numpy/random. Print key outputs; also write every estimate the paper will cite (estimate, CI, SE, N, p) to `results/estimates.json`.
- `requirements.txt` with pinned versions of used packages.

## Cleaning (01)
- Log every step and row-count change: initial N → after each exclusion → final N. Write this flow into `results/results.md` (needed for the paper's sample section).
- Never overwrite raw data. Assert expected dtypes/ranges after cleaning (e.g., age 18–100); fail loudly on violations.

## Descriptives (02)
- Table: N, mean/SD or %, min/max, missingness per analysis variable. Correlation matrix of main variables. Scale reliability if applicable.

## Main models (03)
- Exactly as pre-specified. Report per hypothesis: estimate, 95% CI, SE, test statistic, p, effect size, N.
- Run all pre-specified diagnostics. If one fails, run the pre-specified fallback and report BOTH.
- Apply the pre-specified multiplicity correction; report raw and adjusted p.

## Robustness (04)
- Each planned check; one summary table: does sign/magnitude/significance of the key estimate hold?

## Figures (05)
- matplotlib/seaborn, 300 dpi PNG to `results/figures/`. Axis labels with units, N in caption. Key associations: scatter with fit line + CI band (jitter/alpha for large N). Colorblind-safe palette, no chartjunk.

## results.md
Per hypothesis: plain-language finding; a statistics sentence ready for the paper (e.g., "r = .21, 95% CI [.15, .27], p < .001, N = 1,204"); figure/table reference; diagnostic outcome; robustness summary. Then a clearly-headed **Exploratory** section for anything not pre-specified.

## Rules
- Numbers in results.md must be programmatically produced (read from estimates.json where possible), never typed from memory.
- If results contradict hypotheses, report them exactly as found. Null results are results.
- Finish by running `python analysis/run_all.py` end-to-end; it must complete without errors.
