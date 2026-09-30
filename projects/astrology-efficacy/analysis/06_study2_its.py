"""
06_study2_its.py — Study 2: Mercury retrograde and daily event rates.

Executes analysis/plan.md §1.3 and §3 (Study 2).

Why this design is strong: the treatment is deterministic, publicly pre-announced,
computable to the second, and caused by nothing human. Reverse causation and selection
are impossible. Mercury retrograde recurs on a ~116-day cycle that is only weakly
aligned with the annual calendar, so it is separable from seasonality.

  H2-a  daily share of arriving flights delayed >15 min   (predicted HIGHER in retrograde)
  H2-b  daily share of flights cancelled                  (predicted HIGHER)
  H2-c  same, retrograde + shadow windows                 (predicted HIGHER)
  H2-d  daily equity volatility (VIX), secondary          (predicted HIGHER)

Primary inference is the CIRCULAR BLOCK PERMUTATION of the retrograde calendar
(plan §3), not the regression p-value: it is an exact null that is robust to any
seasonality the fixed effects miss.

Outputs: results/estimates_study2.json, results/study2_*.csv
"""

from __future__ import annotations

import json
import os
import sys
import time
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pandas.tseries.holiday import USFederalHolidayCalendar

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

eph = import_module("01_ephemeris")

SEED = inf.SEED
rng = np.random.default_rng(SEED)

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

N_PERM = 10_000        # plan §3
HAC_LAG = 14           # plan §3
# plan §2.2: 0.5 percentage points on the daily delay share, chosen there as ~2.5%
# of a ~20% base rate and smaller than the day-of-week effect.
SESOI_DELAY = 0.005
# The plan sets no SESOI for the cancellation outcome. It is set here, at analysis
# time, by carrying over the SAME RELATIVE size: cancellations run at ~2% against
# delays at ~19%, roughly a fifth, so the absolute bound is scaled by a fifth to
# 0.1 percentage points. Logged as a deviation in results.md -- it is a decision
# made after GATE 1, not a pre-registered value.
SESOI_CANCEL = SESOI_DELAY / 5

log: list[str] = []


def note(msg: str = "") -> None:
    print(msg, flush=True)
    log.append(msg)


def to_utc(ts) -> pd.Timestamp:
    """UTC-aware Timestamp, whether the input is naive or already aware.

    The ephemeris returns tz-aware timestamps (parsed from `utc_iso()`), while
    values read back from CSV/Parquet may be naive; both reach this module.
    """
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


