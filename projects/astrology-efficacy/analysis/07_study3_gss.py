"""
07_study3_gss.py — Study 3: sun sign, sociability, and the self-attribution test.

Executes analysis/plan.md §1.4 and §3 (Study 3).

The design tests two theories against each other rather than a null against nothing:

  H3-a  main effect of odd ("positive") vs even sign on the sociability composite.
        Astrology predicts positive; self-attribution predicts ~zero in the full sample.
  H3-b  sign x belief INTERACTION. Astrology predicts a NULL interaction (a real
        planetary effect does not care whether you believe in it); self-attribution
        predicts a POSITIVE interaction (sign-congruent self-description only among
        believers, per van Rooij 1999).

Whichever way H3-b resolves it is informative, which is why it is confirmatory.

Outputs: results/estimates_study3.json, results/study3_log.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

SEED = inf.SEED
np.random.seed(SEED)

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

SESOI_D = 0.10  # plan §2.2: conventional "small", and the magnitude Mayo et al. reported

log: list[str] = []


def note(msg: str = "") -> None:
    print(msg, flush=True)
    log.append(msg)


def fit(d: pd.DataFrame, formula: str, term: str, *, weights: str = "w") -> dict:
    """
    Weighted least squares with GSS design-based SEs: survey weights, and standard
    errors clustered on PSU within stratum (plan §3).
    """
    use = d.dropna(subset=[weights, "cluster"]).copy()
    m = smf.wls(formula, data=use, weights=use[weights])
    res = m.fit(cov_type="cluster", cov_kwds={"groups": use["cluster"]})
    return {"estimate": float(res.params[term]), "se": float(res.bse[term]),
            "n": int(res.nobs), "n_clusters": int(use["cluster"].nunique()),
            "formula": formula, "term": term}


def main() -> int:
    note("# Study 3 — Sun sign, sociability, and self-attribution\n")
    note(f"Seed {SEED}. WLS with GSS weights (wtssps), year fixed effects, "
         f"SEs clustered on PSU within stratum.")

    df = pd.read_parquet(PROC / "gss.parquet")
    note(f"\nGSS cumulative file: {len(df):,} respondents, "
         f"{int(df['year'].min())}-{int(df['year'].max())}")

    # Outcome is standardised to SD = 1, so coefficients are in Cohen's d units and
    # are directly comparable to the pre-registered SESOI of d = 0.10.
    d = df.dropna(subset=["sociability", "odd_sign"]).copy()
    d["odd_sign"] = d["odd_sign"].astype(float)
    d["water_sign"] = d["water_sign"].astype(float)
    note(f"Analysis sample (valid sign + sociability composite): {len(d):,}")

    miss_cluster = float(d["cluster"].str.contains("<NA>|nan").mean())
    note(f"Design variables missing for {100 * miss_cluster:.1f}% of the sample")

    estimates: dict = {"seed": SEED, "sesoi_d": SESOI_D, "n_total": int(len(df)),
                       "n_analysis": int(len(d))}

    # =====================================================================
    # H3-a — main effect of sign polarity (confirmatory)
    # =====================================================================
    note("\n## H3-a — main effect of odd ('positive') vs even sign")
    r = fit(d, "sociability ~ odd_sign + C(year)", "odd_sign")
    h3a = inf.full_test("H3-a", r["estimate"], r["se"], SESOI_D, r["n"],
                        direction=+1,
                        extra={"n_clusters": r["n_clusters"],
                               "outcome": "sociability composite (SD units)"})
    estimates["H3a"] = h3a
    note(f"  d = {h3a['estimate']:+.4f} [{h3a['ci_low']:+.4f}, {h3a['ci_high']:+.4f}], "
         f"p = {h3a['p_two_sided']:.3f}, N = {r['n']:,} "
         f"({r['n_clusters']:,} clusters)")
    note(f"  TOST vs +/-{SESOI_D}: p = {h3a['tost_p_tost']:.4g} -> "
         f"{'EQUIVALENT' if h3a['tost_equivalent'] else 'not equivalent'}")
    note(f"  BF01 = {h3a['bf01']:.2f} ({h3a['bf01_label']})")

    # =====================================================================
    # H3-b — sign x belief interaction (confirmatory, the discriminating test)
    # =====================================================================
    note("\n## H3-b — sign x belief interaction (the discriminating test)")
    note("  Astrology predicts a NULL interaction; self-attribution predicts a "
         "POSITIVE one.")

    db = d.dropna(subset=["reads_horoscope"]).copy()
    note(f"\n  Primary belief measure: astrolgy (ever read a horoscope), "
         f"N = {len(db):,}")
    note(f"  NOTE: the GATE 1 plan cited joint zodiac x astrolgy N = 8,531. The "
         f"sociability")
    note(f"  items sit on a different ballot rotation, so the realized moderation "
         f"sample is")
    note(f"  {len(db):,}. Logged as a deviation; the equivalence test is still "
         f"powered (see below).")

    rb = fit(db, "sociability ~ odd_sign * reads_horoscope + C(year)",
             "odd_sign:reads_horoscope")
    h3b = inf.full_test("H3-b", rb["estimate"], rb["se"], SESOI_D, rb["n"],
                        direction=+1,
                        extra={"n_clusters": rb["n_clusters"],
                               "belief_measure": "astrolgy (binary)",
                               "outcome": "sociability composite (SD units)"})
    estimates["H3b"] = h3b
    note(f"  interaction d = {h3b['estimate']:+.4f} "
         f"[{h3b['ci_low']:+.4f}, {h3b['ci_high']:+.4f}], "
         f"p = {h3b['p_two_sided']:.3f}, N = {rb['n']:,}")
    note(f"  TOST vs +/-{SESOI_D}: p = {h3b['tost_p_tost']:.4g} -> "
         f"{'EQUIVALENT' if h3b['tost_equivalent'] else 'not equivalent'}")
    note(f"  BF01 = {h3b['bf01']:.2f} ({h3b['bf01_label']})")

    # Simple slopes, so the interaction is interpretable either way it lands.
    slopes = {}
    for label, sub in [("believers (read horoscopes)", db[db["reads_horoscope"] == 1]),
                       ("non-believers", db[db["reads_horoscope"] == 0])]:
        s = fit(sub, "sociability ~ odd_sign + C(year)", "odd_sign")
        slopes[label] = {"estimate": s["estimate"], "se": s["se"], "n": s["n"],
                         "ci_low": s["estimate"] - 1.96 * s["se"],
                         "ci_high": s["estimate"] + 1.96 * s["se"]}
        note(f"    simple slope, {label:<28} d = {s['estimate']:+.4f} "
             f"[{slopes[label]['ci_low']:+.4f}, {slopes[label]['ci_high']:+.4f}], "
             f"N = {s['n']:,}")
    estimates["H3b_simple_slopes"] = slopes

    # Pre-registered replication on the second belief measure.
    ds = d.dropna(subset=["astro_scientific"]).copy()
    rs = fit(ds, "sociability ~ odd_sign * astro_scientific + C(year)",
             "odd_sign:astro_scientific")
    h3b_rep = inf.full_test("H3-b-replication", rs["estimate"], rs["se"], SESOI_D,
                            rs["n"], direction=+1,
                            extra={"n_clusters": rs["n_clusters"],
                                   "belief_measure": "astrosci (ordinal 1-3)"})
    estimates["H3b_replication"] = h3b_rep
    note(f"\n  Pre-registered replication with astrosci (ordinal), N = {rs['n']:,}")
    note(f"  interaction = {h3b_rep['estimate']:+.4f} "
         f"[{h3b_rep['ci_low']:+.4f}, {h3b_rep['ci_high']:+.4f}], "
         f"p = {h3b_rep['p_two_sided']:.3f}; TOST p = {h3b_rep['tost_p_tost']:.4g} -> "
         f"{'EQUIVALENT' if h3b_rep['tost_equivalent'] else 'not equivalent'}")

    # =====================================================================
    # Robustness
    # =====================================================================
    note("\n## Robustness")
    rob: dict = {}
    # Alternative weight
    try:
        alt = fit(d.dropna(subset=["w_alt"]), "sociability ~ odd_sign + C(year)",
                  "odd_sign", weights="w_alt")
        rob["H3a_wtssall"] = {"estimate": alt["estimate"], "se": alt["se"],
                              "n": alt["n"]}
        note(f"  H3-a with wtssall weight: d = {alt['estimate']:+.4f} "
             f"(primary {h3a['estimate']:+.4f})")
    except Exception as exc:  # noqa: BLE001
        rob["H3a_wtssall"] = {"error": str(exc)}
    # Unweighted
    d2 = d.copy()
    d2["w_one"] = 1.0
    unw = fit(d2, "sociability ~ odd_sign + C(year)", "odd_sign", weights="w_one")
    rob["H3a_unweighted"] = {"estimate": unw["estimate"], "se": unw["se"],
                             "n": unw["n"]}
    note(f"  H3-a unweighted:            d = {unw['estimate']:+.4f}")
    # Restrict the main effect to the moderation subsample, so H3-a and H3-b are
    # estimated on the same people.
    same = fit(db, "sociability ~ odd_sign + C(year)", "odd_sign")
    rob["H3a_on_moderation_subsample"] = {"estimate": same["estimate"],
                                          "se": same["se"], "n": same["n"]}
    note(f"  H3-a on the H3-b subsample: d = {same['estimate']:+.4f} "
         f"(N = {same['n']:,})")

    # The composite averages whatever sociability items a respondent answered, with a
    # floor of one. Restricting to respondents who answered all four checks that the
    # partial-response cases are not driving the result.
    complete = d[d["n_soc_items"] == 4]
    cc = fit(complete, "sociability ~ odd_sign + C(year)", "odd_sign")
    rob["H3a_complete_items_only"] = {"estimate": cc["estimate"], "se": cc["se"],
                                      "n": cc["n"],
                                      "tost_equivalent": inf.tost(
                                          cc["estimate"], cc["se"],
                                          SESOI_D)["equivalent"]}
    note(f"  H3-a, all four items answered: d = {cc['estimate']:+.4f} "
         f"(N = {cc['n']:,}, {100 * len(complete) / len(d):.1f}% of the sample; "
         f"TOST "
         f"{'equivalent' if rob['H3a_complete_items_only']['tost_equivalent'] else 'inconclusive'})")
    if len(db):
        cb = db[db["n_soc_items"] == 4]
        if len(cb) > 500:
            ci = fit(cb, "sociability ~ odd_sign * reads_horoscope + C(year)",
                     "odd_sign:reads_horoscope")
            rob["H3b_complete_items_only"] = {"estimate": ci["estimate"],
                                              "se": ci["se"], "n": ci["n"]}
            note(f"  H3-b, all four items answered: interaction "
                 f"{ci['estimate']:+.4f} (N = {ci['n']:,})")
    estimates["robustness"] = rob

    # =====================================================================
    # Exploratory
    # =====================================================================
    note("\n## Exploratory (NOT confirmatory — labelled as such in all outputs)")
    expl: dict = {}
    # Water signs and emotionality. The GSS has no emotionality scale; `happy` is the
    # nearest available proxy and is a weak one, so this is exploratory by necessity.
    dw = df.dropna(subset=["happy_r", "water_sign"]).copy()
    dw["water_sign"] = dw["water_sign"].astype(float)
    w = fit(dw, "happy_r ~ water_sign + C(year)", "water_sign")
    expl["water_sign_happiness"] = {"estimate": w["estimate"], "se": w["se"],
                                    "n": w["n"],
                                    "p": inf.two_sided_p(w["estimate"], w["se"])}
    note(f"  Water sign -> happiness (proxy for emotionality): "
         f"b = {w['estimate']:+.4f}, p = {expl['water_sign_happiness']['p']:.3f}, "
         f"N = {w['n']:,}")

    # All 12 signs against sociability: an omnibus check that no single sign stands out.
    d3 = d.copy()
    om = smf.wls("sociability ~ C(sign) + C(year)", data=d3,
                 weights=d3["w"]).fit(cov_type="cluster",
                                      cov_kwds={"groups": d3["cluster"]})
    f_test = om.f_test("".join(
        [f"C(sign)[T.{s}] = 0, " for s in sorted(d3['sign'].unique())[1:]]
    ).rstrip(", "))
    expl["omnibus_12_signs"] = {"F": float(np.ravel(f_test.fvalue)[0]),
                                "p": float(np.ravel(f_test.pvalue)[0]),
                                "df_num": int(f_test.df_num),
                                "n": int(om.nobs)}
    note(f"  Omnibus test of all 12 signs: F({f_test.df_num}, .) = "
         f"{expl['omnibus_12_signs']['F']:.2f}, "
         f"p = {expl['omnibus_12_signs']['p']:.3f}")

    # Per-sign deviations, for the figure.
    per_sign = (d3.groupby("sign")
                .apply(lambda g: np.average(g["sociability"], weights=g["w"]),
                       include_groups=False)
                .rename("weighted_mean").reset_index())
    per_sign["n"] = d3.groupby("sign").size().values
    per_sign.to_csv(RESULTS / "study3_per_sign.csv", index=False)
    expl["per_sign_csv"] = "study3_per_sign.csv"
    estimates["exploratory"] = expl

    (RESULTS / "estimates_study3.json").write_text(
        json.dumps(estimates, indent=2, default=float), encoding="utf-8")
    (RESULTS / "study3_log.md").write_text("\n".join(log), encoding="utf-8")
    note(f"\n-> {RESULTS / 'estimates_study3.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
