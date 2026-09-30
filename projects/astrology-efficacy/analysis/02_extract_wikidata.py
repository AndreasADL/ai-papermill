"""
02_extract_wikidata.py — Pull the Study 1 person-level sample from Wikidata.

Source: QLever (`qlever.cs.uni-freiburg.de/api/wikidata`). The official WDQS endpoint
times out on the reified birth-date precision join even at one-month scale; QLever
indexes the same dump and answers in ~1s. See data/provenance.md.

Extracted per person (day-precision date of birth only, 1850-2020):
  qid, dob, gender, occupation QIDs, sitelink count (notability)

Citizenship (P27) is NOT extracted here despite earlier versions of this docstring
claiming it -- the query never selected it. It is fetched separately by
02c_extract_citizenship.py, which also resolves each country to a continent for the
plan §3 covariate-balance check.

Occupations are pulled as a separate long table (a person may hold several) and joined
in 03_clean.py. Output is Parquet under data/raw/wikidata/.
"""

from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "data" / "raw" / "wikidata"
OUT.mkdir(parents=True, exist_ok=True)

QLEVER = "https://qlever.cs.uni-freiburg.de/api/wikidata"
CONTACT = os.environ.get("PAPERMILL_CONTACT_EMAIL", "ai-papermill@example.org")
UA = f"academic-research-bot/1.0 (mailto:{CONTACT})"

YEAR_START, YEAR_END = 1850, 2020
CHUNK = 10  # years per request

PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX schema: <http://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def run_tsv(query: str, label: str, retries: int = 3) -> pd.DataFrame:
    """Execute a SPARQL query, returning TSV results as a DataFrame."""
    for attempt in range(1, retries + 1):
        t0 = time.perf_counter()
        try:
            resp = requests.post(
                QLEVER,
                data={"query": PREFIXES + query},
                headers={"Accept": "text/tab-separated-values", "User-Agent": UA},
                timeout=900,
            )
            resp.raise_for_status()
            # QLever returns UTF-8 but does not always declare a charset, and requests
            # then falls back to ISO-8859-1, mojibaking every non-ASCII label
            # ("Chef superieur" -> "Chef supA©rieur"). Force the correct codec.
            resp.encoding = "utf-8"
            df = pd.read_csv(io.StringIO(resp.text), sep="\t", dtype=str)
            print(f"  [{label}] {len(df):>9,} rows  {time.perf_counter() - t0:6.1f}s",
                  flush=True)
            return df
        except Exception as exc:  # noqa: BLE001
            print(f"  [{label}] attempt {attempt}/{retries} failed: {exc}", flush=True)
            if attempt == retries:
                raise
            time.sleep(5 * attempt)
    raise RuntimeError("unreachable")


def clean_uri(s: pd.Series) -> pd.Series:
    """Strip angle brackets and the entity prefix from QLever's URI output."""
    return (s.str.strip("<>")
             .str.rsplit("/", n=1).str[-1])


def clean_literal(s: pd.Series) -> pd.Series:
    """Strip SPARQL literal quoting and datatype suffix."""
    return s.str.replace(r'^"|"\^\^.*$|"$', "", regex=True)


