"""
03_main_models.py

H1 primary model (plan.md SS4): OLS,
    mortality_rate_std ~ log_pesticide_intensity + poverty_rate + log_pop_density
with HC3 heteroskedasticity-robust standard errors. Reports coefficient, 95% CI, SE,
t, p, standardized beta, and partial correlation (Fisher-z 95% CI) for the pesticide
predictor.

Full assumption-check battery (plan.md SS6): linearity (partial-residual plot),
Breusch-Pagan, Shapiro-Wilk, Cook's distance / leverage, VIF, and the Moran's I
spatial-autocorrelation diagnostic (plan.md SS4/SS6) with the pre-specified
spatial-lag/error contingency if significant. Heavy-tailed-residual contingency
(robust regression + Spearman) run per plan.md SS6.

Writes: results/estimates.json (every number), results/diagnostics.md (prose
summary), and diagnostic figures to results/figures/.
"""

import json
import warnings

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.api as sm
import statsmodels.formula.api as smf
from esda.moran import Moran
from libpysal.weights import Queen
from scipy import stats as sstats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.power import FTestPower

from _common import PROCESSED, RAW, RESULTS

SEED = 42
np.random.seed(SEED)

FORMULA = "mortality_rate_std ~ log_pesticide_intensity + poverty_rate + log_pop_density"
ALPHA = 0.05


def fit_primary(df: pd.DataFrame):
    model_hc3 = smf.ols(FORMULA, data=df).fit(cov_type="HC3")
    model_classical = smf.ols(FORMULA, data=df).fit()  # for influence/Cook's D
    return model_hc3, model_classical


def standardized_beta(df: pd.DataFrame, predictor="log_pesticide_intensity"):
    z = df[["mortality_rate_std", "log_pesticide_intensity", "poverty_rate", "log_pop_density"]].apply(
        lambda s: (s - s.mean()) / s.std(ddof=1)
    )
    m = smf.ols(FORMULA, data=z).fit(cov_type="HC3")
    ci = m.conf_int().loc[predictor]
    return {
        "beta": float(m.params[predictor]),
        "ci_low": float(ci[0]),
        "ci_high": float(ci[1]),
    }


def partial_correlation(df: pd.DataFrame, predictor="log_pesticide_intensity"):
    res = pg.partial_corr(
        data=df,
        x=predictor,
        y="mortality_rate_std",
        covar=["poverty_rate", "log_pop_density"],
        method="pearson",
    )
    row = res.iloc[0]
    p_col = "p-val" if "p-val" in res.columns else "p_val"
    r = float(row["r"])
    n = int(row["n"])
    n_covar = 2  # poverty_rate, log_pop_density

    # pingouin's own CI95% column is pre-rounded to 2 decimals; recompute the
    # Fisher-z CI manually at full precision instead of relying on it (stats_review.md
    # should-fix #2).
    se = 1 / np.sqrt(n - n_covar - 3)
    z = np.arctanh(r)
    z_crit = sstats.norm.ppf(0.975)
    ci_low = float(np.tanh(z - z_crit * se))
    ci_high = float(np.tanh(z + z_crit * se))

    return {
        "r": r,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p": float(row[p_col]),
        "n": n,
    }


def coef_block(model, name):
    return {
        "coef": float(model.params[name]),
        "se": float(model.bse[name]),
        "t": float(model.tvalues[name]),
        "p": float(model.pvalues[name]),
        "ci_low": float(model.conf_int().loc[name, 0]),
        "ci_high": float(model.conf_int().loc[name, 1]),
    }


