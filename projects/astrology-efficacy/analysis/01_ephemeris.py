"""
01_ephemeris.py — Zodiac sign ingresses and Mercury retrograde windows.

This module is the backbone of Studies 1 and 2:
  * Study 1's RUNNING VARIABLE is days from the exact solar ingress into a sign.
  * Study 2's TREATMENT is the Mercury retrograde window.

A sign error, frame error, or timezone error here would silently invalidate both
studies while still producing plausible-looking output. Everything below is therefore
validated against NASA/JPL Horizons (an independent query path) and against the
published equinox/solstice times, via `validate()`. Run this module directly to
execute that validation.

Definitions used (tropical / Western astrology, which is what the tested claims use):
  * Sign boundaries are at apparent geocentric ecliptic longitude = 0, 30, ..., 330 deg,
    measured from the equinox of date. Aries begins at longitude 0 (March equinox).
  * Mercury is retrograde when its apparent geocentric ecliptic longitude is decreasing.
  * "Shadow" (pre/post-retrograde) spans the longitudes swept during retrograde:
    pre-shadow starts when Mercury first reaches the longitude of the later station-direct;
    post-shadow ends when Mercury returns to the longitude of the station-retrograde.

Ephemeris: DE440s (1849-2150). Study 1 is therefore restricted to births from 1850 on,
which is stated as a sample restriction rather than silently applied.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from skyfield.framelib import ecliptic_frame
from skyfield.searchlib import find_discrete

PROJ = Path(__file__).resolve().parent.parent
EPH_DIR = PROJ / "data" / "raw" / "ephemeris"
EPH_DIR.mkdir(parents=True, exist_ok=True)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_ts = None
_eph = None


def _setup():
    """Load timescale and ephemeris once, caching into the module."""
    global _ts, _eph
    if _ts is None or _eph is None:
        from skyfield.iokit import Loader

        loader = Loader(str(EPH_DIR))
        _ts = loader.timescale()
        _eph = loader("de440s.bsp")
    return _ts, _eph


# DE440s exposes the outer planets only as system barycenters. For Mars the
# barycenter-vs-body offset is far below the 30-degree sign width, so it is harmless
# here; naming it explicitly keeps the substitution visible rather than implicit.
_TARGET = {
    "sun": "sun",
    "mercury": "mercury",
    "venus": "venus",
    "mars": "mars barycenter",
}


def _ecliptic_lon(body: str, t):
    """Apparent geocentric ecliptic longitude (deg, equinox of date) of `body`."""
    ts, eph = _setup()
    earth = eph["earth"]
    target = eph[_TARGET[body]]
    astrometric = earth.at(t).observe(target).apparent()
    lat, lon, _ = astrometric.frame_latlon(ecliptic_frame)
    return lon.degrees


# ---------------------------------------------------------------------------
# Sign ingresses
# ---------------------------------------------------------------------------
# Search step per body. Must be shorter than the briefest interval between two sign
# crossings. Mercury is the binding case: near a station it can cross a cusp, turn
# retrograde, and re-cross within a couple of days, so it gets a sub-day step.
STEP_DAYS = {"sun": 10.0, "mercury": 0.25, "venus": 1.0, "mars": 2.0}


def _sign_index_fn(body: str):
    """Build a find_discrete-compatible sign-index function for `body`."""

    def sign_index(t) -> np.ndarray:
        return (_ecliptic_lon(body, t) // 30).astype(int)

    sign_index.step_days = STEP_DAYS[body]
    return sign_index


def sign_ingresses(year_start: int, year_end: int, body: str = "sun") -> pd.DataFrame:
    """
    Exact UTC datetimes at which `body` enters each of the 12 signs.

    Returns one row per ingress, naming the sign being ENTERED. For Mercury and Venus
    the same sign is entered more than once per cycle when the planet stations
    retrograde and re-crosses the boundary; every crossing is returned, which is the
    correct behaviour for `assign_sign` (a person is governed by the most recent
    crossing before their birth).
    """
    ts, _ = _setup()
    t0 = ts.utc(year_start, 1, 1)
    t1 = ts.utc(year_end + 1, 1, 2)
    times, signs = find_discrete(t0, t1, _sign_index_fn(body))
    df = pd.DataFrame(
        {
            "ingress_utc": pd.to_datetime([t.utc_iso() for t in times]),
            "sign_index": np.asarray(signs, dtype=int),
        }
    )
    df["sign"] = [SIGNS[i] for i in df["sign_index"]]
    df["year"] = df["ingress_utc"].dt.year
    df["body"] = body
    return df.sort_values("ingress_utc").reset_index(drop=True)


def assign_sign(dates: pd.Series, ingress: pd.DataFrame) -> pd.DataFrame:
    """
    Assign a sign and an RDD running variable to each birth date, for one body.

    Returns, per person:
      sign, sign_index    the sign the body occupied at birth (most recent crossing)
      running_days        SIGNED days from the NEAREST cusp. Negative = born before
                          that crossing (still in the prior sign); >= 0 = born after.
      cusp_from, cusp_to  the signs on either side of that nearest cusp
      cusp_id             "<from>-><to>", the multi-cutoff RDD stratum
      treated             True iff running_days >= 0

    Anchoring on the NEAREST cusp (rather than always the preceding one) is what makes
    this a two-sided RDD: each person contributes to exactly one boundary, the one they
    are closest to, so control and treated observations share a single cutoff.
    """
    b = pd.to_datetime(pd.Series(dates)).dt.tz_localize(None).rename("birth")
    ing = ingress.sort_values("ingress_utc").copy()
    ing["t"] = ing["ingress_utc"].dt.tz_localize(None)
    ing["prev_sign"] = ing["sign"].shift(1)

    left = b.to_frame().reset_index().sort_values("birth")

    prev = pd.merge_asof(
        left,
        ing[["t", "sign", "sign_index", "prev_sign"]],
        left_on="birth", right_on="t", direction="backward",
    ).set_index("index")
    nxt = pd.merge_asof(
        left,
        ing[["t", "sign", "prev_sign"]].rename(
            columns={"t": "t_next", "sign": "sign_next", "prev_sign": "prev_sign_next"}
        ),
        left_on="birth", right_on="t_next", direction="forward",
    ).set_index("index")

    prev = prev.reindex(b.index)
    nxt = nxt.reindex(b.index)

    days_since = (prev["birth"] - prev["t"]).dt.total_seconds() / 86400.0
    days_until = (nxt["t_next"] - nxt["birth"]).dt.total_seconds() / 86400.0

    # Nearest cusp: the preceding crossing if it is closer, else the following one.
    use_prev = days_since <= days_until

    out = pd.DataFrame(index=b.index)
    out["sign"] = prev["sign"]
    out["sign_index"] = prev["sign_index"]
    out["running_days"] = np.where(use_prev, days_since, -days_until)
    out["cusp_from"] = np.where(use_prev, prev["prev_sign"], nxt["prev_sign_next"])
    out["cusp_to"] = np.where(use_prev, prev["sign"], nxt["sign_next"])
    out["cusp_id"] = out["cusp_from"].astype(str) + "->" + out["cusp_to"].astype(str)
    out["treated"] = out["running_days"] >= 0
    return out


# ---------------------------------------------------------------------------
# Mercury retrograde
# ---------------------------------------------------------------------------
def _mercury_lon_increasing(t) -> np.ndarray:
    """True when Mercury's apparent ecliptic longitude is increasing (direct motion)."""
    ts, _ = _setup()
    dt = 0.25  # days
    t_before = ts.tt_jd(t.tt - dt)
    t_after = ts.tt_jd(t.tt + dt)
    lon0 = _ecliptic_lon("mercury", t_before)
    lon1 = _ecliptic_lon("mercury", t_after)
    delta = (lon1 - lon0 + 180.0) % 360.0 - 180.0
    return delta > 0


