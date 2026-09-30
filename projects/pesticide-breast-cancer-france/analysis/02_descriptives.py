"""
02_descriptives.py

Descriptive statistics for the four primary analysis variables (outcome, exposure,
2 confounders) plus a correlation matrix. Writes results/descriptives.md and
results/correlation_matrix.csv.
"""

import numpy as np
import pandas as pd

from _common import PROCESSED, RESULTS

SEED = 42
np.random.seed(SEED)

VARS = {
    "mortality_rate_std": "Breast cancer mortality rate (age-std., /100,000)",
    "pesticide_intensity": "Pesticide sales intensity, linear (kg a.s./ha/year)",
    "log_pesticide_intensity": "Pesticide sales intensity, log (ln kg a.s./ha/year)",
    "poverty_rate": "Poverty rate (%, 2020 vintage)",
    "pop_density": "Population density, linear (inhab/km2, 2011 vintage)",
    "log_pop_density": "Population density, log (ln inhab/km2, 2011 vintage)",
}


def main():
    df = pd.read_parquet(PROCESSED / "analysis_df.parquet")
    n = len(df)

    rows = []
    for col, label in VARS.items():
        s = df[col]
        rows.append(
            {
                "Variable": label,
                "N": s.notna().sum(),
                "Missing": s.isna().sum(),
                "Mean": round(s.mean(), 3),
                "SD": round(s.std(), 3),
                "Min": round(s.min(), 3),
                "Max": round(s.max(), 3),
            }
        )
    desc = pd.DataFrame(rows)

    corr_cols = [
        "mortality_rate_std",
        "log_pesticide_intensity",
        "poverty_rate",
        "log_pop_density",
    ]
    corr = df[corr_cols].corr(method="pearson").round(3)
    corr.to_csv(RESULTS / "correlation_matrix.csv")

    lines = [
        "# Descriptive statistics\n",
        f"N = {n} mainland French departments (after all exclusions — see "
        f"`sample_flow.md`).\n",
        "## Table 1. Analysis variables\n",
        desc.to_markdown(index=False),
        "\n## Correlation matrix (Pearson r) — primary model variables\n",
        corr.to_markdown(),
        "\n",
    ]
    (RESULTS / "descriptives.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[ok] wrote {RESULTS / 'descriptives.md'} and "
          f"{RESULTS / 'correlation_matrix.csv'}")


if __name__ == "__main__":
    main()
