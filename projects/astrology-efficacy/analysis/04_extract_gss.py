"""
04_extract_gss.py — Extract the Study 3 analysis variables from the GSS cumulative file.

Source: NORC, GSS 1972-2024 Cross-Sectional Cumulative Data, Release 3a
(`gss7224_r3a.dta`, 570 MB, 6,943 variables). See data/provenance.md §3.

Reads only the pre-specified columns, applies the documented codings, and writes
data/processed/gss.parquet. The raw .dta is never modified.

Codings verified against the GSS 2024 cumulative codebook:
  zodiac    1=Aries .. 12=Pisces
  astrolgy  1=Yes, 2=No   ("ever read a horoscope or personal astrology report")
  astrosci  1=very scientific, 2=sort of scientific, 3=not at all scientific
  socfrend/socommun/socrel/socbar  1=almost daily .. 7=never  (REVERSED here)
  happy     1=very happy .. 3=not too happy                   (REVERSED here)
  life      1=exciting .. 3=dull                              (REVERSED here)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hypotheses as H  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
RAW = PROJ / "data" / "raw" / "gss" / "GSS_stata" / "gss7224_r3a.dta"
PROC = PROJ / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

COLUMNS = ["year", "id", "zodiac", "astrolgy", "astrosci",
           "socfrend", "socommun", "socrel", "socbar",
           "happy", "life", "wtssps", "wtssall", "vpsu", "vstrat",
           "age", "sex", "educ", "ballot"]

SOC_ITEMS = H.GSS_SOCIABILITY_ITEMS  # frozen at GATE 1


def main() -> int:
    print(f"Reading {RAW.name} ({RAW.stat().st_size / 1024**2:.0f} MB), "
          f"{len(COLUMNS)} of 6,943 columns")
    df = pd.read_stata(RAW, columns=COLUMNS, convert_categoricals=False)
    print(f"  {len(df):,} respondents, {df['year'].min()}-{df['year'].max()}")

    # ---- sign ----------------------------------------------------------
    df["zodiac"] = pd.to_numeric(df["zodiac"], errors="coerce")
    valid = df["zodiac"].between(1, 12)
    df.loc[~valid, "zodiac"] = np.nan
    df["sign"] = df["zodiac"].map(H.GSS_ZODIAC_CODES)
    # Mayo-White-Eysenck: odd-numbered ("positive") signs predict extraversion.
    df["odd_sign"] = df["sign"].isin(H.POSITIVE_SIGNS).where(df["sign"].notna())
    df["water_sign"] = df["sign"].isin(H.WATER_SIGNS).where(df["sign"].notna())
    print(f"  zodiac valid N = {df['zodiac'].notna().sum():,}")

    # ---- belief --------------------------------------------------------
    a = pd.to_numeric(df["astrolgy"], errors="coerce")
    df["reads_horoscope"] = np.where(a == 1, 1.0, np.where(a == 2, 0.0, np.nan))
    s = pd.to_numeric(df["astrosci"], errors="coerce")
    # Reverse so that HIGHER = rates astrology as more scientific (more believing).
    df["astro_scientific"] = np.where(s.between(1, 3), 4.0 - s, np.nan)
    print(f"  astrolgy valid N = {df['reads_horoscope'].notna().sum():,}  "
          f"(reads horoscope: {100 * df['reads_horoscope'].mean():.1f}%)")
    print(f"  astrosci valid N = {df['astro_scientific'].notna().sum():,}")

    # ---- sociability composite (pre-specified at GATE 1) ----------------
    # Items run 1=almost daily .. 7=never, so they are reversed before averaging:
    # higher = more sociable. Each item is z-scored WITHIN YEAR first, because the
    # item set and response distribution shift across waves.
    zs = []
    for item in SOC_ITEMS:
        v = pd.to_numeric(df[item], errors="coerce")
        v = v.where(v.between(1, 7))
        rev = 8.0 - v
        g = rev.groupby(df["year"])
        z = (rev - g.transform("mean")) / g.transform("std")
        df[f"z_{item}"] = z
        zs.append(z)
        print(f"  {item:<9} valid N = {v.notna().sum():,}")
    Z = pd.concat(zs, axis=1)
    df["n_soc_items"] = Z.notna().sum(axis=1)
    df["sociability"] = Z.mean(axis=1, skipna=True).where(df["n_soc_items"] >= 1)
    # Rescale to SD = 1 so the estimate is directly in Cohen's d units, matching the
    # pre-registered SESOI of d = 0.10.
    df["sociability"] = df["sociability"] / df["sociability"].std()
    print(f"  sociability composite valid N = {df['sociability'].notna().sum():,} "
          f"(mean items per respondent: {df.loc[df['sociability'].notna(), 'n_soc_items'].mean():.2f})")

    # ---- secondary outcomes (reversed: higher = happier / more exciting) ----
    h = pd.to_numeric(df["happy"], errors="coerce")
    df["happy_r"] = np.where(h.between(1, 3), 4.0 - h, np.nan)
    li = pd.to_numeric(df["life"], errors="coerce")
    df["life_exciting"] = np.where(li.between(1, 3), 4.0 - li, np.nan)

    # ---- weights and design ---------------------------------------------
    # wtssps is the post-stratified weight covering the whole cumulative file;
    # wtssall is retained for a robustness comparison.
    df["w"] = pd.to_numeric(df["wtssps"], errors="coerce")
    df["w_alt"] = pd.to_numeric(df["wtssall"], errors="coerce")
    df["cluster"] = (df["vstrat"].astype("Int64").astype(str) + "_"
                     + df["vpsu"].astype("Int64").astype(str))

    out = PROC / "gss.parquet"
    df.to_parquet(out, index=False)

    # ---- realized analysis N, the number that actually constrains Study 3 ----
    core = df["zodiac"].notna() & df["sociability"].notna()
    print(f"\n  zodiac x sociability                 N = {int(core.sum()):,}")
    print(f"  zodiac x sociability x astrolgy      N = "
          f"{int((core & df['reads_horoscope'].notna()).sum()):,}")
    print(f"  zodiac x sociability x astrosci      N = "
          f"{int((core & df['astro_scientific'].notna()).sum()):,}")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