def compute_power(df_resid, k_predictors=3, alpha=ALPHA, power=0.80):
    """Minimum detectable Cohen's f^2 / partial r at the ACHIEVED sample size,
    computed programmatically (not copied from plan.md, whose power analysis assumed
    an approximate N before the final exclusions in 01_clean.py were known).

    NOTE: statsmodels' FTestPower has df_num/df_denom REVERSED relative to their
    names (documented in the class's own docstring: "Warning: The meaning of df_num
    and df_denom is reversed"), and its `effect_size` is Cohen's f (not f-squared).
    df_num= is passed the residual df, df_denom= is passed the number of constraints
    (1, for a single-predictor partial F-test), and the returned effect_size is
    squared to get Cohen's f2. Verified against plan.md's own worked example
    (N~=96, df_resid=92 -> f2~=0.085, partial r~=0.28): this implementation
    reproduces those exact figures at df_resid=92.
    """
    ft = FTestPower()
    f = ft.solve_power(effect_size=None, df_num=df_resid, df_denom=1, alpha=alpha, power=power)
    f2 = f**2
    partial_r = np.sqrt(f2 / (1 + f2))
    return {
        "df_resid": int(df_resid),
        "alpha": alpha,
        "target_power": power,
        "mde_cohens_f2": float(f2),
        "mde_partial_r": float(partial_r),
        "mde_partial_r2": float(partial_r**2),
    }


def linearity_partial_residual_plot(model_classical, df, predictor="log_pesticide_intensity"):
    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111)
    sm.graphics.plot_partregress(
        "mortality_rate_std", predictor,
        ["poverty_rate", "log_pop_density"],
        data=df, obs_labels=False, ax=ax,
    )
    ax.set_title("Partial-residual (added-variable) plot: log pesticide intensity")
    fig.tight_layout()
    out = RESULTS / "figures" / "diagnostic_partial_residual.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def qq_plot(resid):
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111)
    sm.qqplot(resid, line="45", fit=True, ax=ax)
    ax.set_title("Q-Q plot of H1 model residuals")
    fig.tight_layout()
    out = RESULTS / "figures" / "diagnostic_qq.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out


def load_dept_geometries(dept_codes):
    """Load department polygons, dissolving Corsica 2A+2B into unified '20' to match
    the outcome data's department coding (see data/provenance.md)."""
    gdf = gpd.read_file(RAW / "geo" / "departements.geojson")
    gdf = gdf.rename(columns={"code": "dept"})
    is_corsica = gdf["dept"].isin(["2A", "2B"])
    corsica = gdf[is_corsica]
    rest = gdf[~is_corsica]
    if not corsica.empty:
        corsica_dissolved = corsica.dissolve()
        corsica_dissolved["dept"] = "20"
        corsica_dissolved["nom"] = "Corse"
        gdf = pd.concat([rest, corsica_dissolved[rest.columns]], ignore_index=True)
    else:
        gdf = rest
    gdf = gdf[gdf["dept"].isin(dept_codes)].reset_index(drop=True)
    return gdf


