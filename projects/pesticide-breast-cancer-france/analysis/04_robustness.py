"""
04_robustness.py

The four robustness checks pre-specified in plan.md SS7:
  1. Alternative exposure measure: purchase-based (buyer postal code, 2013-2023)
     BNV-D exposure vs. the primary distributor-sales-based measure (2008-2014).
  2. Untransformed (linear) pesticide_intensity in place of the log-transformed
     primary specification.
  3. Outcome robustness (E2): FRANCIM observed incidence (2018-2022), ~20 registry
     departments, same confounder-adjusted model — sign/direction consistency check
     only (power analysis in plan.md SS5 shows this subsample cannot support an
     independently powered test).
  4. Spatial-model comparison (E3): OLS vs. spatial-lag/error pesticide coefficient
     (pulled from results/estimates.json, produced by 03_main_models.py, since
     that comparison is only triggered there when Moran's I is significant).

Writes results/robustness.json (all numbers) and results/robustness.md (summary
table + narrative: does sign/magnitude/significance of the pesticide coefficient
hold across checks?).
"""

import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from _common import (
    PROCESSED,
    RESULTS,
    load_bnvd_achat_totals,
    load_bnvd_vente_totals,
    load_density,
    load_francim_incidence,
    load_poverty,
    load_sau,
)

SEED = 42
np.random.seed(SEED)

ACHAT_YEARS = list(range(2013, 2024))
VENTE_YEARS_E2 = [2018, 2019, 2020, 2021, 2022]
NONAG_SAU_THRESHOLD = 10_000  # same exclusion rule as 01_clean.py, applied consistently


def fit_and_extract(df, formula, predictor):
    m = smf.ols(formula, data=df).fit(cov_type="HC3")
    ci = m.conf_int().loc[predictor]
    return {
        "n": int(m.nobs),
        "coef": float(m.params[predictor]),
        "se": float(m.bse[predictor]),
        "t": float(m.tvalues[predictor]),
        "p": float(m.pvalues[predictor]),
        "ci_low": float(ci[0]),
        "ci_high": float(ci[1]),
        "r_squared": float(m.rsquared),
    }


def check_1_purchase_based(primary_df):
    """E1: purchase-based exposure (2013-2023) in place of sales-based (2008-2014).
    Same mortality outcome and confounders as the primary model; only the exposure
    construction changes."""
    achat = load_bnvd_achat_totals(ACHAT_YEARS)
    sau = load_sau()
    merged = achat.merge(sau, on="dept", how="left")
    merged = merged[merged["sau_ha"] >= NONAG_SAU_THRESHOLD]
    merged["pesticide_intensity_purchase"] = (
        merged["pesticide_kg_total_purchase"] / len(ACHAT_YEARS) / merged["sau_ha"]
    )
    merged["log_pesticide_intensity_purchase"] = np.log(merged["pesticide_intensity_purchase"])

    df = primary_df[["dept", "mortality_rate_std", "poverty_rate", "log_pop_density"]].merge(
        merged[["dept", "log_pesticide_intensity_purchase"]], on="dept", how="inner"
    )
    formula = "mortality_rate_std ~ log_pesticide_intensity_purchase + poverty_rate + log_pop_density"
    result = fit_and_extract(df, formula, "log_pesticide_intensity_purchase")
    result["description"] = (
        f"Purchase-based (buyer postal code, {ACHAT_YEARS[0]}-{ACHAT_YEARS[-1]}) exposure "
        f"in place of distributor-sales-based exposure (2008-2014); same mortality outcome "
        f"and confounders."
    )
    return result


def check_2_linear_exposure(primary_df):
    """Untransformed (linear) pesticide_intensity in place of log."""
    formula = "mortality_rate_std ~ pesticide_intensity + poverty_rate + log_pop_density"
    result = fit_and_extract(primary_df, formula, "pesticide_intensity")
    result["description"] = "Linear (non-log) pesticide_intensity in place of log-transformed primary specification."
    return result


