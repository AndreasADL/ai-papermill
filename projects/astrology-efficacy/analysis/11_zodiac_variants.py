"""
11_zodiac_variants.py — Tropical vs sidereal vs actual-sky zodiacs (EXPLORATORY).

NOT PRE-REGISTERED. Added after the GATE 1 confirmatory analysis was complete and its
outcomes seen, at the user's request. Everything produced here is exploratory and is
labelled as such in every output. The HYPOTHESES are unchanged and still come from the
frozen `hypotheses.py`; only the definition of where the sign boundaries fall changes.

THE QUESTION
------------
Ptolemy defines the signs from the equinoctial and solstitial points (*Tetrabiblos*
I.10-11) — i.e. the TROPICAL zodiac, which is what the confirmatory analysis used. But
in Ptolemy's era precession had not yet separated the tropical signs from the
constellations they are named after (the ayanamsa was ~0 in the early centuries CE), so
his text cannot discriminate between the two. They are now ~24 degrees apart. That makes
this an empirical question rather than an exegetical one.

Three zodiacs are compared:

  TROPICAL   equal 30-degree signs measured from the vernal equinox.
             Ptolemy's own definition; Western astrology. (The confirmatory analysis.)

  SIDEREAL   equal 30-degree signs anchored to a fixed star. Vedic astrology, and the
             operationalization implied by "Ptolemy really meant the constellations".
             Anchored here by the Lahiri/Chitrapaksha convention: Spica at exactly
             180 degrees of sidereal longitude. The ayanamsa is computed from Spica's
             ACTUAL apparent position per epoch, not from a table.

  IAU        the real, unequal constellation boundaries (Delporte 1930, B1875), which
             is what "where the planets actually are" strictly means. These are not
             30 degrees wide — the Sun spends ~6 days in Scorpius and ~18 in Ophiuchus,
             a constellation with no astrological sign at all.

A CAUTION, stated up front
--------------------------
Sidereal cusps sit ~24 degrees from tropical ones, which for the Sun is ~24 days — close
to the +/-20-day PLACEBO cutoffs of plan §4.2, which are supposed to show nothing. So a
sidereal "win" is as easily noise as signal. Each zodiac is therefore reported against
the placebo distribution, not ranked against the others in isolation.

Primary estimator here is LOCAL RANDOMIZATION (+/-3 days), for the reason established in
08_diagnostics.py: the running variable is discrete and the continuity-based estimator
over-rejects on it. rdrobust is reported alongside as a secondary.

Outputs: results/estimates_zodiac_variants.json, results/zodiac_variants_*.csv
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
from skyfield.api import Star, load_constellation_map
from skyfield.framelib import ecliptic_frame
from skyfield.searchlib import find_discrete

warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hypotheses as H  # noqa: E402
import inference as inf  # noqa: E402

eph = import_module("01_ephemeris")
study1 = import_module("05_study1_rdd")

SEED = inf.SEED
np.random.seed(SEED)

PROJ = Path(__file__).resolve().parent.parent
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

PLANETS = ["mercury", "venus", "mars"]
YEAR_START, YEAR_END = 1852, 2020
INGRESS_START, INGRESS_END = 1850, 2022
LR_WINDOW = 3.0        # local-randomization window, matching plan §3
SESOI_OR = 1.05

# Spica (alpha Virginis), HIP 65474. Astrometry from the Hipparcos catalogue
# (van Leeuwen 2007 reduction). The Lahiri/Chitrapaksha ayanamsa is DEFINED by placing
# this star at 180 degrees of sidereal longitude, so computing its apparent tropical
# longitude per epoch gives the ayanamsa directly.
SPICA = dict(ra_hours=(13, 25, 11.579), dec_degrees=(-11, 9, 40.75),
             ra_mas_per_year=-42.35, dec_mas_per_year=-30.67, parallax_mas=13.06)
LAHIRI_J2000_DEG = 23.85306   # published value, used only as a validation check

# IAU constellation abbreviation -> astrological sign name. Constellations with no
# corresponding sign (Ophiuchus above all, plus the occasional off-ecliptic excursion)
# map to themselves, which makes `predicted_direction` return 0 and excludes them from
# the pooled estimate — the correct handling, since Ptolemy assigns them no dignity.
IAU_TO_SIGN = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Cnc": "Cancer",
    "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
    "Sgr": "Sagittarius", "Cap": "Capricorn", "Aqr": "Aquarius", "Psc": "Pisces",
    # Ophiuchus is a real ecliptic constellation with no astrological sign. It is
    # named rather than dropped so that its cusps are visible in the output; because
    # "Ophiuchus" appears in neither DOMICILE nor DETRIMENT, `predicted_direction`
    # returns 0 for its boundaries and they are excluded from the pooled estimate.
    "Oph": "Ophiuchus",
}

log: list[str] = []


def note(msg: str = "") -> None:
    print(msg, flush=True)
    log.append(msg)


# ---------------------------------------------------------------------------
# Ayanamsa, from the actual star
# ---------------------------------------------------------------------------
def ayanamsa_polynomial() -> tuple[np.poly1d, dict]:
    """
    Fit ayanamsa(year) from Spica's computed apparent ecliptic longitude.

    Precession is smooth and very nearly linear over the 170-year sample, so a
    quadratic in decimal year is accurate to far below the one-day resolution of the
    birth data (one day of solar motion is ~1 degree; the fit residual is arcseconds).
    """
    ts, planets = eph._setup()
    earth = planets["earth"]
    spica = Star(**SPICA)
    years = np.arange(INGRESS_START, INGRESS_END + 1, 5)
    lons = []
    for y in years:
        t = ts.utc(int(y), 7, 1)
        ast = earth.at(t).observe(spica).apparent()
        _, lon, _ = ast.frame_latlon(ecliptic_frame)
        lons.append(float(lon.degrees))
    ayan = (np.asarray(lons) - 180.0) % 360.0
    coef = np.polyfit(years.astype(float), ayan, 2)
    poly = np.poly1d(coef)
    resid_arcsec = float(np.max(np.abs(poly(years) - ayan)) * 3600.0)

    # Validation against the published Lahiri value at J2000.0.
    at_2000 = float(poly(2000.0))
    diag = {"ayanamsa_2000_computed_deg": at_2000,
            "ayanamsa_2000_published_lahiri_deg": LAHIRI_J2000_DEG,
            "difference_arcmin": (at_2000 - LAHIRI_J2000_DEG) * 60.0,
            "fit_max_residual_arcsec": resid_arcsec,
            "ayanamsa_1850_deg": float(poly(1850.0)),
            "ayanamsa_2020_deg": float(poly(2020.0))}
    return poly, diag


def _decimal_year(t) -> np.ndarray:
    """Decimal year from a skyfield Time (calendar year plus fraction)."""
    cal = t.utc
    y = np.atleast_1d(np.asarray(cal[0], dtype=float))
    doy = np.atleast_1d(np.asarray(cal[1], dtype=float)) * 30.44
    return y + doy / 365.25


def sidereal_ingresses(year_start: int, year_end: int, body: str,
                       poly: np.poly1d) -> pd.DataFrame:
    """Sign ingresses under the sidereal zodiac (equal signs, Spica-anchored)."""
    ts, _ = eph._setup()

    def sign_index(t):
        lon = eph._ecliptic_lon(body, t)
        sid = (lon - poly(_decimal_year(t))) % 360.0
        return (sid // 30).astype(int)

    sign_index.step_days = eph.STEP_DAYS[body]
    t0 = ts.utc(year_start, 1, 1)
    t1 = ts.utc(year_end + 1, 1, 2)
    times, signs = find_discrete(t0, t1, sign_index)
    df = pd.DataFrame({
        "ingress_utc": pd.to_datetime([t.utc_iso() for t in times]),
        "sign_index": np.asarray(signs, dtype=int)})
    df["sign"] = [eph.SIGNS[i] for i in df["sign_index"]]
    return df.sort_values("ingress_utc").reset_index(drop=True)


def iau_ingresses(year_start: int, year_end: int, body: str) -> pd.DataFrame:
    """
    Constellation boundary crossings under the real IAU boundaries.

    Found on a daily grid: the birth data is day-precision, so sub-day refinement of
    the boundary would be spurious precision. The ingress is timed at midnight of the
    first day on which the body is inside the new constellation.
    """
    ts, planets = eph._setup()
    earth = planets["earth"]
    # Reuse the ephemeris module's own body-name mapping (DE440s exposes Mars only
    # as a system barycenter), so both zodiacs observe exactly the same target.
    target = planets[eph._TARGET[body]]
    cmap = load_constellation_map()

    days = pd.date_range(f"{year_start}-01-01", f"{year_end}-12-31", freq="D",
                         tz="UTC")
    labels = np.empty(len(days), dtype=object)
    # Chunked: skyfield's nutation step allocates a (687 x n_times) array, which blows
    # up memory if the whole 170-year grid is requested at once.
    CHUNK = 3000
    for i in range(0, len(days), CHUNK):
        sl = days[i:i + CHUNK]
        t = ts.utc(sl.year.values, sl.month.values, sl.day.values)
        ast = earth.at(t).observe(target).apparent()
        labels[i:i + CHUNK] = np.asarray(cmap(ast), dtype=object)

    lab = pd.Series(labels, index=days).astype(str)

    # The ecliptic clips the corners of a few non-zodiacal constellations (Cetus,
    # Orion, Sextans), so a planet can spend a day or two in one. Those are grazes,
    # not zodiacal boundaries: counting them would fragment the cusp structure and
    # create artificially crowded cutoffs. They are therefore absorbed into the
    # preceding zodiacal constellation. OPHIUCHUS IS KEPT — it is a genuine, long
    # ecliptic transit (~18 days for the Sun) and is the substantive point of this
    # variant, being a constellation with no astrological sign at all.
    keep = set(IAU_TO_SIGN) | {"Oph"}
    strays = ~lab.isin(keep)
    lab = lab.where(~strays).ffill().bfill()

    changed = lab != lab.shift(1)
    changed.iloc[0] = False
    ing = pd.DataFrame({"ingress_utc": lab.index[changed],
                        "constellation": lab[changed].to_numpy()})
    ing.attrs["stray_days"] = int(strays.sum())
    ing.attrs["total_days"] = int(len(lab))
    ing["sign"] = ing["constellation"].map(
        lambda c: IAU_TO_SIGN.get(str(c), f"IAU:{c}"))
    ing["sign_index"] = range(len(ing))
    return ing.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------
def local_randomization(df: pd.DataFrame, planet: str, outcome: str,
                        run_col: str, cusp_col: str, dir_col: str,
                        n_perm: int = 2000) -> dict:
    """Assumption-light pooled estimate within +/-LR_WINDOW days of each cusp."""
    sub = df[(df[run_col].abs() <= LR_WINDOW) & (df[dir_col].isin([-1, 1]))]
    groups, ests, ses, dirs = [], [], [], []
    for _, g in sub.groupby(cusp_col, observed=True):
        tr = g[run_col].to_numpy(float) >= 0
        y = g[outcome].to_numpy(float)
        if tr.sum() < 100 or (~tr).sum() < 100:
            continue
        p1, p0 = y[tr].mean(), y[~tr].mean()
        ests.append(p1 - p0)
        ses.append(np.sqrt(p1 * (1 - p1) / tr.sum() + p0 * (1 - p0) / (~tr).sum()))
        dirs.append(int(g[dir_col].iloc[0]))
        groups.append((tr, y, dirs[-1]))
    if not groups:
        return {"estimate": np.nan, "se": np.nan, "n_cusps": 0,
                "n_people": int(len(sub)), "p_randomization": np.nan}
    pooled = inf.pool_signed(ests, ses, dirs)

    rs = np.random.default_rng(SEED)
    perm = np.empty(n_perm)
    for i in range(n_perm):
        e2, s2, d2 = [], [], []
        for tr, y, dd in groups:
            sh = rs.permutation(tr)
            p1, p0 = y[sh].mean(), y[~sh].mean()
            e2.append(p1 - p0)
            s2.append(np.sqrt(p1 * (1 - p1) / sh.sum() + p0 * (1 - p0) / (~sh).sum()))
            d2.append(dd)
        perm[i] = inf.pool_signed(e2, s2, d2)["estimate"]
    obs = pooled["estimate"]
    p_ri = float((1 + np.sum(np.abs(perm) >= abs(obs))) / (1 + n_perm))
    return {**pooled, "n_people": int(len(sub)), "p_randomization": p_ri,
            "n_perm": n_perm}


def main() -> int:
    t_start = time.perf_counter()
    note("# Zodiac variants — tropical vs sidereal vs actual sky (EXPLORATORY)\n")
    note("NOT pre-registered. Hypotheses are unchanged and still come from the frozen")
    note("hypotheses.py; only the sign-boundary definition varies.\n")

    out: dict = {"seed": SEED, "status": "exploratory, not pre-registered",
                 "lr_window_days": LR_WINDOW}

    # ---- ayanamsa ------------------------------------------------------
    note("## Ayanamsa, computed from Spica's actual apparent position")
    poly, ayan_diag = ayanamsa_polynomial()
    out["ayanamsa"] = ayan_diag
    note(f"   1850: {ayan_diag['ayanamsa_1850_deg']:.4f} deg   "
         f"2020: {ayan_diag['ayanamsa_2020_deg']:.4f} deg")
    note(f"   J2000 computed {ayan_diag['ayanamsa_2000_computed_deg']:.5f} deg vs "
         f"published Lahiri {LAHIRI_J2000_DEG:.5f} deg "
         f"(difference {ayan_diag['difference_arcmin']:+.2f} arcmin)")
    note(f"   quadratic fit max residual: "
         f"{ayan_diag['fit_max_residual_arcsec']:.2f} arcsec "
         f"(one day of solar motion is 3600 arcsec)")

    # ---- load the people ------------------------------------------------
    cols = ["qid", "dob", "has_occ", "is_mercury_occ", "is_venus_occ",
            "is_mars_occ", "is_heaped_day"]
    people = pd.read_parquet(PROC / "study1.parquet", columns=cols)
    people = people[people["has_occ"]].reset_index(drop=True)
    note(f"\nAnalysis sample: {len(people):,} people with >=1 coded occupation")

    # ---- build each zodiac ----------------------------------------------
    zodiacs = {}
    for zname in ["sidereal", "iau"]:
        note(f"\n## Building the {zname} zodiac")
        for planet in PLANETS:
            t0 = time.perf_counter()
            cache = PROC / f"ingresses_{zname}_{planet}.parquet"
            if cache.exists():
                ing = pd.read_parquet(cache)
            else:
                if zname == "sidereal":
                    parts = [sidereal_ingresses(y, min(y + 9, INGRESS_END), planet,
                                                poly)
                             for y in range(INGRESS_START, INGRESS_END + 1, 10)]
                else:
                    parts = [iau_ingresses(y, min(y + 9, INGRESS_END), planet)
                             for y in range(INGRESS_START, INGRESS_END + 1, 10)]
                ing = (pd.concat(parts, ignore_index=True)
                       .drop_duplicates(subset=["ingress_utc"])
                       .sort_values("ingress_utc").reset_index(drop=True))
                ing.to_parquet(cache, index=False)
            assigned = eph.assign_sign(people["dob"], ing)
            key = f"{zname}_{planet}"
            people[f"{key}_running"] = assigned["running_days"].values
            people[f"{key}_cusp"] = assigned["cusp_id"].values
            dirs = {}
            for c in pd.unique(assigned["cusp_id"].dropna()):
                a, _, b = str(c).partition("->")
                dirs[str(c)] = H.predicted_direction(planet, a, b)
            people[f"{key}_dir"] = people[f"{key}_cusp"].map(dirs)
            n_signed = sum(1 for v in dirs.values() if v != 0)
            note(f"   {planet:<8} {len(ing):>5,} crossings, {len(dirs):>3} cusp types, "
                 f"{n_signed:>3} dignity-relevant  ({time.perf_counter() - t0:.0f}s)")
            zodiacs[key] = {"n_crossings": int(len(ing)),
                            "n_cusp_types": len(dirs),
                            "n_dignity_relevant": n_signed}
    out["zodiac_structure"] = zodiacs

    if "iau_mercury_cusp" in people:
        oph = people["iau_mercury_cusp"].astype(str).str.contains("Ophiuchus").mean()
        note(f"\n   Ophiuchus appears in {100 * oph:.1f}% of Mercury's nearest-cusp "
             f"labels — a constellation with no astrological sign, so those cusps are "
             f"dignity-neutral and excluded from pooling.")
        out["ophiuchus_share_mercury_cusps"] = float(oph)

    # ---- estimate under each zodiac -------------------------------------
    note("\n## Pooled directional estimates under each zodiac")
    note("   Primary estimator: local randomization (+/-3 days), per 08_diagnostics.py.")
    note("   Positive = the direction astrology predicts.\n")
    comparison = []
    s1 = json.loads((RESULTS / "estimates_study1.json").read_text(encoding="utf-8"))
    dg_path = RESULTS / "estimates_diagnostics.json"
    dg = json.loads(dg_path.read_text(encoding="utf-8")) if dg_path.exists() else None

    for planet in PLANETS:
        outcome = f"is_{planet}_occ"
        base = float(people[outcome].mean())
        sesoi = inf.or_to_risk_difference(SESOI_OR, base)

        # Tropical, from the confirmatory run (local randomization where available).
        if dg and "local_randomization" in dg:
            tr = dg["local_randomization"][planet]
            comparison.append({
                "planet": planet, "zodiac": "tropical", "estimator": "local_rand",
                "estimate": tr["estimate"], "se": tr["se"],
                "ci_low": tr["ci_low"], "ci_high": tr["ci_high"],
                "p": tr["p_randomization"], "n_cusps": tr["n_cusps"],
                "n_people": tr["n_people"],
                "equivalence_bound_or": tr["equivalence_bound_or"],
                "tost_equivalent": tr["tost_equivalent"]})

        for zname in ["sidereal", "iau"]:
            key = f"{zname}_{planet}"
            r = local_randomization(people, planet, outcome,
                                    f"{key}_running", f"{key}_cusp", f"{key}_dir")
            bound = inf.equivalence_bound(r["estimate"], r["se"])
            comparison.append({
                "planet": planet, "zodiac": zname, "estimator": "local_rand",
                "estimate": r["estimate"], "se": r["se"],
                "ci_low": r.get("ci_low", np.nan), "ci_high": r.get("ci_high", np.nan),
                "p": r["p_randomization"], "n_cusps": r["n_cusps"],
                "n_people": r["n_people"],
                "equivalence_bound_or": inf.risk_difference_to_or(bound, base),
                "tost_equivalent": inf.tost(r["estimate"], r["se"],
                                            sesoi)["equivalent"]})

    comp = pd.DataFrame(comparison)
    comp.to_csv(RESULTS / "zodiac_variants_comparison.csv", index=False)
    out["comparison"] = comparison

    for planet in PLANETS:
        note(f"   {planet.upper()}  (base rate "
             f"{100 * float(people[f'is_{planet}_occ'].mean()):.2f}%)")
        for r in comp[comp["planet"] == planet].itertuples():
            note(f"     {r.zodiac:<9} {r.estimate:+.5f} "
                 f"[{r.ci_low:+.5f}, {r.ci_high:+.5f}]  "
                 f"randomization p = {r.p:.4f}  "
                 f"{r.n_cusps:>2} cusps  N = {r.n_people:>9,}  "
                 f"rules out OR > {r.equivalence_bound_or:.3f}")
        note("")

    # ---- which zodiac, if any, does better? ------------------------------
    note("## Which zodiac performs better?")
    best = []
    for planet in PLANETS:
        sub = comp[comp["planet"] == planet]
        if sub["p"].notna().any():
            b = sub.loc[sub["p"].idxmin()]
            best.append({"planet": planet, "zodiac": b["zodiac"],
                         "p": float(b["p"]), "estimate": float(b["estimate"])})
            note(f"   {planet:<8} smallest randomization p: {b['zodiac']} "
                 f"(p = {b['p']:.4f}, estimate {b['estimate']:+.5f})")
    out["smallest_p_per_planet"] = best

    n_tests = int(comp["p"].notna().sum())
    n_sig = int((comp["p"] < 0.05).sum())
    note(f"\n   Across all {n_tests} zodiac x planet tests, {n_sig} reached p < .05.")
    note(f"   Expected by chance alone at alpha = .05: {0.05 * n_tests:.1f}.")
    note(f"   The pre-registered placebo battery (plan §4.2) rejected at "
         f"{100 * s1['robustness']['placebo_rejection_rate']:.1f}% on cutoffs known to "
         f"be meaningless, which is the reference rate any 'winner' here must beat.")
    out["n_tests"] = n_tests
    out["n_significant"] = n_sig
    out["expected_by_chance"] = 0.05 * n_tests
    out["placebo_reference_rate"] = s1["robustness"]["placebo_rejection_rate"]

    (RESULTS / "estimates_zodiac_variants.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    (RESULTS / "zodiac_variants_log.md").write_text("\n".join(log), encoding="utf-8")
    note(f"\nRuntime: {(time.perf_counter() - t_start) / 60:.1f} min")
    note(f"-> {RESULTS / 'estimates_zodiac_variants.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
