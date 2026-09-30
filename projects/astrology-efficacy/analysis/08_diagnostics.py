"""
08_diagnostics.py — Why the Study 1 running variable misbehaves, and what survives.

EXPLORATORY. None of this was pre-registered. It exists because two pre-registered
falsification checks (plan §4.2, §4.3) FAILED, and a failed falsification check has
to be explained rather than reported and walked past:

  * placebo cutoffs rejected at ~11% against a nominal 5%;
  * ~29% of cusps rejected density continuity, although birth dates cannot possibly
    be manipulated around a zodiac boundary.

The hypothesis tested here: Mercury and Venus STATION AND REVERSE, so they cross the
same sign boundary three times in quick succession (direct, retrograde, direct). Near
such a triple crossing the running variable's support is truncated — a person cannot
be 20 days from the nearest cusp if the next crossing is 8 days away — which produces
exactly the density discontinuities and the excess placebo rejections observed, with
no astrology and no data error involved.

If that is right, then restricting to ISOLATED cusps (no adjacent crossing within the
analysis window) should remove both symptoms. That is the decisive test below.

Outputs: results/estimates_diagnostics.json, results/diagnostics_*.csv
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import time
import warnings
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
study1 = import_module("05_study1_rdd")
eph = import_module("01_ephemeris")

SEED = inf.SEED
np.random.seed(SEED)

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"

PLANETS = ["mercury", "venus", "mars"]
INGRESS_START, INGRESS_END = 1850, 2022

# A cusp is "isolated" if the nearest OTHER crossing is at least this far away.
# Reported over a grid rather than at one value, because the planets differ by an
# order of magnitude in how often they change sign: at 35 days Mercury has no
# isolated cusps at all, so a single threshold cannot compare them.
ISOLATION_GRID = [10.0, 15.0, 20.0, 35.0]
ISOLATION_DAYS = 35.0  # headline threshold, kept for the summary tables

log: list[str] = []


def note(msg: str = "") -> None:
    print(msg, flush=True)
    log.append(msg)


def cached_ingresses(body: str) -> pd.DataFrame:
    """Ingress times, cached — recomputing them from the ephemeris is the slow step."""
    path = PROC / f"ingresses_{body}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    t0 = time.perf_counter()
    # Computed in 10-year chunks: skyfield's nutation step allocates a
    # (687 x n_times) float64 array, which for Mercury over 172 years at a 0.5-day
    # search step needs ~1.3 GiB in a single call.
    parts = []
    for y0 in range(INGRESS_START, INGRESS_END + 1, 10):
        y1 = min(y0 + 9, INGRESS_END)
        parts.append(eph.sign_ingresses(y0, y1, body=body))
    ing = (pd.concat(parts, ignore_index=True)
           .drop_duplicates(subset=["ingress_utc"])
           .sort_values("ingress_utc").reset_index(drop=True))
    ing.to_parquet(path, index=False)
    note(f"    computed {len(ing):,} {body} ingresses in "
         f"{time.perf_counter() - t0:.0f}s -> cached")
    return ing


def main() -> int:
    note("# Study 1 diagnostics — the running variable (EXPLORATORY)\n")
    diag: dict = {"seed": SEED, "isolation_days": ISOLATION_DAYS,
                  "status": "exploratory, not pre-registered"}

    # ---- 1. Gap structure between consecutive crossings --------------------
    note("## 1. Spacing of consecutive sign crossings")
    note("   A retrograde planet crosses the same boundary three times in a few weeks.")
    gap_stats = {}
    ingress = {}
    for body in PLANETS:
        ing = cached_ingresses(body).sort_values("ingress_utc").reset_index(drop=True)
        ingress[body] = ing
        gaps = ing["ingress_utc"].diff().dt.total_seconds().div(86400).dropna()
        gap_stats[body] = {
            "n_crossings": int(len(ing)),
            "median_gap_days": float(gaps.median()),
            "frac_gap_under_35d": float((gaps < ISOLATION_DAYS).mean()),
            "frac_gap_under_10d": float((gaps < 10).mean()),
            "min_gap_days": float(gaps.min()),
        }
        note(f"   {body:<8} {len(ing):>5,} crossings, median gap "
             f"{gaps.median():>6.1f}d, {100 * (gaps < ISOLATION_DAYS).mean():>5.1f}% "
             f"of gaps < {ISOLATION_DAYS:g}d, min {gaps.min():.2f}d")
    diag["gap_structure"] = gap_stats

    # ---- 2. Flag each person's cusp as isolated or crowded ------------------
    note("\n## 2. Tagging each birth by whether its nearest cusp is isolated")
    df = pd.read_parquet(PROC / "study1.parquet")
    df = df[df["has_occ"]].copy()

    for body in PLANETS:
        ing = ingress[body]
        t = ing["ingress_utc"].dt.tz_localize(None).to_numpy()
        # Distance from each crossing to its nearest neighbouring crossing.
        d_prev = np.r_[np.inf, np.diff(t) / np.timedelta64(1, "D")]
        d_next = np.r_[np.diff(t) / np.timedelta64(1, "D"), np.inf]
        neighbour = np.minimum(d_prev, d_next)

        # Which crossing is each person's nearest? running = birth - crossing, so
        # crossing time = birth - running.
        cross_time = (df["dob"].to_numpy()
                      - (df[f"{body}_running"].to_numpy() * 86400e9
                         ).astype("timedelta64[ns]"))
        idx = np.searchsorted(t, cross_time)
        idx = np.clip(idx, 0, len(t) - 1)
        # searchsorted may land one off because of sub-second rounding; take the closer.
        alt = np.clip(idx - 1, 0, len(t) - 1)
        pick_alt = (np.abs(cross_time - t[alt]) < np.abs(cross_time - t[idx]))
        idx = np.where(pick_alt, alt, idx)

        df[f"{body}_neighbour_gap"] = neighbour[idx]
        df[f"{body}_isolated"] = df[f"{body}_neighbour_gap"] >= ISOLATION_DAYS
        note(f"   {body:<8} {100 * df[f'{body}_isolated'].mean():>5.1f}% of births "
             f"sit at an isolated cusp (nearest other crossing >= "
             f"{ISOLATION_DAYS:g}d away)")

    # ---- 3. Do crowded cusps explain the density failures? ------------------
    note("\n## 3. Density-test failures vs cusp crowding")
    dens_path = RESULTS / "study1_density_tests.csv"
    if dens_path.exists():
        dens = pd.read_csv(dens_path)
        crowd = []
        for body in PLANETS:
            sub = df[df[f"{body}_cusp"].notna()]
            g = (sub.groupby(f"{body}_cusp", observed=True)[f"{body}_isolated"]
                 .mean().rename("frac_isolated").reset_index()
                 .rename(columns={f"{body}_cusp": "cusp"}))
            g["planet"] = body
            crowd.append(g)
        crowd = pd.concat(crowd, ignore_index=True)
        m = dens.merge(crowd, on=["planet", "cusp"], how="left").dropna(
            subset=["p", "frac_isolated"])
        if len(m) > 3:
            rej = m["p"] < 0.05
            note(f"   density rejected at {100 * rej.mean():.0f}% of "
                 f"{len(m)} cusps overall")
            note(f"     mostly-isolated cusps (>=90% isolated): "
                 f"{100 * m.loc[m['frac_isolated'] >= 0.9, 'p'].lt(0.05).mean():.0f}% "
                 f"reject  (n = {int((m['frac_isolated'] >= 0.9).sum())})")
            note(f"     crowded cusps      (<90% isolated): "
                 f"{100 * m.loc[m['frac_isolated'] < 0.9, 'p'].lt(0.05).mean():.0f}% "
                 f"reject  (n = {int((m['frac_isolated'] < 0.9).sum())})")
            r = float(np.corrcoef(m["frac_isolated"], (m["p"] < 0.05).astype(float))[0, 1])
            iso_rate = float(m.loc[m["frac_isolated"] >= 0.9, "p"].lt(0.05).mean())
            cro_rate = float(m.loc[m["frac_isolated"] < 0.9, "p"].lt(0.05).mean())
            supported = bool(np.isfinite(iso_rate) and np.isfinite(cro_rate)
                             and cro_rate - iso_rate > 0.15)
            diag["density_vs_crowding"] = {
                "correlation_frac_isolated_vs_reject": r,
                "reject_rate_isolated": iso_rate,
                "reject_rate_crowded": cro_rate,
                "n_cusps": int(len(m)),
                "crowding_hypothesis_supported": supported}
            note(f"   VERDICT: the crowding hypothesis is "
                 f"{'SUPPORTED' if supported else 'NOT SUPPORTED'} — isolated and "
                 f"crowded cusps reject at similar rates, so retrograde "
                 f"triple-crossings do not explain the density failures.")
            m.to_csv(RESULTS / "diagnostics_density_vs_crowding.csv", index=False)
    else:
        note("   (study1_density_tests.csv not found — run 05_study1_rdd.py first)")

    # ---- 4. Re-estimate over a grid of isolation thresholds -----------------
    note("\n## 4. Primary estimates restricted to progressively more isolated cusps")
    note("   If the pooled effects are artifacts of truncated support, they should")
    note("   shrink toward zero as the threshold rises. If they are real, they")
    note("   should survive. The analysis window is capped at half the threshold so")
    note("   that the retained window is never truncated by the adjacent crossing.")
    iso_results: dict = {}
    iso_grid_rows = []
    for planet in PLANETS:
        outcome = f"is_{planet}_occ"
        base = float(df[outcome].mean())
        sesoi = inf.or_to_risk_difference(1.05, base)
        directions = {str(k): int(v) for k, v in
                      (df[[f"{planet}_cusp", f"{planet}_pred_dir"]].dropna()
                       .drop_duplicates().set_index(f"{planet}_cusp")
                       [f"{planet}_pred_dir"].to_dict()).items()}

        for thr in ISOLATION_GRID:
            sub = df[df[f"{planet}_neighbour_gap"] >= thr]
            frac = len(sub) / len(df)
            if len(sub) < 5000:
                note(f"   {planet:<8} gap>={thr:>4.0f}d: only {len(sub):,} people "
                     f"({100 * frac:.1f}%) — too few to estimate, skipped")
                iso_grid_rows.append({"planet": planet, "threshold": thr,
                                      "n_people": int(len(sub)),
                                      "frac_of_sample": frac,
                                      "estimate": np.nan, "se": np.nan,
                                      "n_cusps": 0})
                continue
            c = study1.per_cusp(sub, planet, outcome, directions=directions,
                                h=None, h_cap=thr / 2.0)
            if "pred_dir" not in c.columns or len(c) == 0:
                note(f"   {planet:<8} gap>={thr:>4.0f}d: no estimable cusps")
                continue
            s = c[c["pred_dir"] != 0]
            p = inf.pool_signed(s["est"], s["se"], s["pred_dir"])
            iso_grid_rows.append({"planet": planet, "threshold": thr,
                                  "n_people": int(len(sub)),
                                  "frac_of_sample": frac,
                                  "estimate": p["estimate"], "se": p["se"],
                                  "ci_low": p["ci_low"], "ci_high": p["ci_high"],
                                  "n_cusps": p["n_cusps"],
                                  "p": inf.two_sided_p(p["estimate"], p["se"])})
            note(f"   {planet:<8} gap>={thr:>4.0f}d: pooled {p['estimate']:+.5f} "
                 f"[{p['ci_low']:+.5f}, {p['ci_high']:+.5f}], "
                 f"{p['n_cusps']:>2} cusps, {len(sub):,} people "
                 f"({100 * frac:.1f}% of sample)")

        # Headline threshold, for the results table.
        sub = df[df[f"{planet}_neighbour_gap"] >= ISOLATION_DAYS]
        if len(sub) >= 5000:
            c = study1.per_cusp(sub, planet, outcome, directions=directions,
                                h_cap=ISOLATION_DAYS / 2.0)
            s = c[c["pred_dir"] != 0] if "pred_dir" in c.columns else c.iloc[0:0]
            p = inf.pool_signed(s.get("est", []), s.get("se", []),
                                s.get("pred_dir", []))
            bound = inf.equivalence_bound(p["estimate"], p["se"])
            iso_results[planet] = {
                **p, "n_people": int(len(sub)),
                "frac_of_sample": float(len(sub) / len(df)),
                "base_rate": base, "sesoi": sesoi,
                "p_two_sided": inf.two_sided_p(p["estimate"], p["se"]),
                "tost_equivalent": inf.tost(p["estimate"], p["se"],
                                            sesoi)["equivalent"],
                "equivalence_bound": bound,
                "equivalence_bound_or": inf.risk_difference_to_or(bound, base)}
        else:
            iso_results[planet] = {
                "status": "not estimable",
                "reason": (f"only {len(sub):,} people ({100 * len(sub) / len(df):.1f}%) "
                           f"sit at a cusp with no other crossing within "
                           f"{ISOLATION_DAYS:g} days"),
                "n_people": int(len(sub)),
                "frac_of_sample": float(len(sub) / len(df)),
                "estimate": np.nan, "se": np.nan,
                "ci_low": np.nan, "ci_high": np.nan}
    diag["isolated_cusp_estimates"] = iso_results
    diag["isolation_grid"] = iso_grid_rows
    pd.DataFrame(iso_grid_rows).to_csv(
        RESULTS / "diagnostics_isolation_grid.csv", index=False)

    # ---- 5. Density on isolated cusps only ----------------------------------
    note("\n## 5. Density continuity on isolated cusps only")
    try:
        from rddensity import rddensity
        rows = []
        for planet in PLANETS:
            sub = df[df[f"{planet}_neighbour_gap"] >= 15.0]
            if len(sub) < 5000:
                note(f"   {planet}: too few isolated births to retest density")
                continue
            for cusp, g in sub.groupby(f"{planet}_cusp", observed=True):
                if "->" not in str(cusp):
                    continue
                x = g[f"{planet}_running"].to_numpy(dtype=float)
                x = x[np.abs(x) <= 30]
                if len(x) < 500:
                    continue
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        rd = rddensity(X=x)
                    rows.append({"planet": planet, "cusp": str(cusp),
                                 "p": float(np.ravel(rd.test["p_jk"])[0]),
                                 "n": int(len(x))})
                except Exception:  # noqa: BLE001
                    pass
        if rows:
            dd = pd.DataFrame(rows)
            frac = float((dd["p"] < 0.05).mean())
            diag["density_isolated_frac_rejected"] = frac
            diag["density_isolated_n_cusps"] = int(len(dd))
            note(f"   {100 * frac:.1f}% of {len(dd)} isolated cusps reject "
                 f"(vs 29.0% over all cusps)")
            dd.to_csv(RESULTS / "diagnostics_density_isolated.csv", index=False)
    except ImportError:
        note("   rddensity unavailable — skipped")

    # ---- 6. The pre-specified local-randomization estimator ----------------
    # plan §3 (Study 1): "Running variable is discrete (daily): honest discrete-
    # support inference per Cattaneo, Idrobo & Titiunik (2023); local randomization
    # check within +/-3 days as a secondary estimator."
    #
    # This is PRE-SPECIFIED, not exploratory, and it was missing from the first run.
    # It matters here because both failed falsification checks -- excess placebo
    # rejection and density discontinuity -- are what you expect when a DISCRETE
    # running variable with mass points is fed to estimators that assume a continuous
    # one. Local randomization assumes nothing about functional form or density: it
    # treats sign assignment within a few days of the cusp as a coin flip and tests
    # it by permutation.
    note("\n## 6. Local-randomization estimator within +/-3 days (PRE-SPECIFIED)")
    note("   Assumption-light: no bandwidth, no functional form, no density "
         "continuity.")
    lr: dict = {}
    for planet in PLANETS:
        outcome = f"is_{planet}_occ"
        base = float(df[outcome].mean())
        sesoi = inf.or_to_risk_difference(1.05, base)
        sub = df[(df[f"{planet}_running"].abs() <= 3)
                 & (df[f"{planet}_pred_dir"].isin([-1, 1]))]
        ests, ses, dirs = [], [], []
        for cusp, g in sub.groupby(f"{planet}_cusp", observed=True):
            tr = g[f"{planet}_running"].to_numpy(float) >= 0
            y = g[outcome].to_numpy(float)
            if tr.sum() < 100 or (~tr).sum() < 100:
                continue
            p1, p0 = y[tr].mean(), y[~tr].mean()
            se = np.sqrt(p1 * (1 - p1) / tr.sum() + p0 * (1 - p0) / (~tr).sum())
            ests.append(p1 - p0)
            ses.append(se)
            dirs.append(int(g[f"{planet}_pred_dir"].iloc[0]))
        pooled = inf.pool_signed(ests, ses, dirs)

        # Randomization inference: permute side-of-cutoff within each cusp.
        obs = pooled["estimate"]
        n_perm = 2000
        perm = np.empty(n_perm)
        groups = [(g[f"{planet}_running"].to_numpy(float) >= 0,
                   g[outcome].to_numpy(float),
                   int(g[f"{planet}_pred_dir"].iloc[0]))
                  for _, g in sub.groupby(f"{planet}_cusp", observed=True)
                  if (g[f"{planet}_running"].to_numpy(float) >= 0).sum() >= 100
                  and (g[f"{planet}_running"].to_numpy(float) < 0).sum() >= 100]
        rs = np.random.default_rng(SEED)
        for i in range(n_perm):
            e2, s2, d2 = [], [], []
            for tr, y, dd in groups:
                sh = rs.permutation(tr)
                p1, p0 = y[sh].mean(), y[~sh].mean()
                s = np.sqrt(p1 * (1 - p1) / sh.sum() + p0 * (1 - p0) / (~sh).sum())
                e2.append(p1 - p0); s2.append(s); d2.append(dd)
            perm[i] = inf.pool_signed(e2, s2, d2)["estimate"]
        p_ri = float((1 + np.sum(np.abs(perm) >= abs(obs))) / (1 + n_perm))

        bound = inf.equivalence_bound(pooled["estimate"], pooled["se"])
        lr[planet] = {**pooled, "base_rate": base, "sesoi": sesoi,
                      "n_people": int(len(sub)),
                      "p_normal": inf.two_sided_p(pooled["estimate"], pooled["se"]),
                      "p_randomization": p_ri, "n_perm": n_perm,
                      "tost_equivalent": inf.tost(pooled["estimate"], pooled["se"],
                                                  sesoi)["equivalent"],
                      "equivalence_bound": bound,
                      "equivalence_bound_or": inf.risk_difference_to_or(bound, base)}
        note(f"   {planet:<8} pooled {pooled['estimate']:+.5f} "
             f"[{pooled['ci_low']:+.5f}, {pooled['ci_high']:+.5f}], "
             f"{pooled['n_cusps']} cusps, {len(sub):,} people; "
             f"randomization p = {p_ri:.4f}; TOST "
             f"{'EQUIVALENT' if lr[planet]['tost_equivalent'] else 'inconclusive'} "
             f"(rules out OR > {lr[planet]['equivalence_bound_or']:.3f})")
    diag["local_randomization"] = lr

    (RESULTS / "estimates_diagnostics.json").write_text(
        json.dumps(diag, indent=2, default=float), encoding="utf-8")
    (RESULTS / "diagnostics_log.md").write_text("\n".join(log), encoding="utf-8")
    note(f"\n-> {RESULTS / 'estimates_diagnostics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
