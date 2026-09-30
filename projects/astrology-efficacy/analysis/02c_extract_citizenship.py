"""
02c_extract_citizenship.py — Citizenship (P27) and its continent, for the plan §3
covariate-balance check.

WHY THIS EXISTS SEPARATELY
--------------------------
`02_extract_wikidata.py` claims in its docstring to extract citizenship, but its
SPARQL query never selected it, so the pre-registered balance check on "citizenship
region" (plan §3) could not be run in the first pass. This stage closes that gap
without re-running the expensive ephemeris join in `03_clean.py`: it writes a
person -> region table that `05_study1_rdd.py` joins on `qid` at analysis time.

Region is not taken from a hand-written country list. Each citizenship country is
mapped to its continent via Wikidata `P30`, so the grouping is sourced rather than
asserted. Countries that have since dissolved (Q34266 Russian Empire, Q15180 USSR,
Q41304 Weimar Republic, ...) still carry P30, so historical citizenships resolve too.

Output: data/raw/wikidata/citizenship.parquet  (qid, country_qid, continent_qid,
                                                continent_label)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
extract = __import__("02_extract_wikidata")

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "data" / "raw" / "wikidata"
OUT.mkdir(parents=True, exist_ok=True)

YEAR_START, YEAR_END = extract.YEAR_START, extract.YEAR_END
CHUNK = extract.CHUNK


def fetch_citizenship() -> pd.DataFrame:
    """One row per (person, citizenship country). People may hold several."""
    frames = []
    for y0 in range(YEAR_START, YEAR_END + 1, CHUNK):
        y1 = min(y0 + CHUNK, YEAR_END + 1)
        q = f"""
        SELECT ?person ?country WHERE {{
          ?person wdt:P31 wd:Q5 .
          ?person p:P569 ?st .
          ?st psv:P569 ?tv .
          ?tv wikibase:timePrecision ?prec ;
              wikibase:timeValue ?dob .
          FILTER(?prec = 11)
          FILTER(?dob >= "{y0}-01-01T00:00:00Z"^^xsd:dateTime)
          FILTER(?dob <  "{y1}-01-01T00:00:00Z"^^xsd:dateTime)
          ?person wdt:P27 ?country .
        }}
        """
        frames.append(extract.run_tsv(q, f"citizenship {y0}-{y1 - 1}"))
    df = pd.concat(frames, ignore_index=True)
    df["qid"] = extract.clean_uri(df["?person"])
    df["country_qid"] = extract.clean_uri(df["?country"])
    return df[["qid", "country_qid"]].drop_duplicates().reset_index(drop=True)


def fetch_country_continents() -> pd.DataFrame:
    """Continent (P30) and English label for every country that appears as P27."""
    q = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?country ?continent ?clabel WHERE {
      ?person wdt:P31 wd:Q5 ; wdt:P27 ?country .
      ?country wdt:P30 ?continent .
      ?continent rdfs:label ?clabel .
      FILTER(LANG(?clabel) = "en")
    }
    """
    df = extract.run_tsv(q, "country -> continent")
    df["country_qid"] = extract.clean_uri(df["?country"])
    df["continent_qid"] = extract.clean_uri(df["?continent"])
    df["continent_label"] = (extract.clean_literal(df["?clabel"])
                             .str.replace(r"@en$", "", regex=True))
    return df[["country_qid", "continent_qid", "continent_label"]]


def main() -> int:
    print(f"Extracting citizenship {YEAR_START}-{YEAR_END} via QLever\n")

    print("Citizenship:")
    cit = fetch_citizenship()
    print(f"  -> {len(cit):,} person-country pairs, "
          f"{cit['qid'].nunique():,} people, "
          f"{cit['country_qid'].nunique():,} distinct countries\n")

    print("Country -> continent:")
    cc = fetch_country_continents()
    # A few transcontinental states (Russia, Turkey, Kazakhstan) carry more than one
    # P30. Keep one per country, chosen deterministically so the mapping is stable
    # across runs rather than depending on result ordering.
    cc = (cc.sort_values(["country_qid", "continent_qid"])
            .drop_duplicates("country_qid"))
    print(f"  -> {len(cc):,} countries mapped to a continent\n")

    df = cit.merge(cc, on="country_qid", how="left")
    # One region per person: people with multiple citizenships get the
    # alphabetically-first continent, again for determinism.
    df = (df.sort_values(["qid", "continent_label"])
            .drop_duplicates("qid").reset_index(drop=True))

    out = OUT / "citizenship.parquet"
    df.to_parquet(out, index=False)

    cov = df["continent_label"].notna().mean()
    print("Region distribution:")
    for label, n in df["continent_label"].value_counts().head(10).items():
        print(f"  {label:<20} {n:>9,}  ({100 * n / len(df):5.1f}%)")
    print(f"\n  continent resolved for {100 * cov:.1f}% of people with a citizenship")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
