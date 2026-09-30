"""
05_study1_rdd.py — Study 1: zodiac-cusp regression discontinuity.

Executes analysis/plan.md §1.2 and §3 (Study 1) and the falsification battery of §4.

Design in one line: a person born just before a cusp and one born just after share
season, photoperiod, maternal conditions and school cohort, but are assigned opposite
planetary dignities. If dignity predicts vocation, the occupation share jumps at the
cusp; if only seasonality is at work, it passes through smoothly.

Confirmatory family (3 tests): H1-Me, H1-Ve, H1-Ma — one pooled, directionally-signed
discontinuity per planet. H1-Su was dropped from the confirmatory set at GATE 1
(see hypotheses.py); the Sun is carried here as EXPLORATORY only.

Outputs: results/estimates_study1.json, results/study1_*.csv
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from rdrobust import rdrobust

# rdrobust prints "Mass points detected in the running variable." on every call and
# emits divide-by-zero RuntimeWarnings from its bandwidth selector on sparse cusps.
# Both are expected here (the running variable is daily, hence discrete) and would
# otherwise bury the actual output under tens of thousands of lines.
warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

SEED = inf.SEED
np.random.seed(SEED)

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CONFIRMATORY = ["mercury", "venus", "mars"]
EXPLORATORY = ["sun"]

# plan §3: analysis window around each cusp. Estimation is local-linear inside an
# MSE-optimal bandwidth; this outer window only bounds the data handed to the
# estimator and is always far wider than any selected bandwidth.
WINDOW = 30.0

# plan §0: solar bandwidth is capped at 7 days so that day-of-month 1 -- the only
# substantial heap (ratio 1.230) -- stays outside the window for every solar ingress,
# which always falls on day-of-month 19-23. Planetary ingresses scatter across all
# days of the month, so day-of-month is orthogonal to the running variable there and
# no cap is needed.
SOLAR_H_CAP = 7.0

BW_GRID = [3, 5, 7, 10, 14, 21]          # plan §3 sensitivity curve
PLACEBO_OFFSETS = [-20, -10, 10, 20]     # plan §4.2
SESOI_OR = 1.05                          # plan §2.2

# vce: the plan specifies robust bias-corrected CIs but not the variance estimator.
# HC1 is used rather than rdrobust's default nearest-neighbour estimator because the
# outcome is binary (the NN estimator is built for continuous outcomes) and because
# NN variance is ~50x slower on samples of this size. Measured difference on the
# Gemini->Cancer cusp: robust SE .00651 (HC1) vs .00633 (NN) -- HC1 is marginally
# CONSERVATIVE, so it cannot manufacture a rejection.
VCE = "hc1"

log: list[str] = []


def note(msg: str = "") -> None:
    print(msg, flush=True)
    log.append(msg)


def rd_fit(y: np.ndarray, x: np.ndarray, h: float | None = None,
           h_cap: float | None = None) -> dict:
    """
    One local-linear RD fit. Returns the bias-corrected estimate paired with the
    robust SE (rdrobust's third row), which is the internally consistent pair for
    inference, plus the conventional point estimate for reporting.
    """
    if len(y) < 200 or np.unique(x).size < 10:
        return {"est": np.nan, "se": np.nan, "est_conv": np.nan, "se_conv": np.nan,
                "h": np.nan, "n_left": 0, "n_right": 0, "n": int(len(y))}
    try:
        kw = dict(y=y, x=x, kernel="triangular", vce=VCE)
        if h is not None:
            kw["h"] = h
        with contextlib.redirect_stdout(io.StringIO()):
            r = rdrobust(**kw)
            h_used = float(np.ravel(r.bws.values)[0]) if h is None else float(h)
            # Re-fit if the MSE-optimal bandwidth exceeds a pre-registered cap.
            if h is None and h_cap is not None and h_used > h_cap:
                r = rdrobust(y=y, x=x, kernel="triangular", vce=VCE, h=h_cap)
                h_used = h_cap
        coef = np.ravel(r.coef.values)
        se = np.ravel(r.se.values)
        # N_h is a plain list of ints, not a DataFrame -- unlike coef/se/bws.
        nh = np.ravel(np.asarray(r.N_h))
        return {"est": float(coef[2]), "se": float(se[2]),
                "est_conv": float(coef[0]), "se_conv": float(se[0]),
                "h": h_used, "n_left": int(nh[0]), "n_right": int(nh[1]),
                "n": int(len(y))}
    except Exception as exc:  # noqa: BLE001
        return {"est": np.nan, "se": np.nan, "est_conv": np.nan, "se_conv": np.nan,
                "h": np.nan, "n_left": 0, "n_right": 0, "n": int(len(y)),
                "error": str(exc)}


def per_cusp(df: pd.DataFrame, planet: str, outcome: str, *,
             shift: float = 0.0, donut: float = 0.0, h: float | None = None,
             h_cap: float | None = None, drop_heaped: bool = False,
             directions: dict | None = None) -> pd.DataFrame:
    """Fit the RD at every cusp of one planet and attach the pre-registered direction."""
    run_col, cusp_col = f"{planet}_running", f"{planet}_cusp"
    rows = []
    for cusp, g in df.groupby(cusp_col, observed=True):
        if "->" not in str(cusp):
            continue
        x = g[run_col].to_numpy(dtype=float) - shift
        y = g[outcome].to_numpy(dtype=float)
        keep = np.abs(x) <= WINDOW
        if donut > 0:
            keep &= np.abs(x) >= donut
        if drop_heaped:
            keep &= ~g["is_heaped_day"].to_numpy(dtype=bool)
        if keep.sum() < 200:
            continue
        fit = rd_fit(y[keep], x[keep], h=h, h_cap=h_cap)
        fit["cusp"] = str(cusp)
        fit["planet"] = planet
        if directions is not None:
            fit["pred_dir"] = int(directions.get(str(cusp), 0))
        rows.append(fit)
    return pd.DataFrame(rows)


def main() -> int:
    t_start = time.perf_counter()
    note("# Study 1 — Zodiac-cusp regression discontinuity\n")
    note(f"Seed {SEED}. Estimator: rdrobust local-linear, triangular kernel, "
         f"vce={VCE}, robust bias-corrected inference.")

    df = pd.read_parquet(PROC / "study1.parquet")
    note(f"\nAnalysis frame: {len(df):,} people (Wikidata, day-precision DOB, 1852-2020)")

    # ---- sample definition -------------------------------------------------
    # The outcome is the SHARE of people whose occupation falls in a Ptolemaic class,
    # so the denominator must be people who have a codeable occupation at all.
    # Including the 16% with no P106 statement would make the outcome partly a measure
    # of Wikidata completeness rather than of vocation. This restriction is a
    # specification decision taken at analysis time and logged as such (see the
    # deviations section of results.md); the unrestricted sample is reported as a
    # robustness check below.
    full = df
    df = df[df["has_occ"]].copy()
    note(f"Restricted to people with >=1 coded occupation: {len(df):,} "
         f"({100 * len(df) / len(full):.1f}%)")

    estimates: dict = {"seed": SEED, "vce": VCE, "window_days": WINDOW,
                       "n_frame": int(len(full)), "n_analysis": int(len(df))}

    # ---- pre-registered directions, straight from the frozen hypothesis module ----
    directions = {}
    for planet in CONFIRMATORY:
        d = (df[[f"{planet}_cusp", f"{planet}_pred_dir"]]
             .dropna().drop_duplicates()
             .set_index(f"{planet}_cusp")[f"{planet}_pred_dir"].to_dict())
        directions[planet] = {str(k): int(v) for k, v in d.items()}
        n_signed = sum(1 for v in directions[planet].values() if v != 0)
        note(f"  {planet:<8} {len(directions[planet]):>2} cusps, "
             f"{n_signed:>2} dignity-relevant (pooled), "
             f"{len(directions[planet]) - n_signed:>2} neutral (excluded from primary)")

    # =======================================================================
    # POSITIVE CONTROLS (plan §4.1) — run FIRST. If the pipeline cannot detect
    # a documented real effect, nothing below it means anything.
    # =======================================================================
    note("\n## Positive controls (plan §4.1)")
    controls: dict = {}

    # (a) Relative-age effect among athletes: birth-quarter skew.
    ath = df[df["is_athlete"]]
    q_counts = ath["birth_quarter"].value_counts().sort_index()
    q_all = df["birth_quarter"].value_counts().sort_index()
    share_ath = (q_counts / q_counts.sum())
    share_all = (q_all / q_all.sum())
    # Q1-vs-Q4 odds ratio of being an athlete, the standard relative-age statistic.
    k1, n1 = int(q_counts.get(1, 0)), int(q_all.get(1, 0))
    k4, n4 = int(q_counts.get(4, 0)), int(q_all.get(4, 0))
    p1, p4 = k1 / n1, k4 / n4
    or_q1q4 = (p1 / (1 - p1)) / (p4 / (1 - p4))
    se_log_or = np.sqrt(1 / k1 + 1 / (n1 - k1) + 1 / k4 + 1 / (n4 - k4))
    controls["relative_age_effect"] = {
        "or_q1_vs_q4": float(or_q1q4),
        "ci_low": float(np.exp(np.log(or_q1q4) - 1.96 * se_log_or)),
        "ci_high": float(np.exp(np.log(or_q1q4) + 1.96 * se_log_or)),
        "p": inf.two_sided_p(np.log(or_q1q4), se_log_or),
        "n_athletes": int(len(ath)),
        "athlete_share_by_quarter": {int(k): float(v) for k, v in share_ath.items()},
        "sample_share_by_quarter": {int(k): float(v) for k, v in share_all.items()},
    }
    note(f"  (a) Relative-age effect, athletes: OR(Q1 vs Q4) = {or_q1q4:.3f} "
         f"[{controls['relative_age_effect']['ci_low']:.3f}, "
         f"{controls['relative_age_effect']['ci_high']:.3f}], "
         f"n = {len(ath):,}")

    # (b) Annual birth seasonality: amplitude of the day-of-year birth cycle.
    # Computed BOTH with and without the heaped days-of-month (1, 10, 15). The
    # raw series peaks on 1 January, which is a registration artifact rather than
    # seasonality, so the heap-excluded version is the one that actually evidences
    # a real annual cycle.
    def seasonality(frame: pd.DataFrame) -> dict:
        doy = frame["day_of_year"].value_counts().sort_index()
        doy = doy[doy.index <= 365]
        counts = doy.to_numpy(dtype=float)
        theta = 2 * np.pi * (doy.index.to_numpy() - 1) / 365.0
        mean_c = counts.mean()
        a1 = 2 * np.mean(counts * np.cos(theta)) / mean_c
        b1 = 2 * np.mean(counts * np.sin(theta)) / mean_c
        return {"first_harmonic_amplitude_pct": float(100 * np.hypot(a1, b1)),
                "peak_day_of_year": int(doy.index[int(np.argmax(counts))]),
                "n": int(counts.sum())}

    seas_raw = seasonality(df)
    seas_clean = seasonality(df[~df["is_heaped_day"]])
    amp = seas_clean["first_harmonic_amplitude_pct"] / 100.0
    controls["birth_seasonality"] = {
        **seas_clean,
        "raw_including_heaped_days": seas_raw,
        "note": ("heaped days-of-month (1, 10, 15) excluded; the raw series peaks "
                 "on 1 January, a registration artifact"),
    }
    note(f"  (b) Birth seasonality (heaped days excluded): first-harmonic amplitude "
         f"{100 * amp:.2f}% of mean daily births, peak day-of-year "
         f"{seas_clean['peak_day_of_year']}")
    note(f"      (raw, including heaps: {seas_raw['first_harmonic_amplitude_pct']:.2f}%, "
         f"peak day-of-year {seas_raw['peak_day_of_year']})")

    controls_pass = (controls["relative_age_effect"]["ci_low"] > 1.0
                     and amp > 0.005)
    note(f"  -> positive controls {'PASS' if controls_pass else 'FAIL'}")
    controls["pass"] = bool(controls_pass)
    estimates["positive_controls"] = controls

    # =======================================================================
    # PRIMARY: pooled directional discontinuity per planet
    # =======================================================================
    note("\n## Primary confirmatory tests (H1-Me, H1-Ve, H1-Ma)")
    primary: dict = {}
    all_cusp_rows = []

    for planet in CONFIRMATORY:
        outcome = f"is_{planet}_occ"
        base = float(df[outcome].mean())
        sesoi = inf.or_to_risk_difference(SESOI_OR, base)
        t0 = time.perf_counter()
        cusps = per_cusp(df, planet, outcome, directions=directions[planet])
        cusps["stage"] = "primary"
        all_cusp_rows.append(cusps)

        signed = cusps[cusps["pred_dir"] != 0]
        pooled = inf.pool_signed(signed["est"], signed["se"], signed["pred_dir"])
        n_used = int(signed[["n_left", "n_right"]].sum().sum())

        rec = inf.full_test(
            f"H1-{planet[:2].capitalize()}", pooled["estimate"], pooled["se"],
            sesoi, n_used, direction=+1,
            extra={"planet": planet, "base_rate": base, "sesoi_or": SESOI_OR,
                   "n_cusps_pooled": pooled["n_cusps"],
                   "q_heterogeneity": pooled["q_het"], "p_heterogeneity": pooled["p_het"],
                   "i2": pooled["i2"], "tau2": pooled["tau2"],
                   "re_estimate": pooled["re_estimate"], "re_se": pooled["re_se"],
                   "re_ci_low": pooled["re_ci_low"], "re_ci_high": pooled["re_ci_high"],
                   "re_tost_equivalent": inf.tost(pooled["re_estimate"],
                                                  pooled["re_se"], sesoi)["equivalent"],
                   "mean_bandwidth_days": float(signed["h"].mean()),
                   "seconds": time.perf_counter() - t0})
        primary[planet] = rec

        note(f"\n  H1-{planet[:2].capitalize()} ({planet}, base rate {100 * base:.2f}%, "
             f"SESOI = {sesoi:+.5f} pp on the probability scale)")
        note(f"    pooled signed RD = {rec['estimate']:+.5f} "
             f"[{rec['ci_low']:+.5f}, {rec['ci_high']:+.5f}], "
             f"p = {rec['p_two_sided']:.3f}, {pooled['n_cusps']} cusps, N = {n_used:,}")
        note(f"    TOST vs +/-{sesoi:.5f}: p = {rec['tost_p_tost']:.4f} "
             f"-> {'EQUIVALENT' if rec['tost_equivalent'] else 'not equivalent'}")
        note(f"    BF01 = {rec['bf01']:.2f} ({rec['bf01_label']}); "
             f"directional BF01 = {rec['bf01_directional']:.2f}")
        note(f"    heterogeneity across cusps: Q = {pooled['q_het']:.1f}, "
             f"p = {pooled['p_het']:.3g}, I2 = {100 * pooled['i2']:.0f}%")
        note(f"    random-effects companion: {pooled['re_estimate']:+.5f} "
             f"[{pooled['re_ci_low']:+.5f}, {pooled['re_ci_high']:+.5f}] "
             f"-> {'EQUIVALENT' if rec['re_tost_equivalent'] else 'not equivalent'}")

    estimates["primary"] = primary

    # =======================================================================
    # EXPLORATORY: Sun (H1-Su dropped from the confirmatory family at GATE 1)
    # =======================================================================
    note("\n## Exploratory — Sun sign and leadership occupations")
    note("  (H1-Su was dropped from the confirmatory family at GATE 1: Ptolemy IV.4")
    note("   assigns occupation to Mars, Venus and Mercury only. See hypotheses.py.)")
    sun_rows = []
    for outcome in ["is_mercury_occ", "is_venus_occ", "is_mars_occ"]:
        c = per_cusp(df, "sun", outcome, h_cap=SOLAR_H_CAP)
        c["outcome"] = outcome
        sun_rows.append(c)
    sun = pd.concat(sun_rows, ignore_index=True)
    sun["stage"] = "exploratory_sun"
    all_cusp_rows.append(sun)
    note(f"  {len(sun)} solar cusp x outcome fits, bandwidth capped at "
         f"h <= {SOLAR_H_CAP:g} days (plan §0); mean |t| = "
         f"{np.nanmean(np.abs(sun['est'] / sun['se'])):.2f}")
    estimates["exploratory_sun_mean_abs_t"] = float(
        np.nanmean(np.abs(sun["est"] / sun["se"])))

    # =======================================================================
    # FALSIFICATION BATTERY (plan §4)
    # =======================================================================
    note("\n## Falsification and robustness (plan §4)")
    robustness: dict = {}

    # --- §4.2 placebo cutoffs ---
    note("\n  Placebo cutoffs (shifted +/-10, +/-20 days; should centre on zero)")
    placebo_rows = []
    for planet in CONFIRMATORY:
        outcome = f"is_{planet}_occ"
        for off in PLACEBO_OFFSETS:
            c = per_cusp(df, planet, outcome, shift=float(off),
                         directions=directions[planet])
            c["offset"] = off
            placebo_rows.append(c)
            s = c[c["pred_dir"] != 0]
            p = inf.pool_signed(s["est"], s["se"], s["pred_dir"])
            note(f"    {planet:<8} offset {off:+3d}d: pooled = {p['estimate']:+.5f} "
                 f"[{p['ci_low']:+.5f}, {p['ci_high']:+.5f}]")
            robustness.setdefault("placebo", {})[f"{planet}_{off:+d}"] = p
    placebo = pd.concat(placebo_rows, ignore_index=True)
    placebo["stage"] = "placebo"
    all_cusp_rows.append(placebo)

    # Rejection rate at nominal 5% across all placebo fits.
    pl = placebo.dropna(subset=["est", "se"])
    rej = float(np.mean(np.abs(pl["est"] / pl["se"]) > 1.96))
    robustness["placebo_rejection_rate"] = rej
    robustness["placebo_n_fits"] = int(len(pl))
    note(f"    -> placebo rejection rate {100 * rej:.1f}% of {len(pl)} fits "
         f"(nominal 5%)")

    # --- §4.3 density / manipulation test ---
    note("\n  Density tests (rddensity; a jump indicates a data artifact)")
    density_rows = []
    try:
        from rddensity import rddensity
        for planet in CONFIRMATORY:
            run_col, cusp_col = f"{planet}_running", f"{planet}_cusp"
            for cusp, g in df.groupby(cusp_col, observed=True):
                if "->" not in str(cusp):
                    continue
                x = g[run_col].to_numpy(dtype=float)
                x = x[np.abs(x) <= WINDOW]
                if len(x) < 500:
                    continue
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        rdd = rddensity(X=x)
                    density_rows.append({"planet": planet, "cusp": str(cusp),
                                         "t": float(np.ravel(rdd.test["t_jk"])[0]),
                                         "p": float(np.ravel(rdd.test["p_jk"])[0]),
                                         "n": int(len(x))})
                except Exception as exc:  # noqa: BLE001
                    density_rows.append({"planet": planet, "cusp": str(cusp),
                                         "t": np.nan, "p": np.nan, "n": int(len(x)),
                                         "error": str(exc)[:120]})
    except ImportError:
        note("    rddensity not installed — density test SKIPPED (reported as a gap)")
    dens = pd.DataFrame(density_rows)
    if len(dens) and dens["p"].notna().any():
        frac = float((dens["p"] < 0.05).mean())
        robustness["density_frac_rejected"] = frac
        robustness["density_n_cusps"] = int(dens["p"].notna().sum())
        note(f"    {100 * frac:.1f}% of {dens['p'].notna().sum()} cusps reject "
             f"density continuity at .05")
        dens.to_csv(RESULTS / "study1_density_tests.csv", index=False)

    # --- §4.4 donut, §4.5 heaping, §3 bandwidth sensitivity, full-sample ---
    note("\n  Specification robustness (pooled estimates)")
    variants = {
        "donut_1day": dict(donut=1.0),
        "drop_heaped_days": dict(drop_heaped=True),
        **{f"fixed_h{h}": dict(h=float(h)) for h in BW_GRID},
    }
    for planet in CONFIRMATORY:
        outcome = f"is_{planet}_occ"
        base = float(df[outcome].mean())
        sesoi = inf.or_to_risk_difference(SESOI_OR, base)
        for vname, kw in variants.items():
            c = per_cusp(df, planet, outcome, directions=directions[planet], **kw)
            s = c[c["pred_dir"] != 0]
            p = inf.pool_signed(s["est"], s["se"], s["pred_dir"])
            p["tost_equivalent"] = inf.tost(p["estimate"], p["se"], sesoi)["equivalent"]
            robustness.setdefault("variants", {}).setdefault(planet, {})[vname] = p
        # full (unrestricted) sample, including people with no coded occupation
        c = per_cusp(full, planet, outcome, directions=directions[planet])
        s = c[c["pred_dir"] != 0]
        p = inf.pool_signed(s["est"], s["se"], s["pred_dir"])
        robustness["variants"][planet]["full_sample_incl_no_occupation"] = p

        v = robustness["variants"][planet]
        note(f"    {planet:<8} primary {primary[planet]['estimate']:+.5f} | "
             + " ".join(f"{k.replace('fixed_h', 'h')}={v[k]['estimate']:+.5f}"
                        for k in ["donut_1day", "drop_heaped_days",
                                  "fixed_h3", "fixed_h7", "fixed_h21"]))

    # --- covariate balance (plan §3) ---
    note("\n  Covariate balance at the cutoff (a jump here invalidates the design)")

    # Citizenship region, extracted by 02c_extract_citizenship.py. Region is
    # categorical, so balance is tested on an indicator for each of the largest
    # regions rather than on the raw label.
    balance_covs = ["is_male", "birth_year", "log_sitelinks"]
    cit_path = PROJ / "data" / "raw" / "wikidata" / "citizenship.parquet"
    if cit_path.exists():
        cit = pd.read_parquet(cit_path)[["qid", "continent_label"]]
        df = df.merge(cit, on="qid", how="left")
        cov_frac = float(df["continent_label"].notna().mean())
        top_regions = (df["continent_label"].value_counts().head(3).index.tolist())
        for reg in top_regions:
            col = f"region_{str(reg).lower().replace(' ', '_')}"
            df[col] = df["continent_label"].eq(reg).astype(float)
            balance_covs.append(col)
        note(f"    citizenship region available for {100 * cov_frac:.1f}% of the "
             f"sample; testing balance on indicators for {', '.join(top_regions)}")
        estimates["citizenship_coverage"] = cov_frac
        estimates["citizenship_top_regions"] = [str(r) for r in top_regions]
    else:
        note("    citizenship.parquet not found — region balance check SKIPPED "
             "(run 02c_extract_citizenship.py)")

    balance_rows = []
    for planet in CONFIRMATORY:
        for cov in balance_covs:
            d2 = df.dropna(subset=[cov]) if df[cov].isna().any() else df
            c = per_cusp(d2.assign(**{f"_cov_{cov}": d2[cov].astype(float)}),
                         planet, f"_cov_{cov}", directions=directions[planet])
            s = c[c["pred_dir"] != 0]
            # Balance is a two-sided question, so pool UNSIGNED (direction +1 for all).
            p = inf.pool_signed(s["est"], s["se"], np.ones(len(s)))
            balance_rows.append({"planet": planet, "covariate": cov,
                                 "pooled_jump": p["estimate"], "se": p["se"],
                                 "p": inf.two_sided_p(p["estimate"], p["se"]),
                                 "sd_of_covariate": float(d2[cov].astype(float).std())})
            note(f"    {planet:<8} {cov:<14} jump = {p['estimate']:+.5f} "
                 f"(SD {balance_rows[-1]['sd_of_covariate']:.3f}), "
                 f"p = {balance_rows[-1]['p']:.3f}")
    pd.DataFrame(balance_rows).to_csv(RESULTS / "study1_balance.csv", index=False)
    robustness["balance"] = balance_rows
    estimates["robustness"] = robustness

    # ---- write ----
    pd.concat(all_cusp_rows, ignore_index=True).to_csv(
        RESULTS / "study1_cusp_estimates.csv", index=False)
    (RESULTS / "estimates_study1.json").write_text(
        json.dumps(estimates, indent=2, default=float), encoding="utf-8")
    (RESULTS / "study1_log.md").write_text("\n".join(log), encoding="utf-8")

    note(f"\nTotal runtime: {(time.perf_counter() - t_start) / 60:.1f} min")
    note(f"-> {RESULTS / 'estimates_study1.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