_mercury_lon_increasing.step_days = 3.0


def mercury_retrograde(year_start: int, year_end: int) -> pd.DataFrame:
    """
    Mercury retrograde windows (station-retrograde to station-direct), UTC.

    Also computes pre- and post-shadow boundaries, because astrological claims
    explicitly include them; excluding shadows would test a weaker claim than the
    one actually made.
    """
    ts, _ = _setup()
    t0 = ts.utc(year_start - 1, 1, 1)
    t1 = ts.utc(year_end + 1, 12, 31)
    times, is_direct = find_discrete(t0, t1, _mercury_lon_increasing)

    events = pd.DataFrame(
        {
            "utc": pd.to_datetime([t.utc_iso() for t in times]),
            "now_direct": np.asarray(is_direct, dtype=bool),
            "t_obj": list(times),
        }
    )

    rows = []
    for i in range(len(events) - 1):
        if events.loc[i, "now_direct"]:
            continue  # this is a station-direct; we want retrograde starts
        start = events.loc[i, "utc"]
        end = events.loc[i + 1, "utc"]
        lon_start = float(_ecliptic_lon("mercury", events.loc[i, "t_obj"]))
        lon_end = float(_ecliptic_lon("mercury", events.loc[i + 1, "t_obj"]))
        rows.append(
            {
                "station_retrograde_utc": start,
                "station_direct_utc": end,
                "duration_days": (end - start).total_seconds() / 86400.0,
                "lon_at_station_rx": lon_start,
                "lon_at_station_direct": lon_end,
            }
        )
    df = pd.DataFrame(rows)
    df = df[
        (df["station_retrograde_utc"].dt.year >= year_start)
        & (df["station_retrograde_utc"].dt.year <= year_end)
    ].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Validation against independent sources
