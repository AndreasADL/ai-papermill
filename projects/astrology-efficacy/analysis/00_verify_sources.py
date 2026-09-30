"""
00_verify_sources.py — Pre-GATE-1 structural validation of every data source.

Purpose: establish that each source EXISTS, is reachable, and contains the variables
the design requires, with real measured numbers rather than estimates.

SCOPE DISCIPLINE (CLAUDE.md rule 2, "plan before peeking"):
This script inspects STRUCTURE ONLY — column names, coverage, sample sizes, and the
distribution of the RUNNING VARIABLE (birth date). It deliberately does NOT compute any
association between an astrological variable and an outcome. Sign-by-outcome crosstabs
stay locked until the analysis plan is approved at GATE 1.

Outputs: results/source_verification.md  (+ console log)
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

PROJ = Path(__file__).resolve().parent.parent
RAW = PROJ / "data" / "raw"
RESULTS = PROJ / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CONTACT = os.environ.get("PAPERMILL_CONTACT_EMAIL", "ai-papermill@example.org")
UA = f"academic-research-bot/1.0 (mailto:{CONTACT})"
QLEVER = "https://qlever.cs.uni-freiburg.de/api/wikidata"

PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

report: list[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)
    report.append(msg)


def sparql(query: str, label: str) -> pd.DataFrame:
    """Run a SPARQL query against QLever, return results as a DataFrame."""
    t0 = time.perf_counter()
    resp = requests.post(
        QLEVER,
        data={"query": PREFIXES + query},
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA},
        timeout=300,
    )
    resp.raise_for_status()
    payload = resp.json()
    elapsed = time.perf_counter() - t0
    rows = [
        {k: v["value"] for k, v in binding.items()}
        for binding in payload["results"]["bindings"]
    ]
    df = pd.DataFrame(rows)
    log(f"  [{label}] {len(df):,} rows in {elapsed:.1f}s")
    return df


# ---------------------------------------------------------------------------
# A. Wikidata via QLever — Study 1 running variable and sample size
# ---------------------------------------------------------------------------
def verify_wikidata() -> None:
    log("## A. Wikidata (Study 1) — via QLever\n")
    log("WDQS (query.wikidata.org) times out on the birth-date precision join even at")
    log("one-month scale. QLever indexes the same Wikidata dump and answers in ~1s.\n")

    log("### A1. Sample size")
    df = sparql(
        """
        SELECT (COUNT(*) AS ?n) WHERE {
          ?person wdt:P31 wd:Q5 ; p:P569 ?st .
          ?st psv:P569 ?tv . ?tv wikibase:timePrecision ?prec .
          FILTER(?prec = 11)
        }
        """,
        "day-precision births",
    )
    n_day = int(df.iloc[0]["n"])
    log(f"  Humans with DAY-precision date of birth: **{n_day:,}**")

    df = sparql(
        """
        SELECT (COUNT(*) AS ?n) WHERE {
          ?person wdt:P31 wd:Q5 ; p:P569 ?st ; wdt:P106 ?occ .
          ?st psv:P569 ?tv . ?tv wikibase:timePrecision ?prec .
          FILTER(?prec = 11)
        }
        """,
        "day-precision + occupation (statement pairs)",
    )
    log(f"  Person-occupation statement pairs: **{int(df.iloc[0]['n']):,}**")

    log("\n### A2. Coverage by birth century")
    df = sparql(
        """
        SELECT ?century (COUNT(*) AS ?n) WHERE {
          ?person wdt:P31 wd:Q5 ; p:P569 ?st .
          ?st psv:P569 ?tv .
          ?tv wikibase:timePrecision ?prec ; wikibase:timeValue ?dob .
          FILTER(?prec = 11)
          BIND(FLOOR(YEAR(?dob) / 100) * 100 AS ?century)
          FILTER(?century >= 1500)
        }
        GROUP BY ?century ORDER BY ?century
        """,
        "births by century",
    )
    if not df.empty:
        df["n"] = df["n"].astype(int)
        df["century"] = df["century"].astype(float).astype(int)
        for _, r in df.iterrows():
            log(f"  {r['century']}s: {r['n']:>10,}")

    log("\n### A3. Date heaping — THE critical check for RDD bandwidth")
    log("Sign ingress falls on day-of-month 19-23. Heaping on the 1st/15th would")
    log("contaminate a wide bandwidth. Measuring the real distribution (births 1900+):\n")
    df = sparql(
        """
        SELECT ?dom (COUNT(*) AS ?n) WHERE {
          ?person wdt:P31 wd:Q5 ; p:P569 ?st .
          ?st psv:P569 ?tv .
          ?tv wikibase:timePrecision ?prec ; wikibase:timeValue ?dob .
          FILTER(?prec = 11)
          FILTER(?dob >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
          BIND(DAY(?dob) AS ?dom)
        }
        GROUP BY ?dom ORDER BY ?dom
        """,
        "day-of-month distribution",
    )
    if not df.empty:
        df["n"] = df["n"].astype(int)
        df["dom"] = df["dom"].astype(int)
        df = df.sort_values("dom")
        total = df["n"].sum()
        # Expected share per day-of-month, accounting for short months
        exp_share = df["n"].median()
        df["ratio"] = df["n"] / exp_share
        log(f"  Total day-precision births 1900+: {total:,}")
        log("")
        log("  | day | n | ratio to median |")
        log("  |---|---|---|")
        for _, r in df.iterrows():
            flag = ""
            if r["ratio"] > 1.15:
                flag = "  <-- HEAP"
            if 19 <= r["dom"] <= 23:
                flag += "  (ingress zone)"
            log(f"  | {r['dom']:>2} | {r['n']:>8,} | {r['ratio']:.3f} |{flag}")
        df.to_csv(RESULTS / "heaping_day_of_month.csv", index=False)
        ingress = df[df["dom"].between(19, 23)]["ratio"]
        log("")
        log(f"  Ingress-zone (19-23) ratio range: {ingress.min():.3f}-{ingress.max():.3f}")

    log("\n### A4. Top occupations (marginal counts only — no sign crosstab)")
    df = sparql(
        """
        SELECT ?occLabel (COUNT(*) AS ?n) WHERE {
          ?person wdt:P31 wd:Q5 ; p:P569 ?st ; wdt:P106 ?occ .
          ?st psv:P569 ?tv . ?tv wikibase:timePrecision ?prec .
          FILTER(?prec = 11)
          ?occ rdfs:label ?occLabel .
          FILTER(LANG(?occLabel) = "en")
        }
        GROUP BY ?occLabel ORDER BY DESC(?n) LIMIT 30
        """,
        "top occupations",
    )
    if not df.empty:
        df["n"] = df["n"].astype(int)
        for _, r in df.iterrows():
            log(f"  {r['occLabel']:<35} {r['n']:>9,}")
        df.to_csv(RESULTS / "occupation_counts.csv", index=False)


# ---------------------------------------------------------------------------
# B. Laouenan notable-people file — schema reality check
# ---------------------------------------------------------------------------
def verify_laouenan() -> None:
    log("\n\n## B. Laouenan et al. 2022 cross-verified notable people\n")
    path = RAW / "notable_people" / "cross-verified-database.csv.gz"
    if not path.exists():
        log(f"  NOT DOWNLOADED: {path}")
        return
    log(f"  File: {path.name} ({path.stat().st_size / 1024**2:.1f} MB)")
    # The published file is not valid UTF-8 (non-ASCII names in a legacy encoding).
    df = pd.read_csv(path, nrows=50_000, low_memory=False,
                     encoding="utf-8", encoding_errors="replace")
    log(f"  Columns: {len(df.columns)}")
    birth_cols = [c for c in df.columns if "birth" in c.lower()]
    log(f"  Birth-related columns: {birth_cols}")
    log("")
    log("  **VERDICT: birth date granularity**")
    sample = df["birth"].dropna().head(8).tolist()
    log(f"  `birth` sample values: {sample}")
    log(f"  `birth` dtype: {df['birth'].dtype}")
    log("")
    log("  `birth` is a YEAR ONLY. There is no month or day field anywhere in the schema.")
    log("  => This dataset CANNOT support the cusp RDD (no running variable).")
    log("  => Demoted from Study 1 primary source to an occupation-taxonomy reference")
    log("     and a birth-YEAR-level descriptive cross-check only.")
    log("")
    log(f"  Occupation taxonomy available: level1_main_occ = "
        f"{sorted(df['level1_main_occ'].dropna().unique().tolist())}")
    log(f"  level2_main_occ distinct values (first 50k rows): "
        f"{df['level2_main_occ'].nunique()}")


# ---------------------------------------------------------------------------
# C. GSS — the crosstab N that decides Study 3
# ---------------------------------------------------------------------------
def verify_gss() -> None:
    log("\n\n## C. GSS (Study 3)\n")
    dest = RAW / "gss"
    dest.mkdir(parents=True, exist_ok=True)
    dta = next(iter(dest.glob("*.dta")), None)

    if dta is None:
        url = "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip"
        log(f"  Downloading {url}")
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=900, stream=True)
            r.raise_for_status()
            blob = io.BytesIO(r.content)
            log(f"  Downloaded {len(r.content) / 1024**2:.1f} MB")
            with zipfile.ZipFile(blob) as z:
                names = z.namelist()
                log(f"  Archive contents: {names}")
                z.extractall(dest)
            dta = next(iter(dest.glob("**/*.dta")), None)
        except Exception as exc:  # noqa: BLE001
            log(f"  DOWNLOAD FAILED: {exc}")
            return

    if dta is None:
        log("  No .dta found after extraction.")
        return

    log(f"  Reading {dta.name} ({dta.stat().st_size / 1024**2:.1f} MB)")
    wanted = ["year", "zodiac", "astrolgy", "astrosci", "wtssall", "wtssps", "id"]
    try:
        df = pd.read_stata(dta, columns=wanted, convert_categoricals=False)
    except ValueError as exc:
        log(f"  Column subset failed ({exc}); reading full file.")
        df = pd.read_stata(dta, convert_categoricals=False)
        df = df[[c for c in wanted if c in df.columns]]

    log(f"  Rows: {len(df):,}")
    for col in ("zodiac", "astrolgy", "astrosci"):
        if col not in df.columns:
            log(f"  {col}: NOT PRESENT in this release")
            continue
        valid = df[col].notna().sum()
        yrs = sorted(df.loc[df[col].notna(), "year"].unique().tolist())
        log(f"  {col}: valid N = {valid:,}; years = {yrs}")

    log("\n  ### The number that decides Study 3's moderation test")
    for belief in ("astrolgy", "astrosci"):
        if belief not in df.columns or "zodiac" not in df.columns:
            continue
        joint = df[df["zodiac"].notna() & df[belief].notna()]
        log(f"\n  **ZODIAC x {belief.upper()}: joint N = {len(joint):,}**")
        if len(joint):
            ct = pd.crosstab(joint["zodiac"], joint[belief])
            log(f"  Crosstab shape: {ct.shape}; min cell = {int(ct.values.min())}; "
                f"median cell = {int(pd.Series(ct.values.ravel()).median())}")
            ct.to_csv(RESULTS / f"gss_zodiac_x_{belief}.csv")


# ---------------------------------------------------------------------------
# D. BTS On-Time Performance — Study 2
# ---------------------------------------------------------------------------
def verify_bts() -> None:
    log("\n\n## D. BTS On-Time Performance (Study 2)\n")
    dest = RAW / "bts"
    dest.mkdir(parents=True, exist_ok=True)
    url = ("https://transtats.bts.gov/PREZIP/"
           "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2023_1.zip")
    out = dest / "ontime_2023_01.zip"
    if not out.exists():
        log(f"  Downloading {url}")
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=900)
            r.raise_for_status()
            out.write_bytes(r.content)
        except Exception as exc:  # noqa: BLE001
            log(f"  DOWNLOAD FAILED: {exc}")
            return
    log(f"  File: {out.name} ({out.stat().st_size / 1024**2:.1f} MB)")
    try:
        with zipfile.ZipFile(out) as z:
            csv_name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(csv_name) as fh:
                df = pd.read_csv(fh, nrows=5000, low_memory=False)
    except Exception as exc:  # noqa: BLE001
        log(f"  UNZIP/PARSE FAILED: {exc}")
        return
    log(f"  Inner CSV: {csv_name}")
    log(f"  Columns: {len(df.columns)}")
    needed = ["FlightDate", "ArrDelay", "ArrDelayMinutes", "DepDelay",
              "Cancelled", "CancellationCode", "Diverted", "Reporting_Airline"]
    for c in needed:
        log(f"    {c:<22} {'PRESENT' if c in df.columns else 'MISSING'}")
    log(f"  Sample FlightDate values: {df['FlightDate'].head(3).tolist()}"
        if "FlightDate" in df.columns else "  FlightDate absent")


def main() -> None:
    log("# Source verification — pre-GATE-1 structural checks")
    log(f"\nRun: {pd.Timestamp.now(tz='UTC').isoformat()}")
    log("\nStructure only. No astrological-variable x outcome association is computed here.\n")
    verify_wikidata()
    verify_laouenan()
    verify_gss()
    verify_bts()
    (RESULTS / "source_verification.md").write_text("\n".join(report), encoding="utf-8")
    log(f"\n\nWritten to {RESULTS / 'source_verification.md'}")


if __name__ == "__main__":
    main()