def check_3_francim_e2():
    """E2: FRANCIM observed incidence (2018-2022), ~20 registry departments, paired
    with BNV-D sales 2018-2022 and Agreste RA2020 SAU. Sign/direction consistency
    check ONLY — the ~20-department subsample cannot support an independently
    powered significance test (plan.md SS5)."""
    incidence = load_francim_incidence()
    incidence_mainland = incidence[~incidence["is_dom"]].drop(columns=["is_dom"])

    vente_e2 = load_bnvd_vente_totals(VENTE_YEARS_E2)
    sau = load_sau()
    poverty = load_poverty(2020)
    density = load_density(2021)  # closer vintage to the 2018-2022 E2 period than 2011

    exposure = vente_e2.merge(sau, on="dept", how="left")
    exposure = exposure[exposure["sau_ha"] >= NONAG_SAU_THRESHOLD]
    exposure["pesticide_intensity_e2"] = (
        exposure["pesticide_kg_total"] / len(VENTE_YEARS_E2) / exposure["sau_ha"]
    )
    exposure["log_pesticide_intensity_e2"] = np.log(exposure["pesticide_intensity_e2"])

    df = incidence_mainland.merge(exposure[["dept", "log_pesticide_intensity_e2"]], on="dept", how="inner")
    df = df.merge(poverty, on="dept", how="left")
    df = df.merge(density, on="dept", how="left")
    df = df.rename(columns={"incidence_rate_std": "incidence_rate"})
    df = df.dropna(subset=["incidence_rate", "log_pesticide_intensity_e2", "poverty_rate", "pop_density"])
    df["log_pop_density"] = np.log(df["pop_density"])

    formula = "incidence_rate ~ log_pesticide_intensity_e2 + poverty_rate + log_pop_density"
    result = fit_and_extract(df, formula, "log_pesticide_intensity_e2")
    result["description"] = (
        "FRANCIM observed incidence (2018-2022), registry departments, paired with BNV-D "
        "sales 2018-2022 and RA2020 SAU. SIGN/DIRECTION CONSISTENCY CHECK ONLY per the "
        "plan.md SS5 power analysis (N too small for an independently powered test) — "
        "not interpreted on significance."
    )
    result["departments_used"] = sorted(df["dept"].tolist())
    return result


def check_4_spatial(estimates):
    h1 = estimates["h1_primary_model"]["predictors"]["log_pesticide_intensity"]
    diag = estimates["diagnostics"]
    result = {
        "ols": {"coef": h1["coef"], "p": h1["p"], "n": estimates["h1_primary_model"]["n"]},
        "moran_i_significant": diag["moran_i"]["significant_p_sim"],
    }
    if diag["spatial_models"]:
        result["spatial_lag"] = diag["spatial_models"]["spatial_lag"]["pesticide_coef"]
        result["spatial_error"] = diag["spatial_models"]["spatial_error"]["pesticide_coef"]
    else:
        result["spatial_lag"] = None
        result["spatial_error"] = None
    result["description"] = (
        "OLS vs. spatial-lag/error pesticide coefficient, triggered because Moran's I on "
        "H1 residuals was significant (see results/diagnostics.md)."
    )
    return result