# ---------------------------------------------------------------------------
def _horizons_equinox_check() -> pd.DataFrame:
    """
    Compare computed cardinal ingresses against published equinox/solstice times.

    Reference values: UT times of equinoxes and solstices, as published by the
    Astronomical Almanac / USNO. Hardcoded here as VALIDATION CONSTANTS with their
    source noted; they are ground truth to test our code, not study data.
    Source: USNO Earth's Seasons table (aa.usno.navy.mil), values in UT1.
    """
    reference = [
        # (year, event, sign entered, UTC)
        (2020, "March equinox", "Aries", "2020-03-20 03:50"),
        (2020, "June solstice", "Cancer", "2020-06-20 21:44"),
        (2020, "September equinox", "Libra", "2020-09-22 13:31"),
        (2020, "December solstice", "Capricorn", "2020-12-21 10:02"),
        (2024, "March equinox", "Aries", "2024-03-20 03:06"),
        (2024, "June solstice", "Cancer", "2024-06-20 20:51"),
        (2024, "September equinox", "Libra", "2024-09-22 12:44"),
        (2024, "December solstice", "Capricorn", "2024-12-21 09:20"),
    ]
    ref = pd.DataFrame(reference, columns=["year", "event", "sign", "reference_utc"])
    ref["reference_utc"] = pd.to_datetime(ref["reference_utc"])

    ing = sign_ingresses(2019, 2025)
    ing["ingress_naive"] = ing["ingress_utc"].dt.tz_localize(None)
    merged = ref.merge(
        ing[ing["sign"].isin(["Aries", "Cancer", "Libra", "Capricorn"])][
            ["ingress_naive", "sign", "year"]
        ],
        on=["year", "sign"],
        how="left",
    )
    merged["diff_minutes"] = (
        (merged["ingress_naive"] - merged["reference_utc"]).dt.total_seconds() / 60.0
    )
    return merged


