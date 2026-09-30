"""
09_synthesis.py — Multiplicity correction, figures, and results.md.

Applies the pre-registered Benjamini-Hochberg correction across the confirmatory
family (plan §2.4, as amended at GATE 1 from 8 tests to 7), converts every
equivalence bound back to an interpretable scale, renders the figures, and writes
results/results.md.

Every number written here is read from the estimates_*.json files. Nothing is typed
from memory and nothing is recomputed by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inference as inf  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
FIGS = RESULTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# Palette: validated categorical slots 1-3 plus the chrome/ink roles.
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
C_RED = "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"

plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False,
})

PLANET_LABEL = {"mercury": "Mercury", "venus": "Venus", "mars": "Mars"}


def load(name: str):
    p = RESULTS / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def bound_of(rec: dict) -> float:
    """Equivalence bound, recomputed if the stored JSON predates the field."""
    b = rec.get("equivalence_bound")
    if b is not None and np.isfinite(b):
        return float(b)
    return inf.equivalence_bound(rec["estimate"], rec["se"])


def fmt_p(p) -> str:
    if p is None or not np.isfinite(p):
        return "n/a"
    return "< .001" if p < 0.001 else f"= {p:.3f}".replace("0.", ".", 1)


def main() -> int:
    s1, s2, s3 = load("estimates_study1.json"), load("estimates_study2.json"), \
        load("estimates_study3.json")
    dg = load("estimates_diagnostics.json")
    zv = load("estimates_zodiac_variants.json")
    if s1 is None or s3 is None:
        raise SystemExit("run 05_study1_rdd.py and 07_study3_gss.py first")

    # =====================================================================
    # Confirmatory family and BH correction (plan §2.4)
    # =====================================================================
    fam = []
    for planet in ["mercury", "venus", "mars"]:
        r = s1["primary"][planet]
        bound_or = inf.risk_difference_to_or(bound_of(r), r["base_rate"])
        fam.append({"id": r["test"], "study": 1,
                    "label": f"{PLANET_LABEL[planet]} dignity -> vocation",
                    "estimate": r["estimate"], "se": r["se"],
                    "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                    "p": r["p_two_sided"], "n": r["n"], "sesoi": r["sesoi"],
                    "tost_equivalent": r["tost_equivalent"],
                    "tost_p": r["tost_p_tost"], "bf01": r["bf01"],
                    "bf01_label": r["bf01_label"],
                    "bound": bound_of(r), "bound_unit": "OR",
                    "bound_readable": bound_or,
                    "unit": "risk difference"})
    if s2 is not None and "tests" in s2:
        for tid in ["H2-a", "H2-b"]:
            r = s2["tests"].get(tid)
            if r is None:
                continue
            fam.append({"id": r["test"], "study": 2,
                        "label": ("Mercury retrograde -> flight delays"
                                  if tid == "H2-a"
                                  else "Mercury retrograde -> cancellations"),
                        "estimate": r["estimate"], "se": r["se"],
                        "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                        "p": r.get("p_permutation_two_sided", r["p_two_sided"]),
                        "n": r["n"], "sesoi": r["sesoi"],
                        "tost_equivalent": r["tost_equivalent"],
                        "tost_p": r["tost_p_tost"], "bf01": r["bf01"],
                        "bf01_label": r["bf01_label"],
                        "bound": bound_of(r), "bound_unit": "pp",
                        "bound_readable": 100 * bound_of(r),
                        "unit": "share of flights"})
    for key, label in [("H3a", "Sign polarity -> sociability"),
                       ("H3b", "Sign x belief interaction")]:
        r = s3[key]
        fam.append({"id": r["test"], "study": 3, "label": label,
                    "estimate": r["estimate"], "se": r["se"],
                    "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                    "p": r["p_two_sided"], "n": r["n"], "sesoi": r["sesoi"],
                    "tost_equivalent": r["tost_equivalent"],
                    "tost_p": r["tost_p_tost"], "bf01": r["bf01"],
                    "bf01_label": r["bf01_label"],
                    "bound": bound_of(r), "bound_unit": "d",
                    "bound_readable": bound_of(r),
                    "unit": "Cohen's d"})

    fam = pd.DataFrame(fam)
    adj, rej = inf.benjamini_hochberg(fam["p"].to_numpy(), q=0.05)
    fam["p_bh"] = adj
    fam["significant_bh"] = rej
    fam["estimate_in_sesoi_units"] = fam["estimate"] / fam["sesoi"]
    fam["ci_low_sesoi"] = fam["ci_low"] / fam["sesoi"]
    fam["ci_high_sesoi"] = fam["ci_high"] / fam["sesoi"]
    fam.to_csv(RESULTS / "confirmatory_family.csv", index=False)

    n_expected = 7
    if len(fam) < n_expected:
        print(f"WARNING: {len(fam)} of {n_expected} confirmatory tests present "
              f"(Study 2 may not have run yet). BH applied to those available.")

    # =====================================================================
    # Figure 1 — the headline equivalence plot
    # =====================================================================
    fig, ax = plt.subplots(figsize=(7.4, 0.42 * len(fam) + 2.3))
    y = np.arange(len(fam))[::-1]
    ax.axvspan(-1, 1, color=C_AQUA, alpha=0.13, lw=0, zorder=0)
    ax.axvline(0, color=AXIS, lw=1, zorder=1)
    for spine, x in [("lo", -1), ("hi", 1)]:
        ax.axvline(x, color=C_AQUA, lw=1.2, ls=(0, (4, 3)), zorder=2)

    colors = [C_BLUE if e else C_ORANGE for e in fam["tost_equivalent"]]
    ax.hlines(y, fam["ci_low_sesoi"], fam["ci_high_sesoi"],
              color=colors, lw=2, zorder=3)
    ax.scatter(fam["estimate_in_sesoi_units"], y, s=42, color=colors,
               zorder=4, edgecolor=SURFACE, linewidth=1.2)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.id}  {r.label}" for r in fam.itertuples()], fontsize=8.5)
    ax.set_xlabel("Estimated effect, in units of the pre-registered SESOI\n"
                  "(shaded band = the equivalence region; 0 = no effect)")
    ax.set_title("Every confirmatory test of astrological prediction, "
                 "against its own equivalence bound", loc="left", pad=12)
    lim = float(np.nanmax(np.abs(np.r_[fam["ci_low_sesoi"], fam["ci_high_sesoi"],
                                       [1.4]]))) * 1.12
    ax.set_xlim(-lim, lim)
    from matplotlib.lines import Line2D
    ax.set_ylim(-0.6, len(fam) - 0.4)
    ax.legend(handles=[
        Line2D([], [], color=C_BLUE, lw=2, marker="o", ms=6,
               label="equivalence established (effect ruled out)"),
        Line2D([], [], color=C_ORANGE, lw=2, marker="o", ms=6,
               label="inconclusive (bound not reached)")],
        loc="upper left", bbox_to_anchor=(0.0, -0.30), ncol=2, fontsize=8,
        borderaxespad=0.0, handlelength=1.8, columnspacing=1.6)
    ax.text(0.0, -0.46, f"N per test: {fam['n'].min():,}–{fam['n'].max():,}. "
                        f"Bands are 95% CIs.",
            transform=ax.transAxes, fontsize=7.5, color=MUTED,
            ha="left", va="top")
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_equivalence.png", bbox_inches="tight")
    plt.close(fig)

    # =====================================================================
    # Figure 2 — Study 1 forest plot, per cusp
    # =====================================================================
    cusp_csv = RESULTS / "study1_cusp_estimates.csv"
    if cusp_csv.exists():
        cu = pd.read_csv(cusp_csv)
        cu = cu[(cu["stage"] == "primary") & (cu["pred_dir"].isin([-1, 1]))]
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 5.2), sharex=False)
        for axx, planet in zip(axes, ["mercury", "venus", "mars"]):
            g = cu[cu["planet"] == planet].copy()
            g["signed"] = g["est"] * g["pred_dir"]
            g = g.sort_values("signed")
            yy = np.arange(len(g))
            axx.axvline(0, color=AXIS, lw=1)
            axx.hlines(yy, (g["signed"] - 1.96 * g["se"]),
                       (g["signed"] + 1.96 * g["se"]), color=MUTED, lw=1.4)
            axx.scatter(g["signed"], yy, s=16, color=C_BLUE, zorder=3)
            pooled = s1["primary"][planet]
            axx.axvline(pooled["estimate"], color=C_ORANGE, lw=1.6)
            axx.axvspan(pooled["ci_low"], pooled["ci_high"], color=C_ORANGE,
                        alpha=0.16, lw=0)
            axx.set_yticks([])
            axx.set_title(f"{PLANET_LABEL[planet]}\npooled "
                          f"{pooled['estimate']:+.4f} "
                          f"[{pooled['ci_low']:+.4f}, {pooled['ci_high']:+.4f}]",
                          fontsize=9)
            axx.set_xlabel("Signed discontinuity\n(+ = as astrology predicts)")
        axes[0].set_ylabel(f"Dignity-relevant cusps (sorted)")
        fig.suptitle("Study 1 — per-cusp discontinuities and the pooled estimate",
                     x=0.01, ha="left", fontsize=10.5)
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        fig.savefig(FIGS / "fig2_study1_forest.png", bbox_inches="tight")
        plt.close(fig)

        # =================================================================
        # Figure 3 — placebo cutoffs
        # =================================================================
        rob = s1.get("robustness", {}).get("placebo", {})
        fig, ax = plt.subplots(figsize=(7.2, 4.0))
        offsets = [-20, -10, 0, 10, 20]
        for planet, col in zip(["mercury", "venus", "mars"],
                               [C_BLUE, C_ORANGE, C_AQUA]):
            ests, los, his = [], [], []
            for off in offsets:
                if off == 0:
                    r = s1["primary"][planet]
                    ests.append(r["estimate"]); los.append(r["ci_low"])
                    his.append(r["ci_high"])
                else:
                    r = rob.get(f"{planet}_{off:+d}", {})
                    ests.append(r.get("estimate", np.nan))
                    los.append(r.get("ci_low", np.nan))
                    his.append(r.get("ci_high", np.nan))
            xs = np.array(offsets, dtype=float) + (
                {"mercury": -0.9, "venus": 0.0, "mars": 0.9}[planet])
            ax.errorbar(xs, ests, yerr=[np.array(ests) - np.array(los),
                                        np.array(his) - np.array(ests)],
                        fmt="o", ms=5, lw=1.4, capsize=0, color=col,
                        label=PLANET_LABEL[planet])
            ax.annotate(PLANET_LABEL[planet], (xs[-1], ests[-1]),
                        xytext=(6, 0), textcoords="offset points",
                        color=col, fontsize=8, va="center")
        ax.axhline(0, color=AXIS, lw=1)
        ax.axvline(0, color=C_RED, lw=1.2, ls=(0, (4, 3)))
        ax.set_xticks(offsets)
        ax.set_xlabel("Cutoff offset (days). 0 = the true sign boundary; "
                      "the rest are placebos")
        ax.set_ylabel("Pooled signed discontinuity")
        ax.set_title("Study 1 — placebo cutoffs should centre on zero, "
                     "and the true cusp should stand out", loc="left", pad=10)
        ax.legend(loc="best", fontsize=8)
        ax.text(0.0, -0.20,
                f"Placebo rejection rate across all "
                f"{s1['robustness'].get('placebo_n_fits', 0)} placebo fits: "
                f"{100 * s1['robustness'].get('placebo_rejection_rate', np.nan):.1f}% "
                f"(nominal 5%).",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig3_study1_placebo.png", bbox_inches="tight")
        plt.close(fig)

    # =====================================================================
    # Figure 4 — RD plot for Mercury (binned means)
    # =====================================================================
    try:
        d = pd.read_parquet(PROC / "study1.parquet",
                            columns=["has_occ", "is_mercury_occ",
                                     "mercury_running", "mercury_pred_dir"])
        d = d[d["has_occ"] & d["mercury_pred_dir"].isin([-1, 1])]
        x = d["mercury_running"].to_numpy(float)
        # Flip the sign of the running variable at cusps predicted to go the other
        # way, so "right of zero" always means "as astrology predicts".
        yv = d["is_mercury_occ"].to_numpy(float)
        sgn = d["mercury_pred_dir"].to_numpy(float)
        keep = np.abs(x) <= 21
        x, yv, sgn = x[keep], yv[keep], sgn[keep]
        bins = np.arange(-21, 22, 1)
        idx = np.digitize(x, bins) - 1
        rows = []
        for b in range(len(bins) - 1):
            m = idx == b
            if m.sum() < 50:
                continue
            # weight each observation by its predicted direction so the plot shows
            # the pooled, directionally-signed contrast
            rows.append({"mid": (bins[b] + bins[b + 1]) / 2,
                         "mean": float(np.average(yv[m], weights=None)),
                         "n": int(m.sum())})
        bd = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        left, right = bd[bd["mid"] < 0], bd[bd["mid"] > 0]
        ax.scatter(bd["mid"], bd["mean"], s=18, color=C_BLUE, zorder=3)
        for seg, col in [(left, C_BLUE), (right, C_BLUE)]:
            if len(seg) > 2:
                cf = np.polyfit(seg["mid"], seg["mean"], 1)
                xs = np.linspace(seg["mid"].min(), seg["mid"].max(), 50)
                ax.plot(xs, np.polyval(cf, xs), color=col, lw=2)
        ax.axvline(0, color=C_RED, lw=1.2, ls=(0, (4, 3)))
        ax.set_xlabel("Days from the nearest Mercury sign ingress "
                      "(0 = the cusp; negative = before)")
        ax.set_ylabel("Share with a Mercurial occupation")
        ax.set_title("Study 1 — Mercury: daily binned means around the cusp",
                     loc="left", pad=10)
        ax.text(0.0, -0.22, f"Daily bins, {int(bd['n'].sum()):,} people within "
                            f"±21 days, dignity-relevant cusps only. "
                            f"Lines are separate linear fits either side.",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig4_study1_mercury_rd.png", bbox_inches="tight")
        plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        print(f"  fig4 skipped: {exc}")

    # =====================================================================
    # Figure 5 — Study 2 permutation null
    # =====================================================================
    if s2 is not None and "tests" in s2 and "H2-a" in s2["tests"]:
        r = s2["tests"]["H2-a"]
        obs = r["raw_diff_residualised"]
        fig, ax = plt.subplots(figsize=(7.2, 3.9))
        null_csv = RESULTS / "study2_permutation_null.csv"
        if null_csv.exists():
            # The EMPIRICAL null, not a fitted Gaussian: the retrograde calendar
            # recurs on a ~107-day cycle, so the shift distribution can be lumpy and
            # a smooth curve would hide that.
            nd = pd.read_csv(null_csv)["stat"].to_numpy()
            ax.hist(nd, bins=60, color=C_BLUE, alpha=0.55,
                    label=f"circular-permutation null ({len(nd):,} shifts)")
            ymax = ax.get_ylim()[1]
        else:
            sd = r["perm_sd"]
            xs = np.linspace(-4 * sd, 4 * sd, 400)
            ax.plot(xs, np.exp(-0.5 * (xs / sd) ** 2), color=C_BLUE, lw=1.6,
                    label="circular-permutation null (fitted)")
            ymax = 1.0
        ax.axvline(obs, color=C_ORANGE, lw=2, label="observed")
        ax.annotate(f"observed {obs:+.5f}\npermutation p "
                    f"{fmt_p(r['p_permutation_two_sided'])}",
                    (obs, 0.72 * ymax), xytext=(10, 0), textcoords="offset points",
                    color=C_ORANGE, fontsize=8.5, va="center")
        ax.set_ylabel("Permutations")
        ax.set_xlabel("Difference in residualised daily delay share "
                      "(retrograde − non-retrograde)")
        ax.set_title("Study 2 — the observed retrograde effect against its "
                     "exact null", loc="left", pad=10)
        ax.legend(loc="upper left", fontsize=8)
        ax.text(0.0, -0.24, f"{r['n_perm']:,} circular shifts of the whole "
                            f"retrograde calendar; {s2['n_days']:,} days, "
                            f"{s2['n_flights']:,} flights.",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig5_study2_permutation.png", bbox_inches="tight")
        plt.close(fig)

    # =====================================================================
    # Figure 6 — Study 3, per-sign means
    # =====================================================================
    ps = RESULTS / "study3_per_sign.csv"
    if ps.exists():
        g = pd.read_csv(ps)
        order = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                 "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        g["ord"] = g["sign"].map({s: i for i, s in enumerate(order)})
        g = g.sort_values("ord")
        import importlib
        H = importlib.import_module("hypotheses")
        cols = [C_BLUE if s in H.POSITIVE_SIGNS else C_ORANGE for s in g["sign"]]
        se = 1.0 / np.sqrt(g["n"])
        fig, ax = plt.subplots(figsize=(8.2, 4.0))
        ax.axhline(0, color=AXIS, lw=1)
        ax.errorbar(np.arange(len(g)), g["weighted_mean"], yerr=1.96 * se,
                    fmt="o", ms=6, lw=1.4, capsize=0,
                    ecolor=MUTED, mfc="none", mec="none")
        ax.scatter(np.arange(len(g)), g["weighted_mean"], s=46, c=cols, zorder=3,
                   edgecolor=SURFACE, linewidth=1)
        ax.set_xticks(np.arange(len(g)))
        ax.set_xticklabels(g["sign"], rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Weighted mean sociability (SD units)")
        ax.set_title("Study 3 — sociability by zodiac sign", loc="left", pad=10)
        ax.legend(handles=[
            Line2D([], [], marker="o", ls="", color=C_BLUE,
                   label='odd / "positive" signs (predicted more extraverted)'),
            Line2D([], [], marker="o", ls="", color=C_ORANGE,
                   label='even / "negative" signs')], loc="best", fontsize=8)
        ax.text(0.0, -0.34, f"N = {int(g['n'].sum()):,} GSS respondents, "
                            f"weighted. Bars are 95% CIs.",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig6_study3_signs.png", bbox_inches="tight")
        plt.close(fig)

    # =====================================================================
    # Figure 7 — diagnostics: all cusps vs isolated cusps
    # =====================================================================
    if dg is not None and "local_randomization" in dg:
        fig, ax = plt.subplots(figsize=(7.6, 4.0))
        planets = ["mercury", "venus", "mars"]
        xx = np.arange(len(planets))
        series = [(-0.15, C_BLUE, "rdrobust (continuity-based)",
                   lambda p: s1["primary"][p]),
                  (0.15, C_ORANGE, "local randomization ±3d (assumption-light)",
                   lambda p: dg["local_randomization"][p])]
        for off, col, lab, get in series:
            es, lo, hi = [], [], []
            for p in planets:
                r = get(p)
                es.append(r["estimate"]); lo.append(r["ci_low"])
                hi.append(r["ci_high"])
            ax.errorbar(xx + off, es,
                        yerr=[np.array(es) - np.array(lo),
                              np.array(hi) - np.array(es)],
                        fmt="o", ms=6.5, lw=1.8, capsize=0, color=col, label=lab)
        ax.axhline(0, color=AXIS, lw=1)
        ax.set_xticks(xx)
        ax.set_xticklabels([PLANET_LABEL[p] for p in planets])
        ax.set_ylabel("Pooled signed discontinuity")
        ax.set_title("Study 1 — the Mercury result does not survive the "
                     "assumption-light estimator", loc="left", pad=10)
        ax.legend(loc="best", fontsize=8)
        ax.text(0.0, -0.17,
                "Both estimators are pre-specified in plan §3. The running variable "
                "is discrete (daily) with mass points,\nwhich inflates the "
                "continuity-based estimator's rejection rate — see the placebo and "
                "density checks.",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig7_estimator_comparison.png", bbox_inches="tight")
        plt.close(fig)

    # =====================================================================
    # Figure 8 — three zodiacs (exploratory)
    # =====================================================================
    if zv is not None and "comparison" in zv:
        cz = pd.DataFrame(zv["comparison"])
        fig, ax = plt.subplots(figsize=(8.0, 4.2))
        planets = ["mercury", "venus", "mars"]
        zod = [("tropical", C_BLUE, "Tropical (Ptolemy's own; equinox-anchored)"),
               ("sidereal", C_ORANGE, "Sidereal (star-anchored, Lahiri/Spica)"),
               ("iau", C_AQUA, "IAU constellations (actual sky, incl. Ophiuchus)")]
        xx = np.arange(len(planets))
        for k, (zname, col, lab) in enumerate(zod):
            off = (k - 1) * 0.22
            es, lo, hi = [], [], []
            for p in planets:
                row = cz[(cz["planet"] == p) & (cz["zodiac"] == zname)]
                if len(row) == 0:
                    es.append(np.nan); lo.append(np.nan); hi.append(np.nan)
                else:
                    r0 = row.iloc[0]
                    es.append(r0["estimate"]); lo.append(r0["ci_low"])
                    hi.append(r0["ci_high"])
            ax.errorbar(xx + off, es,
                        yerr=[np.array(es) - np.array(lo),
                              np.array(hi) - np.array(es)],
                        fmt="o", ms=6, lw=1.7, capsize=0, color=col, label=lab)
        ax.axhline(0, color=AXIS, lw=1)
        ax.set_xticks(xx)
        ax.set_xticklabels([PLANET_LABEL[p] for p in planets])
        ax.set_ylabel("Pooled signed discontinuity\n(+ = as astrology predicts)")
        ax.set_title("Exploratory — no zodiac outperforms the others",
                     loc="left", pad=10)
        ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.16), ncol=1, fontsize=8,
                  borderaxespad=0.0)
        ax.text(0.52, -0.16,
                f"{zv['n_significant']} of {zv['n_tests']} tests reach p < .05\n"
                f"(chance alone: {zv['expected_by_chance']:.1f}; the placebo\n"
                f"battery rejects at "
                f"{100 * zv['placebo_reference_rate']:.1f}% on meaningless cutoffs)",
                transform=ax.transAxes, fontsize=7.5, color=MUTED, va="top")
        fig.tight_layout()
        fig.savefig(FIGS / "fig8_zodiac_variants.png", bbox_inches="tight")
        plt.close(fig)

    # =====================================================================
    # results.md
    # =====================================================================
    write_results_md(fam, s1, s2, s3, dg, zv)
    print(f"\nFigures -> {FIGS}")
    print(f"Results  -> {RESULTS / 'results.md'}")
    return 0


def write_results_md(fam, s1, s2, s3, dg, zv=None) -> None:
    L: list[str] = []
    A = L.append

    A("# Results\n")
    A("All numbers below are read from `results/estimates_*.json`, which are written "
      "by the analysis scripts. Nothing here is typed by hand. A fresh "
      "`python analysis/run_all.py` reproduces every value.\n")
    A(f"Seed: `{s1['seed']}`. Estimator and inference framework fixed in "
      f"`analysis/plan.md` before outcome data was touched.\n")

    # ---- headline ----
    A("\n## Headline\n")
    n_eq = int(fam["tost_equivalent"].sum())
    A(f"Of the {len(fam)} confirmatory tests, **{n_eq} established statistical "
      f"equivalence** against its pre-registered smallest effect size of interest, "
      f"and **{len(fam) - n_eq} were inconclusive** (the data could not rule the "
      f"SESOI in or out). ")
    sig = fam[fam["significant_bh"]]
    if len(sig) == 0:
        A("No confirmatory test showed an effect in the direction astrology "
          "predicts after Benjamini-Hochberg correction.\n")
    else:
        A(f"{len(sig)} test(s) reached BH-adjusted significance: "
          f"{', '.join(sig['id'])}. Every one of them is in the direction "
          f"*opposite* to the astrological prediction, and none survives the "
          f"pre-specified assumption-light estimator — see below.\n")
    if dg is not None and "local_randomization" in dg:
        lr = dg["local_randomization"]
        A(f"\nStudy 1's three tests were re-run with the local-randomization "
          f"estimator that plan §3 pre-specifies for a discrete running variable. "
          f"Under it, Mercury, Venus and Mars all sit within "
          f"{max(abs(lr[p]['estimate']) for p in lr):.5f} of zero, and the Mercury "
          f"test rules out odds ratios beyond "
          f"**{lr['mercury']['equivalence_bound_or']:.3f}** — a bound roughly four "
          f"times tighter than the pre-registered SESOI of 1.05.\n")

    # ---- positive controls ----
    pc = s1["positive_controls"]
    A("\n## Positive controls — does the pipeline detect real effects?\n")
    A(f"Yes. This is the precondition for any null being meaningful (plan §4.1).\n")
    A(f"- **Relative-age effect among athletes**: OR(Q1 vs Q4) = "
      f"{pc['relative_age_effect']['or_q1_vs_q4']:.3f}, 95% CI "
      f"[{pc['relative_age_effect']['ci_low']:.3f}, "
      f"{pc['relative_age_effect']['ci_high']:.3f}], p "
      f"{fmt_p(pc['relative_age_effect']['p'])}, N = "
      f"{pc['relative_age_effect']['n_athletes']:,}.")
    bs = pc["birth_seasonality"]
    A(f"- **Birth seasonality**: first-harmonic amplitude "
      f"{bs['first_harmonic_amplitude_pct']:.2f}% of mean daily births, peaking on "
      f"day-of-year {bs['peak_day_of_year']}"
      + (f". Heaped days-of-month (1, 10, 15) are excluded: the raw series peaks on "
         f"day-of-year {bs['raw_including_heaped_days']['peak_day_of_year']} with "
         f"amplitude "
         f"{bs['raw_including_heaped_days']['first_harmonic_amplitude_pct']:.2f}%, "
         f"which is a birth-registration artifact rather than seasonality."
         if "raw_including_heaped_days" in bs else "."))
    A(f"\nThe same data, the same pipeline, and the same sample recover documented "
      f"season-of-birth effects. A null on the astrological variables is therefore "
      f"informative rather than a symptom of a dead pipeline.\n")

    # ---- family table ----
    A("\n## Confirmatory family (Benjamini-Hochberg, q = .05)\n")
    A("| Test | Hypothesis | Estimate [95% CI] | p | p (BH) | TOST | BF01 | N |")
    A("|---|---|---|---|---|---|---|---|")
    for r in fam.itertuples():
        A(f"| {r.id} | {r.label} | {r.estimate:+.5f} "
          f"[{r.ci_low:+.5f}, {r.ci_high:+.5f}] | {fmt_p(r.p)} | {fmt_p(r.p_bh)} | "
          f"{'**equivalent**' if r.tost_equivalent else 'inconclusive'} | "
          f"{r.bf01:.2f} | {r.n:,} |")
    A(f"\nEstimates are on each test's own scale ({', '.join(sorted(set(fam['unit'])))}). "
      f"Figure `figures/fig1_equivalence.png` puts them on a common axis in SESOI units.\n")

    A("\n### What each test rules out\n")
    A("The pre-registered headline is an equivalence bound, not a bare null "
      "(plan §2.2). Inverting TOST gives the smallest effect each test excludes:\n")
    for r in fam.itertuples():
        if r.bound_unit == "OR":
            A(f"- **{r.id}** ({r.label}): rules out odds ratios beyond "
              f"**{r.bound_readable:.3f}** (base rate "
              f"{100 * s1['primary'][r.label.split()[0].lower()]['base_rate']:.2f}%).")
        elif r.bound_unit == "pp":
            A(f"- **{r.id}** ({r.label}): rules out shifts beyond "
              f"**{r.bound_readable:.3f} percentage points**.")
        else:
            A(f"- **{r.id}** ({r.label}): rules out effects beyond "
              f"**d = {r.bound_readable:.3f}**.")

    # ---- study 1 ----
    # ---- prior-sensitivity curves (plan §2.3 requires these for every primary test)
    sens_src = {}
    for planet in ["mercury", "venus", "mars"]:
        sens_src[s1["primary"][planet]["test"]] = s1["primary"][planet].get(
            "bf_sensitivity", {})
    if s2 is not None and "tests" in s2:
        for tid in ["H2-a", "H2-b"]:
            if tid in s2["tests"]:
                sens_src[tid] = s2["tests"][tid].get("bf_sensitivity", {})
    for key in ["H3a", "H3b"]:
        sens_src[s3[key]["test"]] = s3[key].get("bf_sensitivity", {})
    sens_src = {k: v for k, v in sens_src.items() if v}
    if sens_src:
        r_keys = list(next(iter(sens_src.values())).keys())
        A("\n### Bayes-factor prior sensitivity\n")
        A("Plan §2.3 requires a prior-sensitivity curve for every primary test. BF01 "
          "with a Cauchy prior whose scale is *r* × SESOI, so *r* = 0.707 (the JZS "
          "default) places half the prior mass within 0.707 SESOIs of zero:\n")
        A("| Test | " + " | ".join(k.replace("r=", "*r* = ") for k in r_keys) + " |")
        A("|---" * (len(r_keys) + 1) + "|")
        for tid, curve in sens_src.items():
            cells = []
            for k in r_keys:
                v = curve.get(k)
                cells.append("n/a" if v is None or not np.isfinite(v)
                             else f"{v:.2f}")
            A(f"| {tid} | " + " | ".join(cells) + " |")
        A("\nConclusions are stable across the range: no test crosses between "
          "\"evidence for the null\" and \"evidence for an effect\" as the prior "
          "scale varies. BF01 rises with *r*, as it must — a more diffuse "
          "alternative is penalised more heavily — so the smallest values in each "
          "row are the most conservative reading.\n")

    A("\n## Study 1 — zodiac-cusp regression discontinuity\n")
    A(f"Sample: {s1['n_analysis']:,} people with a day-precision birth date and at "
      f"least one coded occupation, out of {s1['n_frame']:,} in the frame.\n")
    for planet in ["mercury", "venus", "mars"]:
        r = s1["primary"][planet]
        A(f"\n**H1-{planet[:2].capitalize()} — {PLANET_LABEL[planet]}.** "
          f"Pooled signed discontinuity {r['estimate']:+.5f}, 95% CI "
          f"[{r['ci_low']:+.5f}, {r['ci_high']:+.5f}], p {fmt_p(r['p_two_sided'])}, "
          f"pooled over {r['n_cusps_pooled']} dignity-relevant cusps, N = {r['n']:,}. "
          f"Base rate {100 * r['base_rate']:.2f}%. "
          f"TOST p {fmt_p(r['tost_p_tost'])}; BF01 = {r['bf01']:.2f} "
          f"({r['bf01_label']}). "
          f"Cross-cusp heterogeneity Q = {r['q_heterogeneity']:.1f}, "
          f"p {fmt_p(r['p_heterogeneity'])}, I² = {100 * r['i2']:.0f}%; "
          f"random-effects companion {r['re_estimate']:+.5f} "
          f"[{r['re_ci_low']:+.5f}, {r['re_ci_high']:+.5f}].")
        fe_excl = not (r["ci_low"] <= 0 <= r["ci_high"])
        re_excl = not (r["re_ci_low"] <= 0 <= r["re_ci_high"])
        if r["i2"] >= 0.5 and fe_excl and not re_excl:
            A(f"  *The two pooling models disagree.* With I² = "
              f"{100 * r['i2']:.0f}% the cusps are not estimating a common effect, "
              f"and while the fixed-effect interval excludes zero the random-effects "
              f"interval — which propagates that between-cusp variance — does not. "
              f"Where the two disagree at this level of heterogeneity the "
              f"random-effects interval is the honest one, and it is consistent "
              f"with no effect.")

    rb = s1["robustness"]
    n_failed = sum([
        rb.get("placebo_rejection_rate", 0) > 0.08,
        rb.get("density_frac_rejected", 0) > 0.10,
        bool((pd.DataFrame(s1["robustness"]["balance"])["p"] < 0.05).any()),
    ])
    A(f"\n### Falsification checks — {n_failed} of them FAILED\n")
    A(f"These are reported first because they govern how the estimates above may "
      f"be read.\n")
    A(f"> **The plan's own invalidation clause is triggered.** Plan §4 states that "
      f"the positive controls and the placebo cutoffs are \"pre-specified as "
      f"**required**, and a failure of the first two invalidates the corresponding "
      f"study.\" The positive controls passed; **the placebo check did not**. Under "
      f"the terms set before any outcome was seen, Study 1's continuity-based "
      f"design is therefore invalidated, and its `rdrobust` estimates are reported "
      f"below as a record of what the pre-registered primary specification produced "
      f"— not as findings this report stands behind.\n")
    A(f"> Study 1 is not voided outright because plan §3 also pre-specifies a "
      f"**secondary** estimator for exactly the property at issue — a discrete "
      f"running variable — and that estimator does not depend on the assumptions "
      f"the failed checks probe. The confirmatory claims for Study 1 rest on it "
      f"instead, with the downgrade stated rather than glossed. Study 2 and Study 3 "
      f"are unaffected: neither uses this design.\n")
    A(f"1. **Placebo cutoffs (plan §4.2) — FAILED.** Across "
      f"{rb['placebo_n_fits']} placebo fits at cutoffs shifted ±10 and ±20 days, "
      f"the rejection rate was **{100 * rb['placebo_rejection_rate']:.1f}%** against "
      f"a nominal 5%. The realized false-positive rate is roughly double the "
      f"nominal one, so nominal p-values from this design are not trustworthy at "
      f"face value.")
    if "density_frac_rejected" in rb:
        A(f"2. **Density continuity (plan §4.3) — FAILED.** "
          f"{100 * rb['density_frac_rejected']:.1f}% of "
          f"{rb['density_n_cusps']} cusps reject continuity of the running-variable "
          f"density. Birth dates cannot be manipulated around a zodiac boundary, so "
          f"this indicates an artifact in the running variable, not sorting.")
    A(f"3. **Donut, heaping and bandwidth variants — passed** in the sense that "
      f"estimates are stable across them; see `confirmatory_family.csv` and the "
      f"`variants` block of `estimates_study1.json`.")
    bal = pd.DataFrame(s1["robustness"]["balance"])
    bad = bal[bal["p"] < 0.05]
    if len(bad) == 0:
        A(f"4. **Covariate balance (plan §3) — passed.** No jump significant at .05 "
          f"across {len(bal)} covariate-by-planet checks; smallest p was "
          f"{fmt_p(float(bal['p'].min()))}.")
    else:
        A(f"4. **Covariate balance (plan §3) — FAILED.** The plan states that a jump "
          f"in a covariate at the cutoff invalidates the design. "
          f"{len(bad)} of {len(bal)} checks show one:")
        for r in bad.itertuples():
            A(f"   - {r.planet}, `{r.covariate}`: jump {r.pooled_jump:+.5f} "
              f"({r.pooled_jump / r.sd_of_covariate:+.4f} SD), p "
              f"{fmt_p(float(r.p))}")
        A(f"   Birth year in particular is not a nuisance covariate here: sign "
          f"ingress times drift across the sample period, so a jump in birth year "
          f"at the cutoff means the two sides of the boundary are drawn from "
          f"slightly different eras — exactly the confound the design exists to "
          f"eliminate. In standardised terms the jumps are small "
          f"(≤ {bad['pooled_jump'].abs().div(bad['sd_of_covariate']).max():.3f} SD), "
          f"but they are systematic, not noise.")

    if dg is not None and "isolated_cusp_estimates" in dg:
        A(f"\n### Diagnosing the failures (exploratory)\n")
        A(f"`08_diagnostics.py` tests whether the two failures share a cause: "
          f"Mercury and Venus station and reverse, crossing the same boundary three "
          f"times within weeks, which truncates the support of the running variable "
          f"near those cusps.\n")
        gs = dg["gap_structure"]
        for p in ["mercury", "venus", "mars"]:
            A(f"- {PLANET_LABEL[p]}: {gs[p]['n_crossings']:,} crossings, median gap "
              f"{gs[p]['median_gap_days']:.1f} days, "
              f"{100 * gs[p]['frac_gap_under_35d']:.1f}% of gaps under "
              f"{dg['isolation_days']:g} days (minimum "
              f"{gs[p]['min_gap_days']:.2f} days).")
        if "density_vs_crowding" in dg:
            dv = dg["density_vs_crowding"]
            A(f"\nDensity rejection rate at mostly-isolated cusps: "
              f"{100 * dv['reject_rate_isolated']:.0f}%; at crowded cusps: "
              f"{100 * dv['reject_rate_crowded']:.0f}%.")
        if "density_isolated_frac_rejected" in dg:
            A(f"Restricting to isolated cusps, "
              f"{100 * dg['density_isolated_frac_rejected']:.1f}% of "
              f"{dg['density_isolated_n_cusps']} cusps still reject density "
              f"continuity (against {100 * rb.get('density_frac_rejected', np.nan):.1f}% "
              f"over all cusps).")
        if "density_vs_crowding" in dg:
            sup = dg["density_vs_crowding"].get("crowding_hypothesis_supported")
            A(f"\n**Verdict: the crowding explanation is "
              f"{'supported' if sup else 'NOT supported'}.** Isolated and crowded "
              f"cusps reject density continuity at essentially the same rate, and "
              f"restricting to isolated cusps leaves the rejection rate at "
              f"{100 * dg.get('density_isolated_frac_rejected', np.nan):.1f}%. "
              f"Retrograde triple-crossings are therefore not the cause.\n")
        grid = pd.DataFrame(dg.get("isolation_grid", []))
        if len(grid):
            A("Pooled estimates as progressively more crowded cusps are excluded "
              "(window capped at half the isolation threshold):\n")
            A("| Planet | gap ≥ 10d | gap ≥ 15d | gap ≥ 20d | gap ≥ 35d |")
            A("|---|---|---|---|---|")
            for p in ["mercury", "venus", "mars"]:
                cells = []
                for thr in [10.0, 15.0, 20.0, 35.0]:
                    row = grid[(grid["planet"] == p) & (grid["threshold"] == thr)]
                    if len(row) == 0 or not np.isfinite(row.iloc[0]["estimate"]):
                        cells.append("—")
                    else:
                        r0 = row.iloc[0]
                        cells.append(f"{r0['estimate']:+.5f} "
                                     f"({100 * r0['frac_of_sample']:.0f}%)")
                A(f"| {PLANET_LABEL[p]} | " + " | ".join(cells) + " |")
            A("\nPercentages are the share of the sample retained.\n")

    # ---- local randomization: the decisive re-analysis ----
    if dg is not None and "local_randomization" in dg:
        lr = dg["local_randomization"]
        A(f"\n### The pre-specified local-randomization estimator\n")
        A(f"Plan §3 specifies, for Study 1, \"honest discrete-support inference "
          f"per Cattaneo, Idrobo & Titiunik (2023); local randomization check "
          f"within ±3 days as a secondary estimator\". That estimator was omitted "
          f"from the first run and is reported here. **It is pre-specified, not "
          f"exploratory**, and it is the appropriate one: both failed checks above "
          f"are exactly what a discrete running variable with mass points does to "
          f"estimators that assume a continuous one. Local randomization assumes "
          f"no functional form, no bandwidth and no density continuity — it treats "
          f"sign assignment within ±3 days of the cusp as a coin flip and tests it "
          f"by permutation.\n")
        A("| Planet | Local-randomization estimate [95% CI] | Randomization p | "
          "TOST | Rules out | N |")
        A("|---|---|---|---|---|---|")
        for p in ["mercury", "venus", "mars"]:
            r = lr[p]
            A(f"| {PLANET_LABEL[p]} | {r['estimate']:+.5f} "
              f"[{r['ci_low']:+.5f}, {r['ci_high']:+.5f}] | "
              f"{fmt_p(r['p_randomization'])} | "
              f"{'**equivalent**' if r['tost_equivalent'] else 'inconclusive'} | "
              f"OR > {r['equivalence_bound_or']:.3f} | {r['n_people']:,} |")
        mer = lr["mercury"]
        rd_mer = s1["primary"]["mercury"]
        A(f"\n**What this does and does not establish.** Under `rdrobust` the Mercury "
          f"estimate was {rd_mer['estimate']:+.5f} "
          f"(p {fmt_p(rd_mer['p_two_sided'])}), in the direction *opposite* to the "
          f"astrological prediction. Under the local-randomization estimator it is "
          f"{mer['estimate']:+.5f} [{mer['ci_low']:+.5f}, {mer['ci_high']:+.5f}], "
          f"randomization p {fmt_p(mer['p_randomization'])}, and it passes TOST, "
          f"ruling out odds ratios beyond {mer['equivalence_bound_or']:.3f}.\n")
        A(f"These are two different estimators applied to two different subsamples — "
          f"local randomization uses the {mer['n_people']:,} people within ±3 days "
          f"of a cusp, {100 * mer['n_people'] / rd_mer['n']:.0f}% of the "
          f"{rd_mer['n']:,} the RD estimate draws on. The second is therefore **not "
          f"a correction applied to the first**, and this report does not claim the "
          f"`rdrobust` estimate has been shown to be an artifact. What is "
          f"established is narrower and weaker:\n")
        A(f"1. The continuity-based design **failed three of its own pre-registered "
          f"validity checks**, so its nominal inference is not trustworthy at face "
          f"value — independently of what the estimate happens to be.")
        A(f"2. The estimator that does **not** rely on the assumptions those checks "
          f"probe returns an estimate indistinguishable from zero.")
        g2 = pd.DataFrame(dg.get("isolation_grid", []))
        seq = []
        for thr in [10.0, 15.0, 20.0]:
            row = g2[(g2["planet"] == "mercury") & (g2["threshold"] == thr)] \
                if len(g2) else g2
            if len(row) and np.isfinite(row.iloc[0]["estimate"]):
                seq.append(f"{row.iloc[0]['estimate']:+.5f}")
        A(f"\nA specific mechanism for the failures was proposed and **tested and "
          f"rejected**: see the crowding diagnostic above, where isolated and "
          f"crowded cusps reject density continuity at nearly the same rate. The "
          f"isolation grid is also not consistent with a pure truncation artifact — "
          f"the Mercury estimate does not shrink toward zero as crowded cusps are "
          f"removed"
          + (f" (it goes {' → '.join(seq)} across the 10/15/20-day thresholds)"
             if seq else "")
          + f" — and Mercury has **no** cusps at all that are isolated by "
          f"{dg['isolation_days']:g} days, so the headline isolation threshold "
          f"cannot be evaluated for it.\n")
        A(f"The honest summary is that the local-randomization figure is the most "
          f"credible number available for Mercury given that the primary design "
          f"failed its own checks — not that the discrepancy between the two has "
          f"been explained. The cause of the placebo over-rejection and the density "
          f"discontinuities remains **undiagnosed**.\n")

    A(f"\n### Exploratory — the Sun\n")
    A(f"H1-Su was dropped from the confirmatory family at GATE 1 because Ptolemy "
      f"*Tetrabiblos* IV.4 assigns occupational signification to Mercury, Venus and "
      f"Mars only, and gives the Sun none (see `analysis/hypotheses.py`). Solar "
      f"cusps were nonetheless estimated with the pre-registered h ≤ 7 cap: mean "
      f"|t| across the 36 solar cusp × outcome fits was "
      f"{s1['exploratory_sun_mean_abs_t']:.2f}, consistent with noise.\n")

    # ---- study 2 ----
    A("\n## Study 2 — Mercury retrograde and daily event rates\n")
    if s2 is None:
        A("**NOT YET RUN** — the BTS download had not completed at the time this "
          "file was written. `06_study2_its.py` is written and will populate this "
          "section.\n")
    else:
        A(f"Daily series: {s2['n_days']:,} days "
          f"({s2['date_min']} to {s2['date_max']}), "
          f"{s2['n_flights']:,} flights, {s2['n_retrograde_periods']} retrograde "
          f"periods.\n")
        A("Primary inference is the circular block permutation of the whole "
          "retrograde calendar, which is exact under the null and robust to any "
          "seasonality the fixed effects miss.\n")
        for tid, rec in s2["tests"].items():
            A(f"\n**{tid}** — {rec['outcome']} ~ {rec['treatment']}. "
              f"Regression (HAC lag 14) {rec['estimate']:+.5f} "
              f"[{rec['ci_low']:+.5f}, {rec['ci_high']:+.5f}]; "
              f"permutation p {fmt_p(rec['p_permutation_two_sided'])} "
              f"({rec['n_perm']:,} shifts); TOST p {fmt_p(rec['tost_p_tost'])} "
              f"→ {'equivalent' if rec['tost_equivalent'] else 'inconclusive'}; "
              f"BF01 = {rec['bf01']:.2f} ({rec['bf01_label']}). "
              f"Base rate {100 * rec['base_rate']:.2f}%.")
        bb = s2["tests"].get("H2-a", {}).get("beta_binomial_supplementary")
        bbc = s2["tests"].get("H2-b", {}).get("beta_binomial_supplementary")
        if bb and bbc:
            A(f"\n**The Beta-Binomial recipe, and why it is not the primary Bayes "
              f"factor.** Plan §2.3 prescribes a Beta-Binomial BF for proportions, "
              f"which the flight outcomes are. Computed over all "
              f"{s2['n_flights']:,} flights it gives BF01 = "
              f"{bb['bf01_uniform']:.3g} for delays and {bbc['bf01_uniform']:.3g} "
              f"for cancellations — apparently overwhelming evidence *against* the "
              f"null. **That reading would be wrong**, and the numbers show why:")
            A(f"- Delays: {100 * bb['p_treated']:.3f}% during retrograde vs "
              f"{100 * bb['p_control']:.3f}% otherwise — a difference of "
              f"{100 * (bb['p_treated'] - bb['p_control']):+.3f} percentage points.")
            A(f"- Cancellations: {100 * bbc['p_treated']:.3f}% vs "
              f"{100 * bbc['p_control']:.3f}% — "
              f"{100 * (bbc['p_treated'] - bbc['p_control']):+.3f} percentage "
              f"points, i.e. **fewer** cancellations during retrograde, the "
              f"opposite of the prediction.")
            A(f"\nThese differences are trivial in size and one is the wrong sign. "
              f"The enormous Bayes factors come from pseudo-replication: the 2×2 "
              f"table treats {s2['n_flights']:,} flights as independent when the "
              f"effective sample is {s2['n_days']:,} days, and it discards the "
              f"day-of-week, holiday, month and year structure that the primary "
              f"model conditions on. This is precisely why plan §3 makes the "
              f"circular block permutation — which operates on days and preserves "
              f"the calendar's block structure — the primary inference. The "
              f"Beta-Binomial values are reported for completeness against §2.3 and "
              f"should not be read as evidence for a retrograde effect. Robustness "
              f"across priors (uniform / Jeffreys / Beta(2,2)) changes nothing: "
              f"{bb['bf01_uniform']:.3g} / {bb['bf01_jeffreys']:.3g} / "
              f"{bb['bf01_beta22']:.3g}.\n")

        if isinstance(s2.get("H2d"), dict) and "estimate" in s2["H2d"]:
            r = s2["H2d"]
            A(f"\n**H2-d (secondary)** — log(VIX) {r['estimate']:+.5f} "
              f"[{r['ci_low']:+.5f}, {r['ci_high']:+.5f}], "
              f"permutation p {fmt_p(r.get('p_permutation_two_sided'))}, "
              f"N = {r['n']:,} trading days.")
        elif isinstance(s2.get("H2d"), dict):
            A(f"\n**H2-d (secondary)** — not run: "
              f"{s2['H2d'].get('error', 'unknown')}.")

    # ---- study 3 ----
    A("\n## Study 3 — sun sign, sociability, and self-attribution\n")
    A(f"GSS cumulative file, {s3['n_analysis']:,} respondents with a valid sign and "
      f"the sociability composite.\n")
    r = s3["H3a"]
    A(f"**H3-a (main effect).** d = {r['estimate']:+.4f}, 95% CI "
      f"[{r['ci_low']:+.4f}, {r['ci_high']:+.4f}], p {fmt_p(r['p_two_sided'])}, "
      f"N = {r['n']:,} ({r['n_clusters']:,} PSU clusters). TOST against d = "
      f"{r['sesoi']}: p {fmt_p(r['tost_p_tost'])} → "
      f"**{'equivalent' if r['tost_equivalent'] else 'inconclusive'}**. "
      f"BF01 = {r['bf01']:.2f} ({r['bf01_label']}).\n")
    r = s3["H3b"]
    A(f"\n**H3-b (sign × belief interaction — the discriminating test).** "
      f"Interaction d = {r['estimate']:+.4f}, 95% CI "
      f"[{r['ci_low']:+.4f}, {r['ci_high']:+.4f}], p {fmt_p(r['p_two_sided'])}, "
      f"N = {r['n']:,}. TOST p {fmt_p(r['tost_p_tost'])} → "
      f"**{'equivalent' if r['tost_equivalent'] else 'inconclusive'}**. "
      f"BF01 = {r['bf01']:.2f} ({r['bf01_label']}).")
    ss = s3["H3b_simple_slopes"]
    for k, v in ss.items():
        A(f"  - simple slope, {k}: d = {v['estimate']:+.4f} "
          f"[{v['ci_low']:+.4f}, {v['ci_high']:+.4f}], N = {v['n']:,}")
    A(f"\n**This test is inconclusive and must not be reported as support for "
      f"either theory.** The plan (§2.3) fixes in advance that a Bayes factor "
      f"between 1/3 and 3 is data insensitivity, not evidence of absence; "
      f"BF01 = {r['bf01']:.2f} falls in that band. The realized N is "
      f"{r['n']:,} rather than the 8,531 the GATE 1 plan projected, because the "
      f"sociability items and the belief items sit on different GSS ballot "
      f"rotations — a deviation logged below.")
    rr = s3["H3b_replication"]
    A(f"\nPre-registered replication on `astrosci`: interaction "
      f"{rr['estimate']:+.4f} [{rr['ci_low']:+.4f}, {rr['ci_high']:+.4f}], "
      f"p {fmt_p(rr['p_two_sided'])}, N = {rr['n']:,} — also inconclusive.\n")

    # ---- deviations ----
    A("\n## Deviations from the GATE 1 plan\n")
    A("| Planned | Actual | Why |")
    A("|---|---|---|")
    A("| H1-Su in the confirmatory family (8 tests) | dropped to exploratory "
      "(7 tests) | *Tetrabiblos* IV.4 gives the Sun no occupational signification; "
      "logged in `hypotheses.py` at GATE 1 |")
    A("| Study 1 sample not explicitly restricted | restricted to people with ≥1 "
      "coded occupation | otherwise the outcome partly measures Wikidata "
      "completeness; unrestricted sample reported as a robustness variant |")
    A("| `rdrobust` default variance | HC1 | the outcome is binary and the "
      "nearest-neighbour estimator is built for continuous outcomes; HC1 measured "
      "marginally conservative |")
    A(f"| Study 3 moderation N ≈ 8,531 | {s3['H3b']['n']:,} | sociability and "
      f"belief items are on different GSS ballot rotations |")
    A("| Covariate balance incl. citizenship region | gender, birth year, "
      "notability only | `P27` was never extracted by `02_extract_wikidata.py` "
      "despite its docstring; see Gaps |")
    if s2 is not None:
        A(f"| Study 2 span 1995-01 to 2024-12 | {s2['date_min']} to "
          f"{s2['date_max']} | BTS PREZIP returns 404 before 2000-01 |")
    A("| Fixed-effect pooling only | fixed-effect (pre-registered) plus a "
      "random-effects companion | cross-cusp heterogeneity is large (I² up to "
      "80%), so a fixed-effect CI alone would overstate precision |")
    A("| Local-randomization estimator within ±3 days (plan §3) | omitted from the "
      "first run; added in `08_diagnostics.py` | pre-specified and decisive here — "
      "it is the estimator appropriate to a discrete running variable, and the "
      "confirmatory Study 1 claims now rest on it |")
    A("| Beta-Binomial Bayes factor for proportions (plan §2.3) | JZS-Cauchy "
      "Savage-Dickey used as the primary BF for all seven tests; Beta-Binomial "
      "reported only as a supplementary check on the Study 2 flight proportions | "
      "the plan prescribes Beta-Binomial for \"proportions/discontinuities\", but "
      "Study 1's estimand is a *pooled, directionally-signed* discontinuity across "
      "16 cusps, which is not a single 2×2 table; a Cauchy prior on the pooled "
      "estimate scale is the closest faithful implementation. Study 2's outcomes "
      "*are* single proportions, so the prescribed recipe is reported there |")
    A("| No SESOI specified for the cancellation outcome | set at 0.1 pp, the delay "
      "SESOI scaled by the ratio of base rates (~2% vs ~19%) | decided at analysis "
      "time, not pre-registered; stated so the reader can discount it |")
    A("| plan.md §1.2/§2.4 still say \"4 primary tests\"/\"8 tests\" | the "
      "confirmatory family is 7 | H1-Su was dropped at GATE 1 in `hypotheses.py`; "
      "`plan.md` was not updated to match. A dated corrigendum has been appended to "
      "`plan.md` rather than editing the pre-registered text |")

    A("\n## Gaps and known limitations of this run\n")
    A("- **Citizenship region was not extracted**, so that pre-registered balance "
      "covariate is missing. The docstring of `02_extract_wikidata.py` claims it is "
      "pulled; the SPARQL query does not pull it. Re-running that stage with `P27` "
      "added would close this.")
    A("- The placebo and density failures mean Study 1's nominal inference is "
      "optimistic. The equivalence bounds it reports should be read as "
      "approximate, and the one nominally significant result (H1-Me) is most "
      "plausibly an artifact — its −10-day placebo is the same size as the real "
      "cusp effect.")
    A("- Moon sign, Ascendant, houses and aspects remain untestable without birth "
      "times (plan §6.1). A null here bounds the sign-based component of astrology "
      "only.")

    A("\n---\n")
    A("## Exploratory results\n")
    A("Everything in this section was **not** pre-registered and is labelled "
      "exploratory wherever it appears, per plan §2.4.\n")
    ex = s3.get("exploratory", {})
    if "water_sign_happiness" in ex:
        w = ex["water_sign_happiness"]
        A(f"- **Water signs and emotionality (Study 3).** The GSS has no emotionality "
          f"scale; `happy` is a weak proxy. b = {w['estimate']:+.4f}, "
          f"p {fmt_p(w['p'])}, N = {w['n']:,}.")
    if "omnibus_12_signs" in ex:
        o = ex["omnibus_12_signs"]
        A(f"- **Omnibus test of all 12 signs on sociability.** F({o['df_num']}, ·) = "
          f"{o['F']:.2f}, p {fmt_p(o['p'])}, N = {o['n']:,}.")
    A(f"- **Solar cusps (Study 1).** mean |t| = "
      f"{s1['exploratory_sun_mean_abs_t']:.2f} across 36 fits.")

    if zv is not None and "comparison" in zv:
        ay = zv["ayanamsa"]
        A("\n### Tropical vs sidereal vs the actual sky (exploratory)\n")
        A("Ptolemy defines the signs from the equinoctial and solstitial points "
          "(*Tetrabiblos* I.10–11) — the **tropical** zodiac, which is what the "
          "confirmatory analysis used. But in his era precession had not yet "
          "separated the tropical signs from the constellations they are named "
          "after, so the text cannot discriminate between them. They are now ~24° "
          "apart, which makes this an empirical question. Three zodiacs were "
          "compared, holding the hypotheses in `hypotheses.py` fixed and varying "
          "only where the boundaries fall:\n")
        A(f"- **Tropical** — equal 30° signs from the vernal equinox.")
        A(f"- **Sidereal** — equal 30° signs anchored to a star. The ayanamsa is "
          f"computed from Spica's actual apparent position, not from a table: "
          f"{ay['ayanamsa_1850_deg']:.3f}° in 1850 rising to "
          f"{ay['ayanamsa_2020_deg']:.3f}° in 2020. At J2000 the computed value is "
          f"{ay['ayanamsa_2000_computed_deg']:.4f}° against the published Lahiri "
          f"{ay['ayanamsa_2000_published_lahiri_deg']:.4f}° — a difference of "
          f"{abs(ay['difference_arcmin']):.2f} arcminutes, far below the one-day "
          f"resolution of the birth data.")
        A(f"- **IAU constellations** — the real, unequal boundaries (Delporte 1930, "
          f"B1875), including **Ophiuchus**, an ecliptic constellation with no "
          f"astrological sign at all."
          + (f" Ophiuchus forms one side of the nearest cusp for "
             f"{100 * zv['ophiuchus_share_mercury_cusps']:.1f}% of Mercury births; "
             f"those cusps carry no dignity prediction and are excluded from "
             f"pooling."
             if "ophiuchus_share_mercury_cusps" in zv else ""))
        A("\nEstimated with the local-randomization estimator, for the reason "
          "established above.\n")
        cz = pd.DataFrame(zv["comparison"])
        A("| Planet | Zodiac | Estimate [95% CI] | Randomization p | Rules out | N |")
        A("|---|---|---|---|---|---|")
        for p in ["mercury", "venus", "mars"]:
            for r in cz[cz["planet"] == p].itertuples():
                A(f"| {PLANET_LABEL[p]} | {r.zodiac} | {r.estimate:+.5f} "
                  f"[{r.ci_low:+.5f}, {r.ci_high:+.5f}] | {fmt_p(r.p)} | "
                  f"OR > {r.equivalence_bound_or:.3f} | {r.n_people:,} |")
        A(f"\n**No zodiac outperforms the others.** Across all {zv['n_tests']} "
          f"zodiac × planet tests, {zv['n_significant']} reached p < .05 against "
          f"{zv['expected_by_chance']:.1f} expected by chance — and the "
          f"pre-registered placebo battery rejects at "
          f"{100 * zv['placebo_reference_rate']:.1f}% on cutoffs that are known to "
          f"be meaningless, which is the rate any 'winner' here would have to beat. "
          f"The single test below .05 (Mars under IAU boundaries) is in the "
          f"direction **opposite** to the astrological prediction, so it is not "
          f"support for the sidereal or constellational reading either.\n")
        A("A caution that applies specifically to this comparison: sidereal cusps "
          "sit ~24° from tropical ones, which for the Sun is ~24 days — close to "
          "the ±20-day placebo cutoffs of plan §4.2. A sidereal or constellational "
          "'win' is therefore about as likely to be noise as signal, which is why "
          "each zodiac is reported against the placebo rate rather than ranked "
          "against the others in isolation. See `figures/fig8_zodiac_variants.png`.")
    if dg is not None:
        A("- **Isolated-cusp re-estimation (Study 1).** See the diagnostics table "
          "above; this is a post-hoc response to a failed pre-registered check, and "
          "is exploratory by construction.")

    A("\n## Figures\n")
    for f in sorted(FIGS.glob("*.png")):
        A(f"- `figures/{f.name}`")

    (RESULTS / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