def main():
    primary_df = pd.read_parquet(PROCESSED / "analysis_df.parquet")
    estimates = json.loads((RESULTS / "estimates.json").read_text(encoding="utf-8"))
    h1_coef = estimates["h1_primary_model"]["predictors"]["log_pesticide_intensity"]

    checks = {
        "h1_primary": {
            "n": estimates["h1_primary_model"]["n"],
            "coef": h1_coef["coef"],
            "p": h1_coef["p"],
            "ci_low": h1_coef["ci_low"],
            "ci_high": h1_coef["ci_high"],
            "description": "Primary H1 model (sales-based, log exposure, mortality 2007-2014).",
        },
        "check_1_purchase_based_exposure": check_1_purchase_based(primary_df),
        "check_2_linear_exposure": check_2_linear_exposure(primary_df),
        "check_3_francim_incidence_e2": check_3_francim_e2(),
        "check_4_spatial_model_comparison": check_4_spatial(estimates),
    }

    (RESULTS / "robustness.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[ok] wrote {RESULTS / 'robustness.json'}")

    def sign(x):
        return "+" if x is not None and x > 0 else ("-" if x is not None else "n/a")

    h1_sign = sign(h1_coef["coef"])

    rows = []
    rows.append(("H1 primary (sales, log)", checks["h1_primary"]["coef"],
                  checks["h1_primary"]["p"], checks["h1_primary"]["n"],
                  sign(checks["h1_primary"]["coef"]) == h1_sign))
    c1 = checks["check_1_purchase_based_exposure"]
    rows.append(("1. Purchase-based exposure", c1["coef"], c1["p"], c1["n"], sign(c1["coef"]) == h1_sign))
    c2 = checks["check_2_linear_exposure"]
    rows.append(("2. Linear (non-log) exposure", c2["coef"], c2["p"], c2["n"], sign(c2["coef"]) == h1_sign))
    c3 = checks["check_3_francim_incidence_e2"]
    rows.append(("3. FRANCIM incidence E2 (direction only)", c3["coef"], c3["p"], c3["n"],
                  sign(c3["coef"]) == h1_sign))
    c4 = checks["check_4_spatial_model_comparison"]
    if c4["spatial_lag"]:
        rows.append(("4a. Spatial lag", c4["spatial_lag"]["coef"], c4["spatial_lag"]["p"],
                      checks["h1_primary"]["n"], sign(c4["spatial_lag"]["coef"]) == h1_sign))
        rows.append(("4b. Spatial error", c4["spatial_error"]["coef"], c4["spatial_error"]["p"],
                      checks["h1_primary"]["n"], sign(c4["spatial_error"]["coef"]) == h1_sign))

    table_df = pd.DataFrame(rows, columns=["Check", "Coef (pesticide)", "p", "N", "Sign matches H1"])
    table_df["Coef (pesticide)"] = table_df["Coef (pesticide)"].round(4)
    table_df["p"] = table_df["p"].round(4)

    lines = [
        "# Robustness checks (plan.md SS7)\n",
        f"H1 primary pesticide coefficient: {checks['h1_primary']['coef']:.4f} "
        f"(p = {checks['h1_primary']['p']:.4f}, N = {checks['h1_primary']['n']}), "
        f"direction: {'positive' if h1_coef['coef'] > 0 else 'negative'}.\n",
        "## Summary table\n",
        table_df.to_markdown(index=False),
        "\n## Detail\n",
    ]
    for key in ["check_1_purchase_based_exposure", "check_2_linear_exposure",
                "check_3_francim_incidence_e2", "check_4_spatial_model_comparison"]:
        lines.append(f"### {key}\n")
        lines.append(f"```json\n{json.dumps(checks[key], indent=2, ensure_ascii=False)}\n```\n")

    robustness_rows = table_df.iloc[1:]  # exclude the H1 row itself
    n_sign_match = int(robustness_rows["Sign matches H1"].sum())
    n_total = len(robustness_rows)
    sig_rows = robustness_rows[robustness_rows["p"] < 0.05]
    n_sig = len(sig_rows)
    sig_desc = (
        ", ".join(f"{r.Check} (p={r.p:.4f})" for r in sig_rows.itertuples())
        if n_sig > 0 else "none"
    )
    lines.append(
        f"\n**Overall**: sign of the pesticide coefficient matches the H1 primary "
        f"direction in {n_sign_match}/{n_total} robustness checks (excluding the "
        f"H1 row itself; check 3/FRANCIM E2 counted for direction only, per its "
        f"pre-specified power caveat). {n_sig}/{n_total} robustness/sensitivity "
        f"specifications reach p < .05: {sig_desc}. The H1 primary specification "
        f"itself is non-significant (p = {checks['h1_primary']['p']:.4f}); the fact "
        f"that one alternative specification (purchase-based exposure) crosses the "
        f"nominal .05 threshold while the primary, pre-registered specification does "
        f"not is reported here at face value, not treated as confirmatory — H1's "
        f"pre-specified inference criterion (plan.md SS4) is the primary model only.\n"
    )

    (RESULTS / "robustness.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] wrote {RESULTS / 'robustness.md'}")
    print("\n".join(lines[:20]))


if __name__ == "__main__":
    main()