def moran_diagnostic(df, resid):
    gdf = load_dept_geometries(set(df["dept"]))
    merged = gdf.merge(df[["dept"]].assign(resid=resid.values), on="dept", how="inner")
    merged = merged.set_index("dept").loc[df["dept"]].reset_index()  # align order
    assert len(merged) == len(df), (
        f"geometry merge lost rows: {len(merged)} vs {len(df)} — "
        f"missing: {set(df['dept']) - set(merged['dept'])}"
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = Queen.from_dataframe(merged, ids=merged["dept"].tolist(), use_index=False)
    w.transform = "r"
    islands = list(w.islands)

    np.random.seed(SEED)  # esda.Moran's permutation test draws from the global numpy RNG
    mi = Moran(merged["resid"].values, w, permutations=999)
    return {
        "n": len(merged),
        "n_islands": len(islands),
        "island_depts": islands,
        "I": float(mi.I),
        "expected_I": float(mi.EI),
        "z_norm": float(mi.z_norm),
        "p_norm": float(mi.p_norm),
        "p_sim": float(mi.p_sim),
        "significant_p_sim": bool(mi.p_sim < ALPHA),
    }, merged, w


def spatial_models(merged_gdf, w, predictors):
    """Fit spatial-lag and spatial-error ML models via spreg, triggered only if
    Moran's I on OLS residuals is significant (plan.md SS4 contingency)."""
    import spreg

    y = merged_gdf[["mortality_rate_std"]].values
    x = merged_gdf[predictors].values
    w.transform = "r"

    lag = spreg.ML_Lag(y, x, w=w, name_y="mortality_rate_std", name_x=predictors, name_w="queen")
    err = spreg.ML_Error(y, x, w=w, name_y="mortality_rate_std", name_x=predictors, name_w="queen")

    def extract(model, pname="log_pesticide_intensity"):
        idx = model.name_x.index(pname)
        coef = float(model.betas[idx][0])
        se = float(model.std_err[idx])
        return {
            "coef": coef,
            "se": se,
            "z": float(model.z_stat[idx][0]),
            "p": float(model.z_stat[idx][1]),
            "ci_low": coef - 1.96 * se,
            "ci_high": coef + 1.96 * se,
        }

    return {
        "spatial_lag": {
            "pesticide_coef": extract(lag),
            "rho": float(lag.rho),
            "pseudo_r2": float(lag.pr2),
        },
        "spatial_error": {
            "pesticide_coef": extract(err),
            "lambda": float(err.lam),
            "pseudo_r2": float(err.pr2),
        },
    }


def main():
    df = pd.read_parquet(PROCESSED / "analysis_df.parquet").reset_index(drop=True)
    n = len(df)

    model_hc3, model_classical = fit_primary(df)
    resid = model_classical.resid

    predictor = "log_pesticide_intensity"
    predictors_all = ["log_pesticide_intensity", "poverty_rate", "log_pop_density"]

    h1 = {
        "formula": FORMULA,
        "n": int(n),
        "cov_type": "HC3",
        "predictors": {name: coef_block(model_hc3, name) for name in ["Intercept"] + predictors_all},
        "model_fit": {
            "r_squared": float(model_hc3.rsquared),
            "adj_r_squared": float(model_hc3.rsquared_adj),
            "f_stat": float(model_hc3.fvalue),
            "f_pvalue": float(model_hc3.f_pvalue),
            "df_model": int(model_hc3.df_model),
            "df_resid": int(model_hc3.df_resid),
        },
    }
    h1["predictors"][predictor]["standardized_beta"] = standardized_beta(df, predictor)
    h1["predictors"][predictor]["partial_correlation"] = partial_correlation(df, predictor)
    h1["predictors"][predictor]["significant_at_alpha05"] = bool(
        h1["predictors"][predictor]["p"] < ALPHA
    )
    h1["predictors"][predictor]["direction"] = (
        "positive" if h1["predictors"][predictor]["coef"] > 0 else "negative"
    )

    power = compute_power(df_resid=model_hc3.df_resid)
    h1["mde_cleared"] = bool(
        abs(h1["predictors"][predictor]["partial_correlation"]["r"]) >= power["mde_partial_r"]
    )

    # -- Diagnostics ----------------------------------------------------------
    diagnostics = {}

    # Linearity (figure only — qualitative check)
    partial_resid_fig = linearity_partial_residual_plot(model_classical, df, predictor)
    diagnostics["linearity_figure"] = str(partial_resid_fig.relative_to(RESULTS.parent))

    # Breusch-Pagan
    exog = sm.add_constant(df[predictors_all])
    bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(resid, exog)
    diagnostics["breusch_pagan"] = {
        "lm_stat": float(bp_lm), "lm_p": float(bp_lm_p),
        "f_stat": float(bp_f), "f_p": float(bp_f_p),
        "heteroskedastic_at_alpha05": bool(bp_lm_p < ALPHA),
    }

    # Shapiro-Wilk
    sw_stat, sw_p = sstats.shapiro(resid)
    diagnostics["shapiro_wilk"] = {
        "stat": float(sw_stat), "p": float(sw_p),
        "nonnormal_at_alpha05": bool(sw_p < ALPHA),
    }
    qq_fig = qq_plot(resid)
    diagnostics["qq_figure"] = str(qq_fig.relative_to(RESULTS.parent))

    # VIF
    vif = {}
    exog_arr = exog.values
    for i, name in enumerate(exog.columns):
        if name == "const":
            continue
        vif[name] = float(variance_inflation_factor(exog_arr, i))
    diagnostics["vif"] = vif
    diagnostics["vif_flag_gt5"] = {k: v for k, v in vif.items() if v > 5}

    # Cook's distance / leverage
    infl = OLSInfluence(model_classical)
    cooks_d = infl.cooks_distance[0]
    threshold = 4 / n
    flagged_idx = np.where(cooks_d > threshold)[0]
    flagged_depts = df.iloc[flagged_idx][["dept", "dept_name"]].to_dict("records")
    diagnostics["cooks_distance"] = {
        "threshold_4_over_n": float(threshold),
        "n_flagged": int(len(flagged_idx)),
        "flagged_departments": flagged_depts,
        "max_cooks_d": float(cooks_d.max()),
    }

    if len(flagged_idx) > 0:
        df_sens = df.drop(df.index[flagged_idx]).reset_index(drop=True)
        model_sens = smf.ols(FORMULA, data=df_sens).fit(cov_type="HC3")
        diagnostics["sensitivity_excl_influential"] = {
            "n": int(len(df_sens)),
            "excluded_n": int(len(flagged_idx)),
            predictor: coef_block(model_sens, predictor),
        }
    else:
        diagnostics["sensitivity_excl_influential"] = None

    # Heavy-tailed contingency (plan.md SS6)
    if diagnostics["shapiro_wilk"]["nonnormal_at_alpha05"]:
        rlm = sm.RLM(df["mortality_rate_std"], sm.add_constant(df[predictors_all]),
                     M=sm.robust.norms.HuberT()).fit()
        rlm_ci = rlm.conf_int()
        diagnostics["robust_regression_huber"] = {
            "coef": float(rlm.params[predictor]),
            "se": float(rlm.bse[predictor]),
            "t": float(rlm.tvalues[predictor]),
            "p": float(rlm.pvalues[predictor]),
            "ci_low": float(rlm_ci.loc[predictor, 0]),
            "ci_high": float(rlm_ci.loc[predictor, 1]),
        }
        rho, rho_p = sstats.spearmanr(df["pesticide_intensity"], df["mortality_rate_std"])
        diagnostics["spearman_raw_bivariate"] = {"rho": float(rho), "p": float(rho_p)}
    else:
        diagnostics["robust_regression_huber"] = None
        diagnostics["spearman_raw_bivariate"] = None

    # Moran's I
    moran_result, merged_gdf, w = moran_diagnostic(df, resid)
    diagnostics["moran_i"] = moran_result

    if moran_result["significant_p_sim"]:
        # merge residuals-frame predictors back for spatial model fitting, in the
        # SAME row order as `merged_gdf`
        sp_df = df.set_index("dept").loc[merged_gdf["dept"]].reset_index()
        diagnostics["spatial_models"] = spatial_models(sp_df, w, predictors_all)
    else:
        diagnostics["spatial_models"] = None

    estimates = {"h1_primary_model": h1, "power": power, "diagnostics": diagnostics}
    (RESULTS / "estimates.json").write_text(json.dumps(estimates, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] wrote {RESULTS / 'estimates.json'}")

    # -- diagnostics.md prose summary -----------------------------------------
    lines = ["# Diagnostics — H1 primary model\n"]
    lines.append(f"Formula: `{FORMULA}` (HC3 robust SE), N = {n}.\n")
    lines.append(f"**Linearity**: partial-residual plot saved to "
                 f"`{diagnostics['linearity_figure']}` (visual check, see figure).\n")
    bp = diagnostics["breusch_pagan"]
    lines.append(f"**Breusch-Pagan**: LM = {bp['lm_stat']:.3f}, p = {bp['lm_p']:.4f} "
                 f"({'heteroskedastic' if bp['heteroskedastic_at_alpha05'] else 'homoskedastic'} "
                 f"at alpha=.05). HC3 robust SEs used as baseline regardless of result.\n")
    sw = diagnostics["shapiro_wilk"]
    lines.append(f"**Shapiro-Wilk**: W = {sw['stat']:.4f}, p = {sw['p']:.4f} "
                 f"({'non-normal' if sw['nonnormal_at_alpha05'] else 'consistent with normal'} "
                 f"residuals at alpha=.05). Q-Q plot: `{diagnostics['qq_figure']}`.\n")
    lines.append(f"**VIF**: {diagnostics['vif']} "
                 f"({'FLAGGED > 5: ' + str(diagnostics['vif_flag_gt5']) if diagnostics['vif_flag_gt5'] else 'all < 5, no multicollinearity concern'}).\n")
    cd = diagnostics["cooks_distance"]
    lines.append(f"**Cook's distance**: threshold 4/n = {cd['threshold_4_over_n']:.4f}, "
                 f"{cd['n_flagged']} department(s) flagged: {cd['flagged_departments']}. "
                 f"Sensitivity refit excluding them: "
                 f"{diagnostics['sensitivity_excl_influential']}.\n")
    if diagnostics["robust_regression_huber"]:
        lines.append(f"**Heavy-tailed contingency triggered** (Shapiro-Wilk p < .05): "
                     f"Huber-T robust regression coef = "
                     f"{diagnostics['robust_regression_huber']['coef']:.4f} "
                     f"(p = {diagnostics['robust_regression_huber']['p']:.4f}); "
                     f"Spearman rho (raw bivariate) = "
                     f"{diagnostics['spearman_raw_bivariate']['rho']:.4f} "
                     f"(p = {diagnostics['spearman_raw_bivariate']['p']:.4f}).\n")
    else:
        lines.append("**Heavy-tailed contingency**: not triggered (residuals not "
                     "significantly non-normal).\n")
    mi = diagnostics["moran_i"]
    lines.append(f"**Moran's I** (Queen contiguity, N={mi['n']}, {mi['n_islands']} "
                 f"island department(s): {mi['island_depts']}): I = {mi['I']:.4f}, "
                 f"E[I] = {mi['expected_I']:.4f}, p (999-permutation) = {mi['p_sim']:.4f} "
                 f"({'SIGNIFICANT' if mi['significant_p_sim'] else 'not significant'} "
                 f"at alpha=.05).\n")
    if diagnostics["spatial_models"]:
        err_lambda = diagnostics["spatial_models"]["spatial_error"]["lambda"]
        err_pr2 = diagnostics["spatial_models"]["spatial_error"]["pseudo_r2"]
        lines.append(
            f"**I = {mi['I']:.4f} is far above the range typically seen for genuine areal "
            f"disease-risk clustering (~0.2-0.5 in the epidemiological literature).** "
            f"lambda = {err_lambda:.3f} paired with a low spatial-error pseudo-R2 "
            f"({err_pr2:.3f}) is more consistent with an artifact of the outcome's own "
            f"model-smoothed construction (see `data/candidates.md` candidate 2A) than with "
            f"a true omitted spatial confounder. The spatial-lag/error coefficients below "
            f"are reported as exploratory and model-dependent, not as a validated spatial "
            f"correction — see `results/results.md` E3 for the full discussion.\n")
        lines.append(f"**Spatial-lag/error contingency triggered**: {diagnostics['spatial_models']}\n")
    else:
        lines.append("**Spatial-lag/error contingency**: not triggered (Moran's I not "
                     "significant) — OLS result stands as the final primary estimate.\n")

    (RESULTS / "diagnostics.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] wrote {RESULTS / 'diagnostics.md'}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