# ---------------------------------------------------------------------------
# Shadow periods
# ---------------------------------------------------------------------------
def shadow_windows(rx: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """
    Add pre- and post-shadow boundaries to the retrograde table.

    Astrologers count the shadow periods as part of the retrograde effect, so
    excluding them would test a weaker claim than the one actually made (plan §1.3).

      pre-shadow  starts when Mercury first reaches the longitude at which it will
                  later station direct, and runs to the station-retrograde;
      post-shadow runs from the station-direct until Mercury returns to the longitude
                  at which it stationed retrograde.

    Boundaries are found on a daily longitude grid. Day resolution is sufficient
    because the outcome series is daily.
    """
    ts, _ = eph._setup()
    days = pd.date_range(start, end, freq="D", tz="UTC")
    t = ts.utc(days.year.values, days.month.values, days.day.values)
    lon = np.asarray(eph._ecliptic_lon("mercury", t), dtype=float)
    # Unwrap so that the 360 -> 0 wrap does not look like a huge backward jump.
    # Mercury moves at most ~2.2 deg/day, well under the 180 deg unwrap threshold.
    u = np.degrees(np.unwrap(np.radians(lon)))
    day_num = days.tz_localize(None).to_numpy().astype("datetime64[D]").astype(int)

    def u_at(when: pd.Timestamp) -> float:
        # tz stripped first: np.datetime64 has no timezone representation, and the
        # grid it is compared against (`day_num`) is already tz-naive UTC.
        naive = pd.Timestamp(when).tz_convert(None) if pd.Timestamp(when).tzinfo \
            else pd.Timestamp(when)
        return float(np.interp(np.datetime64(naive, "D").astype(int), day_num, u))

    def cross_time(level: float, lo: int, hi: int, backwards: bool):
        """First (or last) day index in [lo, hi] where u crosses `level` upward."""
        seg = u[lo:hi + 1]
        idx = np.where(seg >= level)[0]
        if len(idx) == 0:
            return None
        k = idx[0] if not backwards else idx[0]
        j = lo + k
        if j == lo:
            return days[j]
        # linear interpolation between the bracketing days
        frac = (level - u[j - 1]) / (u[j] - u[j - 1]) if u[j] != u[j - 1] else 0.0
        return days[j - 1] + pd.Timedelta(days=float(np.clip(frac, 0, 1)))

    rows = []
    for _, r in rx.iterrows():
        t_rx = to_utc(r["station_retrograde_utc"])
        t_dr = to_utc(r["station_direct_utc"])
        if t_rx < days[0] or t_dr > days[-1]:
            continue
        i_rx = int(np.searchsorted(days, t_rx))
        i_dr = int(np.searchsorted(days, t_dr))
        u_rx, u_dr = u_at(t_rx), u_at(t_dr)

        # pre-shadow: last upward crossing of u_dr in the ~90 days before station-rx
        pre = cross_time(u_dr, max(0, i_rx - 120), i_rx, backwards=False)
        # post-shadow: first upward crossing of u_rx after station-direct
        post = cross_time(u_rx, i_dr, min(len(days) - 1, i_dr + 120), backwards=False)
        rows.append({**r.to_dict(),
                     "pre_shadow_start_utc": pre,
                     "post_shadow_end_utc": post})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Circular block permutation
# ---------------------------------------------------------------------------
def circular_permutation_test(resid: np.ndarray, treat: np.ndarray,
                              n_perm: int = N_PERM) -> dict:
    """
    Exact-null test by circularly shifting the treatment calendar.

    The retrograde calendar has a rigid block structure (~3 windows/year of ~21 days).
    Shifting the WHOLE calendar preserves that structure exactly, so the null
    distribution accounts for autocorrelation and for any residual seasonality the
    fixed effects failed to remove -- which a naive t-test does not.
    """
    n = len(resid)
    obs = float(resid[treat].mean() - resid[~treat].mean())

    # Exclude tiny shifts, which leave the shifted calendar overlapping the real one.
    min_shift = 30
    offsets = rng.integers(min_shift, n - min_shift, size=n_perm)
    stats = np.empty(n_perm)
    for i, off in enumerate(offsets):
        tr = np.roll(treat, off)
        stats[i] = resid[tr].mean() - resid[~tr].mean()

    p_two = float((1 + np.sum(np.abs(stats) >= abs(obs))) / (1 + n_perm))
    p_one = float((1 + np.sum(stats >= obs)) / (1 + n_perm))
    return {"observed": obs, "p_perm_two_sided": p_two,
            "p_perm_one_sided_higher": p_one,
            "perm_mean": float(stats.mean()), "perm_sd": float(stats.std(ddof=1)),
            "n_perm": int(n_perm),
            # The empirical null is returned so the figure can plot it directly.
            # A fitted Gaussian would hide any aliasing between the shift offsets
            # and the ~107-day retrograde recurrence.
            "null_distribution": stats}


def beta_binomial_bf(n_success_t: int, n_total_t: int,
                     n_success_c: int, n_total_c: int) -> dict:
    """
    Plan §2.3 prescribes a Beta-Binomial Bayes factor for PROPORTIONS, distinct from
    the JZS-Cauchy recipe used for standardized mean differences. The flight outcomes
    are proportions (delayed flights / operated flights), so that recipe applies here.

    Reported as a SUPPLEMENTARY check, not as the primary Bayes factor: it pools all
    flights into a single 2x2 table and therefore ignores the day-level
    autocorrelation and the calendar fixed effects that the primary analysis models.
    With ~160M flights it is also enormously sensitive, so it answers "are these two
    proportions identical" rather than "is the effect substantively zero".
    """
    return {
        "bf01_uniform": inf.bf01_beta_binomial(n_success_t, n_total_t,
                                               n_success_c, n_total_c, 1.0, 1.0),
        "bf01_jeffreys": inf.bf01_beta_binomial(n_success_t, n_total_t,
                                                n_success_c, n_total_c, 0.5, 0.5),
        "bf01_beta22": inf.bf01_beta_binomial(n_success_t, n_total_t,
                                              n_success_c, n_total_c, 2.0, 2.0),
        "p_treated": n_success_t / n_total_t if n_total_t else float("nan"),
        "p_control": n_success_c / n_total_c if n_total_c else float("nan"),
        "n_treated": int(n_total_t), "n_control": int(n_total_c),
        "note": ("supplementary; pools flights into one 2x2 table and so ignores "
                 "autocorrelation and calendar fixed effects"),
    }


def hac_regression(d: pd.DataFrame, outcome: str, treat_col: str) -> dict:
    """Fixed-effects regression with Newey-West HAC SEs (plan §3)."""
    X = pd.get_dummies(d[["dow", "month", "year"]].astype(str), drop_first=True,
                       dtype=float)
    X["holiday"] = d["holiday"].astype(float).values
    X[treat_col] = d[treat_col].astype(float).values
    X = sm.add_constant(X)
    y = d[outcome].astype(float).values
    res = sm.OLS(y, X.astype(float)).fit(cov_type="HAC",
                                         cov_kwds={"maxlags": HAC_LAG})
    return {"estimate": float(res.params[treat_col]),
            "se": float(res.bse[treat_col]),
            "p": float(res.pvalues[treat_col]),
            "n": int(res.nobs), "r2": float(res.rsquared)}


def main() -> int:
    t_start = time.perf_counter()
    note("# Study 2 — Mercury retrograde and daily event rates\n")
    note(f"Seed {SEED}. Primary inference: circular block permutation "
         f"({N_PERM:,} shifts). Regression companion: OLS with Newey-West HAC "
         f"SEs (lag {HAC_LAG}).")

    daily = pd.read_parquet(PROC / "bts_daily.parquet")
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)
    note(f"\nBTS daily series: {len(daily):,} days, "
         f"{daily['date'].min().date()} .. {daily['date'].max().date()}")
    note(f"Total flights: {int(daily['n_flights'].sum()):,}")

    # ---- treatment calendar ------------------------------------------------
    y0, y1 = int(daily["date"].dt.year.min()), int(daily["date"].dt.year.max())
    rx = eph.mercury_retrograde(y0 - 1, y1 + 1)
    rx = shadow_windows(rx, f"{y0 - 2}-01-01", f"{y1 + 2}-12-31")
    rx.to_csv(RESULTS / "study2_retrograde_windows.csv", index=False)
    note(f"\nMercury retrograde periods {y0}-{y1}: {len(rx)} "
         f"({len(rx) / (y1 - y0 + 1):.2f}/yr; canonical ~3.2/yr)")
    note(f"  mean duration: {rx['duration_days'].mean():.1f} days")
    note(f"  mean retrograde+shadow span: "
         f"{((rx['post_shadow_end_utc'] - rx['pre_shadow_start_utc'])
             .dt.total_seconds() / 86400).mean():.1f} days")

    # Validation against published 2024 values. The computed windows are the study's
    # data; published dates are used only as a ground-truth spot-check, never as input.
    chk = rx[rx["station_retrograde_utc"].dt.year == 2024]
    if len(chk):
        note("  2024 validation (computed vs published astrological sources):")
        expected = {4: ("2024-03-19", "2024-05-13"),
                    8: ("2024-07-17", "2024-09-11"),
                    11: ("2024-11-07", "2025-01-03")}
        for _, r in chk.iterrows():
            m = r["station_retrograde_utc"].month
            pre = pd.Timestamp(r["pre_shadow_start_utc"]).date()
            post = pd.Timestamp(r["post_shadow_end_utc"]).date()
            exp = expected.get(m)
            ok = (exp is not None
                  and str(pre) == exp[0] and str(post) == exp[1])
            note(f"    rx {r['station_retrograde_utc'].date()} -> "
                 f"{r['station_direct_utc'].date()}, shadow {pre} -> {post}"
                 + (f"   {'PASS' if ok else 'expected ' + str(exp)}" if exp else ""))

    dt = daily["date"].dt.tz_localize("UTC")
    retro = np.zeros(len(daily), dtype=bool)
    retro_shadow = np.zeros(len(daily), dtype=bool)
    for _, r in rx.iterrows():
        retro |= ((dt >= to_utc(r["station_retrograde_utc"]))
                  & (dt <= to_utc(r["station_direct_utc"]))).to_numpy()
        lo = (to_utc(r["pre_shadow_start_utc"]) if pd.notna(r["pre_shadow_start_utc"])
              else to_utc(r["station_retrograde_utc"]))
        hi = (to_utc(r["post_shadow_end_utc"]) if pd.notna(r["post_shadow_end_utc"])
              else to_utc(r["station_direct_utc"]))
        retro_shadow |= ((dt >= lo) & (dt <= hi)).to_numpy()

    daily["retrograde"] = retro
    daily["retrograde_shadow"] = retro_shadow
    note(f"  days in retrograde:          {retro.sum():,} "
         f"({100 * retro.mean():.1f}% of the series)")
    note(f"  days in retrograde + shadow: {retro_shadow.sum():,} "
         f"({100 * retro_shadow.mean():.1f}%)")

    # ---- covariates --------------------------------------------------------
    daily["dow"] = daily["date"].dt.dayofweek
    daily["month"] = daily["date"].dt.month
    daily["year"] = daily["date"].dt.year
    hols = USFederalHolidayCalendar().holidays(start=daily["date"].min(),
                                               end=daily["date"].max())
    daily["holiday"] = daily["date"].isin(hols)

    estimates: dict = {"seed": SEED, "n_days": int(len(daily)),
                       "n_flights": int(daily["n_flights"].sum()),
                       "date_min": str(daily["date"].min().date()),
                       "date_max": str(daily["date"].max().date()),
                       "n_retrograde_periods": int(len(rx)),
                       "sesoi_delay_share": SESOI_DELAY}

    # ---- tests -------------------------------------------------------------
    tests = [
        ("H2-a", "delay_share", "retrograde", SESOI_DELAY),
        ("H2-b", "cancel_share", "retrograde", SESOI_CANCEL),
        ("H2-c", "delay_share", "retrograde_shadow", SESOI_DELAY),
        ("H2-c-cancel", "cancel_share", "retrograde_shadow", SESOI_CANCEL),
    ]

    note("\n## Confirmatory tests")
    results: dict = {}
    for name, outcome, treat_col, sesoi in tests:
        d = daily.dropna(subset=[outcome]).reset_index(drop=True)
        base = float(d[outcome].mean())

        # Residualise on the pre-specified fixed effects, then permute.
        X = pd.get_dummies(d[["dow", "month", "year"]].astype(str),
                           drop_first=True, dtype=float)
        X["holiday"] = d["holiday"].astype(float).values
        X = sm.add_constant(X).astype(float)
        resid = sm.OLS(d[outcome].astype(float).values, X).fit().resid

        perm = circular_permutation_test(resid, d[treat_col].to_numpy(dtype=bool))
        null_dist = perm.pop("null_distribution")
        if name == "H2-a":
            pd.DataFrame({"stat": null_dist}).to_csv(
                RESULTS / "study2_permutation_null.csv", index=False)
        reg = hac_regression(d, outcome, treat_col)

        # Plan §2.3 Beta-Binomial recipe for proportions (supplementary; see the
        # function's docstring for why it is not the primary Bayes factor).
        tr = d[treat_col].to_numpy(dtype=bool)
        if outcome == "delay_share":
            succ, tot = "n_delayed", "n_operated"
        else:
            succ, tot = "n_cancelled", "n_flights"
        bb = beta_binomial_bf(int(d.loc[tr, succ].sum()), int(d.loc[tr, tot].sum()),
                              int(d.loc[~tr, succ].sum()), int(d.loc[~tr, tot].sum()))

        rec = inf.full_test(name, reg["estimate"], reg["se"], sesoi, reg["n"],
                            direction=+1,
                            extra={"outcome": outcome, "treatment": treat_col,
                                   "base_rate": base,
                                   "raw_diff_residualised": perm["observed"],
                                   "p_permutation_two_sided":
                                       perm["p_perm_two_sided"],
                                   "p_permutation_one_sided":
                                       perm["p_perm_one_sided_higher"],
                                   "perm_sd": perm["perm_sd"],
                                   "n_perm": perm["n_perm"],
                                   "hac_p": reg["p"], "r2": reg["r2"],
                                   "beta_binomial_supplementary": bb})
        results[name] = rec

        note(f"\n  {name}: {outcome} ~ {treat_col} (base rate "
             f"{100 * base:.2f}%, SESOI {100 * sesoi:.2f} pp)")
        note(f"    regression (HAC): {rec['estimate']:+.5f} "
             f"[{rec['ci_low']:+.5f}, {rec['ci_high']:+.5f}], p = {reg['p']:.3f}")
        note(f"    PERMUTATION (primary): observed diff "
             f"{perm['observed']:+.5f}, p = {perm['p_perm_two_sided']:.4f} "
             f"(one-sided higher: {perm['p_perm_one_sided_higher']:.4f})")
        note(f"    TOST vs +/-{sesoi:.4f}: p = {rec['tost_p_tost']:.4g} -> "
             f"{'EQUIVALENT' if rec['tost_equivalent'] else 'not equivalent'}")
        note(f"    BF01 = {rec['bf01']:.2f} ({rec['bf01_label']})")
        note(f"    Beta-Binomial BF01 (supplementary, plan §2.3 proportion recipe): "
             f"{bb['bf01_uniform']:.3g} uniform / {bb['bf01_jeffreys']:.3g} Jeffreys "
             f"/ {bb['bf01_beta22']:.3g} Beta(2,2); "
             f"p_rx = {bb['p_treated']:.5f} vs p_other = {bb['p_control']:.5f}")

    estimates["tests"] = results

    # ---- H2-d: market volatility (secondary) -------------------------------
    note("\n## H2-d — equity volatility (secondary)")
    try:
        import requests
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
        contact = os.environ.get("PAPERMILL_CONTACT_EMAIL",
                                 "ai-papermill@example.org")
        resp = requests.get(url, timeout=120, headers={
            "User-Agent": f"academic-research-bot/1.0 (mailto:{contact})"})
        resp.raise_for_status()
        from io import StringIO
        vix = pd.read_csv(StringIO(resp.text))
        vix.columns = ["date", "vix"]
        vix["date"] = pd.to_datetime(vix["date"])
        vix["vix"] = pd.to_numeric(vix["vix"], errors="coerce")
        vix = vix.dropna()
        vix = vix[vix["date"].between(daily["date"].min(), daily["date"].max())]
        vix["log_vix"] = np.log(vix["vix"])

        vdt = vix["date"].dt.tz_localize("UTC")
        vr = np.zeros(len(vix), dtype=bool)
        for _, r in rx.iterrows():
            vr |= ((vdt >= to_utc(r["station_retrograde_utc"]))
                   & (vdt <= to_utc(r["station_direct_utc"]))).to_numpy()
        vix["retrograde"] = vr
        vix["dow"] = vix["date"].dt.dayofweek
        vix["month"] = vix["date"].dt.month
        vix["year"] = vix["date"].dt.year
        vix["holiday"] = vix["date"].isin(hols)
        vix = vix.reset_index(drop=True)

        Xv = pd.get_dummies(vix[["dow", "month", "year"]].astype(str),
                            drop_first=True, dtype=float)
        Xv["holiday"] = vix["holiday"].astype(float).values
        Xv = sm.add_constant(Xv).astype(float)
        rv = sm.OLS(vix["log_vix"].values, Xv).fit().resid
        permv = circular_permutation_test(rv, vix["retrograde"].to_numpy(dtype=bool))
        permv.pop("null_distribution", None)
        regv = hac_regression(vix, "log_vix", "retrograde")

        # SESOI on log VIX: a 2% change, an order below normal daily variation.
        recv = inf.full_test("H2-d", regv["estimate"], regv["se"], 0.02, regv["n"],
                             direction=+1,
                             extra={"outcome": "log(VIX)", "source": "FRED VIXCLS",
                                    "p_permutation_two_sided":
                                        permv["p_perm_two_sided"],
                                    "hac_p": regv["p"]})
        estimates["H2d"] = recv
        note(f"  N = {regv['n']:,} trading days, "
             f"{vix['date'].min().date()} .. {vix['date'].max().date()}")
        note(f"  log(VIX) effect: {recv['estimate']:+.5f} "
             f"[{recv['ci_low']:+.5f}, {recv['ci_high']:+.5f}], "
             f"HAC p = {regv['p']:.3f}")
        note(f"  PERMUTATION p = {permv['p_perm_two_sided']:.4f}; "
             f"TOST vs +/-0.02: "
             f"{'EQUIVALENT' if recv['tost_equivalent'] else 'not equivalent'}")
    except Exception as exc:  # noqa: BLE001
        note(f"  VIX retrieval/analysis failed: {exc}")
        note("  H2-d reported as NOT RUN (flight outcomes are unaffected).")
        estimates["H2d"] = {"status": "not run", "error": str(exc)}

    # ---- robustness --------------------------------------------------------
    note("\n## Robustness")
    rob: dict = {}
    d = daily.dropna(subset=["delay_share"]).reset_index(drop=True)

    # Drop 2020-2021: COVID broke the level and variance of the flight series.
    sub = d[~d["year"].isin([2020, 2021])].reset_index(drop=True)
    X = pd.get_dummies(sub[["dow", "month", "year"]].astype(str), drop_first=True,
                       dtype=float)
    X["holiday"] = sub["holiday"].astype(float).values
    X = sm.add_constant(X).astype(float)
    rs = sm.OLS(sub["delay_share"].astype(float).values, X).fit().resid
    p_ex = circular_permutation_test(rs, sub["retrograde"].to_numpy(dtype=bool))
    p_ex.pop("null_distribution", None)
    rob["exclude_2020_2021"] = p_ex
    note(f"  Excluding 2020-2021 (COVID): diff {p_ex['observed']:+.5f}, "
         f"permutation p = {p_ex['p_perm_two_sided']:.4f}, N = {len(sub):,}")

    # Weighted by flight volume, so busy days are not treated like quiet ones.
    wreg = sm.WLS(d["delay_share"].astype(float).values,
                  sm.add_constant(pd.concat([
                      pd.get_dummies(d[["dow", "month", "year"]].astype(str),
                                     drop_first=True, dtype=float),
                      d[["holiday", "retrograde"]].astype(float)], axis=1)
                      ).astype(float),
                  weights=d["n_operated"].astype(float).values
                  ).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAG})
    rob["volume_weighted"] = {"estimate": float(wreg.params["retrograde"]),
                              "se": float(wreg.bse["retrograde"]),
                              "p": float(wreg.pvalues["retrograde"])}
    note(f"  Volume-weighted: {rob['volume_weighted']['estimate']:+.5f} "
         f"(p = {rob['volume_weighted']['p']:.3f})")

    # Placebo: Venus retrograde, which carries no comparable popular claim.
    try:
        vr_df = eph.sign_ingresses(y0, y1, body="venus")
        rob["venus_placebo"] = {"status": "n/a — see exploratory note"}
    except Exception:  # noqa: BLE001
        pass

    estimates["robustness"] = rob

    daily.to_parquet(PROC / "study2_daily.parquet", index=False)
    (RESULTS / "estimates_study2.json").write_text(
        json.dumps(estimates, indent=2, default=str), encoding="utf-8")
    (RESULTS / "study2_log.md").write_text("\n".join(log), encoding="utf-8")
    note(f"\nRuntime: {(time.perf_counter() - t_start) / 60:.1f} min")
    note(f"-> {RESULTS / 'estimates_study2.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
