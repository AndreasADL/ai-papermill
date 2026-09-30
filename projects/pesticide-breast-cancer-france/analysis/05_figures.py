"""
05_figures.py

Publication-quality figures (300 dpi PNG) to results/figures/:
  1. fig1_scatter_pesticide_mortality.png — bivariate scatter, pesticide sales
     intensity (kg a.s./ha/year, real units on a log x-axis) vs. breast cancer
     mortality rate, with an unadjusted log-linear fit line + 95% CI band. N in
     caption; the adjusted (confounder-controlled) H1 estimate is reported
     separately in the caption for context, not conflated with this bivariate fit.
  2. fig2_robustness_forest.png — pesticide coefficient + 95% CI across the H1
     primary model and all robustness/sensitivity checks (plan.md SS7), forest-plot
     style.

Colorblind-safe palette (Okabe-Ito blue/orange), no chartjunk, axis labels with
units throughout.
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from _common import PROCESSED, RESULTS

SEED = 42
np.random.seed(SEED)

# Okabe-Ito colorblind-safe palette
BLUE = "#0072B2"
DARK_BLUE = "#00456B"
ORANGE = "#E69F00"
GRAY = "#4D4D4D"
LIGHT_GRAY = "#B0B0B0"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": GRAY,
    "axes.labelcolor": "black",
    "text.color": "black",
    "xtick.color": GRAY,
    "ytick.color": GRAY,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def fig1_scatter(df, estimates):
    x = df["log_pesticide_intensity"].values
    y = df["mortality_rate_std"].values
    n = len(df)

    X = sm.add_constant(x)
    bivar = sm.OLS(y, X).fit()

    x_grid = np.linspace(x.min(), x.max(), 200)
    pred = bivar.get_prediction(sm.add_constant(x_grid))
    mean = pred.predicted_mean
    ci = pred.conf_int(alpha=0.05)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.scatter(
        np.exp(x), y, s=34, color=BLUE, alpha=0.75, edgecolor="white", linewidth=0.5,
        zorder=3, label=f"Department (N={n})",
    )
    ax.plot(np.exp(x_grid), mean, color=DARK_BLUE, linewidth=2, zorder=4,
            label="Unadjusted log-linear fit")
    ax.fill_between(np.exp(x_grid), ci[:, 0], ci[:, 1], color=BLUE, alpha=0.15,
                     zorder=2, label="95% CI (unadjusted)")

    ax.set_xscale("log")
    ax.set_xlabel("Pesticide sales intensity (kg active substance / ha / year, log scale)")
    ax.set_ylabel("Female breast cancer mortality rate\n(age-standardized, per 100,000; 2007-2014)")
    ax.set_title("Pesticide sales intensity vs. breast cancer mortality,\nmainland French departments")
    ax.grid(True, which="major", axis="both", color=LIGHT_GRAY, linewidth=0.4, alpha=0.5, zorder=0)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)

    h1 = estimates["h1_primary_model"]["predictors"]["log_pesticide_intensity"]
    caption = (
        f"N = {n} mainland French departments (2007-2014 mortality; 2008-2014 sales; "
        f"4 non-agricultural departments excluded — see provenance.md). Line shows the "
        f"UNADJUSTED bivariate log-linear relationship (for visualization only). The "
        f"pre-specified, confounder-adjusted H1 primary model estimate is "
        f"beta = {h1['coef']:.3f}, 95% CI [{h1['ci_low']:.3f}, {h1['ci_high']:.3f}], "
        f"p = {h1['p']:.3f} (HC3 robust SE, adjusting for poverty rate and log "
        f"population density)."
    )
    fig.text(0.02, -0.02, caption, ha="left", va="top", fontsize=7.5, wrap=True,
              transform=fig.transFigure)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    out = RESULTS / "figures" / "fig1_scatter_pesticide_mortality.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out}")


def fig2_robustness_forest(robustness):
    labels, coefs, los, his, colors = [], [], [], [], []

    def add(label, block, color=BLUE):
        labels.append(label)
        coefs.append(block["coef"])
        los.append(block["coef"] - block["ci_low"])
        his.append(block["ci_high"] - block["coef"])
        colors.append(color)

    add("H1 primary\n(sales, log)", robustness["h1_primary"], DARK_BLUE)
    add("1. Purchase-based\nexposure", robustness["check_1_purchase_based_exposure"])
    add("2. Linear (non-log)\nexposure", robustness["check_2_linear_exposure"])
    add("3. FRANCIM E2\n(direction only, N=19)", robustness["check_3_francim_incidence_e2"], ORANGE)
    sp = robustness["check_4_spatial_model_comparison"]
    if sp["spatial_lag"]:
        add("4a. Spatial lag", sp["spatial_lag"])
        add("4b. Spatial error", sp["spatial_error"])

    y_pos = np.arange(len(labels))[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.62 * len(labels) + 1.3))
    for i, (c, lo, hi, col) in enumerate(zip(coefs, los, his, colors)):
        ax.errorbar(c, y_pos[i], xerr=[[lo], [hi]], fmt="o", color=col, ecolor=col,
                    elinewidth=1.8, capsize=3, markersize=6, zorder=3)
    ax.axvline(0, color=GRAY, linewidth=1, linestyle="--", zorder=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Pesticide-exposure coefficient (model-specific units) + 95% CI")
    ax.set_title("Robustness of the pesticide-mortality association across specifications")
    ax.grid(True, axis="x", color=LIGHT_GRAY, linewidth=0.4, alpha=0.5, zorder=0)
    fig.tight_layout()
    out = RESULTS / "figures" / "fig2_robustness_forest.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out}")


def main():
    (RESULTS / "figures").mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED / "analysis_df.parquet")
    estimates = json.loads((RESULTS / "estimates.json").read_text(encoding="utf-8"))
    robustness = json.loads((RESULTS / "robustness.json").read_text(encoding="utf-8"))

    fig1_scatter(df, estimates)
    fig2_robustness_forest(robustness)


if __name__ == "__main__":
    main()