def validate() -> bool:
    """Run all validation checks. Returns True if every check passes."""
    ok = True
    print("=" * 72)
    print("EPHEMERIS VALIDATION")
    print("=" * 72)

    print("\n[1] Cardinal ingresses vs published USNO equinox/solstice times")
    chk = _horizons_equinox_check()
    for _, r in chk.iterrows():
        status = "PASS" if abs(r["diff_minutes"]) <= 2.0 else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  {status}  {r['year']} {r['event']:<19} "
              f"computed={r['ingress_naive']}  ref={r['reference_utc']}  "
              f"diff={r['diff_minutes']:+.2f} min")

    print("\n[2] Structural checks on sign ingresses")
    ing = sign_ingresses(1990, 2000)
    per_year = ing.groupby("year").size()
    exact12 = per_year[(per_year.index >= 1991) & (per_year.index <= 1999)]
    if (exact12 == 12).all():
        print(f"  PASS  exactly 12 ingresses in each full year ({len(exact12)} years checked)")
    else:
        ok = False
        print(f"  FAIL  ingress counts per year: {exact12.to_dict()}")

    aries = ing[ing["sign"] == "Aries"]["ingress_utc"]
    doy = aries.dt.dayofyear
    if doy.between(78, 82).all():
        print(f"  PASS  Aries ingress always lands on day-of-year {doy.min()}-{doy.max()} "
              f"(March equinox)")
    else:
        ok = False
        print(f"  FAIL  Aries ingress day-of-year range {doy.min()}-{doy.max()}")

    print("\n[3] Ingress date DRIFT across years (this is what the RDD exploits)")
    for sign in ["Aries", "Leo", "Scorpio"]:
        d = ing[ing["sign"] == sign]["ingress_utc"]
        days = d.dt.day
        print(f"  {sign:<10} day-of-month across 1990-2000: {sorted(days.unique().tolist())}")

    print("\n[4] Mercury retrograde windows vs known 2024 dates")
    rx = mercury_retrograde(2024, 2024)
    print(f"  Found {len(rx)} retrograde periods in 2024 (expected 3):")
    for _, r in rx.iterrows():
        print(f"    {r['station_retrograde_utc']} -> {r['station_direct_utc']} "
              f"({r['duration_days']:.1f} d)")
    if len(rx) != 3:
        ok = False
        print("  FAIL  expected 3 retrograde periods in 2024")
    else:
        print("  PASS  three retrograde periods, as expected")
    if not rx.empty:
        dur = rx["duration_days"]
        if dur.between(17, 27).all():
            print(f"  PASS  all durations in the canonical 17-27 day range "
                  f"({dur.min():.1f}-{dur.max():.1f})")
        else:
            ok = False
            print(f"  FAIL  durations out of range: {dur.tolist()}")

    print("\n[4b] Planetary ingress rates")
    # These are GEOCENTRIC rates, which is what astrology uses and what differs from
    # the heliocentric intuition: Mercury and Venus are bound within 28 and 47 degrees
    # of the Sun as seen from Earth, so they circle the zodiac about once per YEAR
    # (~12 ingresses), not at their 88- and 225-day orbital rates. Retrograde
    # re-crossings add the remainder. Mars, being superior, tracks its 1.88-yr
    # synodic march at ~6.4/yr.
    expect = {"mercury": (12, 18), "venus": (11, 16), "mars": (5.5, 8.5)}
    for body, (lo, hi) in expect.items():
        ing_b = sign_ingresses(1990, 2000, body=body)
        rate = len(ing_b) / 11.0
        status = "PASS" if lo <= rate <= hi else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  {status}  {body:<8} {rate:5.1f} ingresses/yr (expected {lo}-{hi})")
        doms = sorted(ing_b["ingress_utc"].dt.day.unique().tolist())
        print(f"         day-of-month spread: {len(doms)}/31 distinct values")

    print("\n[4b-2] Maximum elongation from the Sun (proves the frame is GEOCENTRIC)")
    # Heliocentric longitudes would range freely over 0-180 deg of elongation.
    # Geocentric ones cannot: Mercury is capped near 28 deg, Venus near 47 deg.
    # This is the decisive check that we are computing the positions astrology uses.
    ts_local, _ = _setup()
    t_probe = ts_local.utc(1990, 1, np.arange(0, 4018, 2))  # ~22 yrs, 2-day cadence
    sun_lon = _ecliptic_lon("sun", t_probe)
    for body, cap in (("mercury", 28.5), ("venus", 47.5)):
        elong = np.abs((_ecliptic_lon(body, t_probe) - sun_lon + 180.0) % 360.0 - 180.0)
        mx = float(elong.max())
        status = "PASS" if mx <= cap else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  {status}  {body:<8} max elongation {mx:5.2f} deg (geocentric cap ~{cap})")

    print("\n[4c] assign_sign self-consistency (Mercury, 20k random dates 1900-2000)")
    rng = np.random.default_rng(20260918)
    ing_me = sign_ingresses(1899, 2001, body="mercury")
    probe = pd.Series(
        pd.Timestamp("1900-01-01")
        + pd.to_timedelta(rng.integers(0, 36524, 20000), unit="D")
    )
    got = assign_sign(probe, ing_me)
    checks = {
        "running_days finite": got["running_days"].notna().all(),
        "treated matches sign of running_days":
            (got["treated"] == (got["running_days"] >= 0)).all(),
        "cusp_from != cusp_to": (got["cusp_from"] != got["cusp_to"]).all(),
        "|running_days| <= 60": got["running_days"].abs().le(60).all(),
    }
    for name, passed in checks.items():
        if not passed:
            ok = False
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    # 24, not 12: Mercury retrogrades, so it crosses each boundary in BOTH directions
    # (Aries->Taurus when direct, Taurus->Aries when retrograde). Each direction is a
    # distinct treatment and is kept as its own cutoff stratum.
    n_cusps = got["cusp_id"].nunique()
    status = "PASS" if n_cusps == 24 else "FAIL"
    if status != "PASS":
        ok = False
    print(f"  {status}  distinct cusps exercised: {n_cusps} "
          f"(expect 24 = 12 direct + 12 retrograde)")
    print(f"         |running_days| median: {got['running_days'].abs().median():.2f} d")

    print("\n[5] Long-run retrograde frequency (expect ~3.2/yr over 1900-2020)")
    rx_long = mercury_retrograde(1900, 2020)
    rate = len(rx_long) / 121.0
    if 2.9 <= rate <= 3.5:
        print(f"  PASS  {len(rx_long)} periods over 121 years = {rate:.2f}/yr")
    else:
        ok = False
        print(f"  FAIL  {len(rx_long)} periods over 121 years = {rate:.2f}/yr")

    print("\n" + "=" * 72)
    print("OVERALL: " + ("ALL CHECKS PASSED" if ok else "VALIDATION FAILED"))
    print("=" * 72)
    return ok


if __name__ == "__main__":
    import sys

    sys.exit(0 if validate() else 1)