def fetch_people() -> pd.DataFrame:
    """One row per person: qid, dob, gender, sitelinks."""
    frames = []
    for y0 in range(YEAR_START, YEAR_END + 1, CHUNK):
        y1 = min(y0 + CHUNK, YEAR_END + 1)
        q = f"""
        SELECT ?person ?dob ?gender ?sitelinks WHERE {{
          ?person wdt:P31 wd:Q5 .
          ?person p:P569 ?st .
          ?st psv:P569 ?tv .
          ?tv wikibase:timePrecision ?prec ;
              wikibase:timeValue ?dob .
          FILTER(?prec = 11)
          FILTER(?dob >= "{y0}-01-01T00:00:00Z"^^xsd:dateTime)
          FILTER(?dob <  "{y1}-01-01T00:00:00Z"^^xsd:dateTime)
          OPTIONAL {{ ?person wdt:P21 ?gender }}
          OPTIONAL {{ ?person wikibase:sitelinks ?sitelinks }}
        }}
        """
        frames.append(run_tsv(q, f"people {y0}-{y1 - 1}"))
    df = pd.concat(frames, ignore_index=True)

    df["qid"] = clean_uri(df["?person"])
    df["dob"] = pd.to_datetime(clean_literal(df["?dob"]), errors="coerce", utc=True)
    df["gender"] = clean_uri(df["?gender"].fillna(""))
    df["sitelinks"] = pd.to_numeric(clean_literal(df["?sitelinks"].fillna("0")),
                                    errors="coerce").fillna(0).astype(int)
    df = df[["qid", "dob", "gender", "sitelinks"]].dropna(subset=["dob"])
    # A person can carry more than one gender/sitelink row through the OPTIONALs.
    df = df.sort_values("sitelinks", ascending=False).drop_duplicates("qid")
    return df.reset_index(drop=True)


def fetch_occupations() -> pd.DataFrame:
    """Long table: one row per (person, occupation) pair."""
    frames = []
    for y0 in range(YEAR_START, YEAR_END + 1, CHUNK):
        y1 = min(y0 + CHUNK, YEAR_END + 1)
        q = f"""
        SELECT ?person ?occ WHERE {{
          ?person wdt:P31 wd:Q5 .
          ?person p:P569 ?st .
          ?st psv:P569 ?tv .
          ?tv wikibase:timePrecision ?prec ;
              wikibase:timeValue ?dob .
          FILTER(?prec = 11)
          FILTER(?dob >= "{y0}-01-01T00:00:00Z"^^xsd:dateTime)
          FILTER(?dob <  "{y1}-01-01T00:00:00Z"^^xsd:dateTime)
          ?person wdt:P106 ?occ .
        }}
        """
        frames.append(run_tsv(q, f"occ {y0}-{y1 - 1}"))
    df = pd.concat(frames, ignore_index=True)
    df["qid"] = clean_uri(df["?person"])
    df["occ_qid"] = clean_uri(df["?occ"])
    return df[["qid", "occ_qid"]].drop_duplicates().reset_index(drop=True)


def fetch_occupation_labels() -> pd.DataFrame:
    """English labels for every occupation QID, so mappings are human-auditable."""
    q = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?occ ?label WHERE {
      ?person wdt:P31 wd:Q5 ; wdt:P106 ?occ .
      ?occ rdfs:label ?label .
      FILTER(LANG(?label) = "en")
    }
    """
    df = run_tsv(q, "occupation labels")
    df["occ_qid"] = clean_uri(df["?occ"])
    df["occ_label"] = clean_literal(df["?label"]).str.replace(r"@en$", "", regex=True)
    return df[["occ_qid", "occ_label"]].drop_duplicates("occ_qid").reset_index(drop=True)


def main() -> None:
    print(f"Extracting Wikidata {YEAR_START}-{YEAR_END} via QLever\n")

    print("People:")
    people = fetch_people()
    people.to_parquet(OUT / "people.parquet", index=False)
    print(f"  -> {len(people):,} people  ({OUT / 'people.parquet'})\n")

    print("Occupations:")
    occ = fetch_occupations()
    occ.to_parquet(OUT / "occupations.parquet", index=False)
    print(f"  -> {len(occ):,} person-occupation pairs\n")

    print("Occupation labels:")
    try:
        labels = fetch_occupation_labels()
        labels.to_parquet(OUT / "occupation_labels.parquet", index=False)
        print(f"  -> {len(labels):,} labelled occupations\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  label fetch failed ({exc}); 03_clean.py will fetch on demand\n")

    print("Summary")
    print(f"  people:            {len(people):>10,}")
    print(f"  with >=1 occupation:{occ['qid'].nunique():>10,}")
    print(f"  dob range:         {people['dob'].min()} .. {people['dob'].max()}")
    print(f"  median sitelinks:  {people['sitelinks'].median():.0f}")


if __name__ == "__main__":
    sys.exit(main())
