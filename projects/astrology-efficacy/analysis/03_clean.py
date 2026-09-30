"""
03_clean.py — Build the Study 1 analysis frame.

Joins the Wikidata person and occupation tables to ephemeris-derived sign placements,
producing one row per person with, for each of Mercury/Venus/Mars/Sun:
  sign, running_days (signed distance to the NEAREST cusp), cusp_id, treated

and the Ptolemaic occupation-class indicators that the hypotheses predict.

Also builds the POSITIVE CONTROL variables: birth quarter and athlete status, used to
verify the pipeline can detect the documented relative-age effect. A pipeline that
finds nothing anywhere is broken, not skeptical.

Output: data/processed/study1.parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hypotheses as H  # noqa: E402
from importlib import import_module  # noqa: E402

eph = import_module("01_ephemeris")

PROJ = Path(__file__).resolve().parent.parent
RAW = PROJ / "data" / "raw" / "wikidata"
PROC = PROJ / "data" / "processed"
RESULTS = PROJ / "results"
PROC.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

BODIES = ["mercury", "venus", "mars", "sun"]

# DE440s covers 1849-12-26 onward. Ingresses are searched from 1850 so that every
# birth has a preceding crossing in range for every body -- Mars can occupy one sign
# for ~7 months, so births start two years after the ephemeris does.
YEAR_START, YEAR_END = 1852, 2020
INGRESS_START, INGRESS_END = 1850, 2022

# Athlete occupations, for the relative-age positive control. Drawn from the
# most common sporting P106 values measured in 00_verify_sources.py.
ATHLETE_KEYWORDS = [
    "association football player", "basketball player", "ice hockey player",
    "athletics competitor", "baseball player", "tennis player", "cricketer",
    "rugby union player", "handball player", "volleyball player", "swimmer",
    "cyclist", "boxer", "sprinter", "rower", "skier", "gymnast",
]

flow: list[str] = []


def note(msg: str) -> None:
    print(msg, flush=True)
    flow.append(msg)


def main() -> int:
    note("# Sample construction — Study 1\n")

    people = pd.read_parquet(RAW / "people.parquet")
    note(f"Wikidata people, day-precision DOB, {YEAR_START}-{YEAR_END}: {len(people):,}")

    people["dob"] = pd.to_datetime(people["dob"], utc=True).dt.tz_localize(None)
    people = people[
        people["dob"].dt.year.between(YEAR_START, YEAR_END)
    ].reset_index(drop=True)
    note(f"After restricting to ephemeris coverage (DE440s, 1849-2150): {len(people):,}")

    # ---- occupation classes -------------------------------------------------
    occ = pd.read_parquet(RAW / "occupations.parquet")
    labels = pd.read_parquet(RAW / "occupation_labels.parquet")
    note(f"Person-occupation pairs: {len(occ):,}; labelled occupations: {len(labels):,}")

    label_map = dict(zip(labels["occ_qid"], labels["occ_label"]))
    audit = RESULTS / "occupation_mapping_audit.csv"
    classes = H.build_occupation_classes(label_map, audit_path=audit)
    note(f"Occupation mapping audit written to {audit.name} (inspect by hand)")
    for planet, qids in classes.items():
        examples = sorted(label_map[q] for q in qids)[:6]
        note(f"  {planet:<8} {len(qids):>5} occupation types  e.g. {examples}")

    athlete_qids = {
        q for q, lab in label_map.items()
        if isinstance(lab, str)
        and any(k in lab.lower() for k in ATHLETE_KEYWORDS)
    }
    note(f"  athlete  {len(athlete_qids):>5} occupation types (positive control)")

    occ_by_person = occ.groupby("qid")["occ_qid"].agg(set)
    note(f"People with >=1 occupation: {len(occ_by_person):,}")

    people = people.set_index("qid")
    people["occ_set"] = occ_by_person
    people["has_occ"] = people["occ_set"].notna()
    people["occ_set"] = people["occ_set"].apply(lambda s: s if isinstance(s, set) else set())

    for planet, qids in classes.items():
        people[f"is_{planet}_occ"] = people["occ_set"].apply(
            lambda s, q=qids: len(s & q) > 0
        )
        note(f"  is_{planet}_occ: {people[f'is_{planet}_occ'].sum():,} people "
             f"({100 * people[f'is_{planet}_occ'].mean():.2f}%)")
    people["is_athlete"] = people["occ_set"].apply(lambda s: len(s & athlete_qids) > 0)
    note(f"  is_athlete:    {people['is_athlete'].sum():,} people "
         f"({100 * people['is_athlete'].mean():.2f}%)")

    people = people.drop(columns=["occ_set"]).reset_index()

    # ---- ephemeris: sign + running variable per body ------------------------
    note("\nComputing sign ingresses (this is the expensive step)")
    for body in BODIES:
        ing = eph.sign_ingresses(INGRESS_START, INGRESS_END, body=body)
        note(f"  {body:<8} {len(ing):,} ingresses "
             f"({len(ing) / (YEAR_END - YEAR_START + 5):.1f}/yr)")
        assigned = eph.assign_sign(people["dob"], ing)
        people[f"{body}_sign"] = assigned["sign"].values
        people[f"{body}_running"] = assigned["running_days"].values
        people[f"{body}_cusp"] = assigned["cusp_id"].values
        people[f"{body}_treated"] = assigned["treated"].values

    # ---- pre-registered directional prediction per cusp ---------------------
    note("\nAttaching pre-registered direction per cusp (from hypotheses.py)")
    for planet in ("mercury", "venus", "mars"):
        cusps = people[f"{planet}_cusp"].dropna().unique()
        direction = {}
        for c in cusps:
            if "->" not in str(c):
                continue
            a, b = str(c).split("->")
            direction[c] = H.predicted_direction(planet, a, b)
        people[f"{planet}_pred_dir"] = people[f"{planet}_cusp"].map(direction)
        counts = pd.Series(direction).value_counts().to_dict()
        note(f"  {planet:<8} cusp directions: "
             f"+1:{counts.get(1, 0)}  -1:{counts.get(-1, 0)}  0:{counts.get(0, 0)}")

    # ---- heaping / covariates ----------------------------------------------
    people["birth_year"] = people["dob"].dt.year
    people["day_of_month"] = people["dob"].dt.day
    people["day_of_year"] = people["dob"].dt.dayofyear
    people["birth_quarter"] = people["dob"].dt.quarter
    people["is_heaped_day"] = people["day_of_month"].isin([1, 10, 15])
    people["is_male"] = people["gender"].eq("Q6581097")
    people["log_sitelinks"] = np.log1p(people["sitelinks"])

    note(f"\nHeaped-day records (dom 1/10/15): {people['is_heaped_day'].sum():,} "
         f"({100 * people['is_heaped_day'].mean():.1f}%)")

    out = PROC / "study1.parquet"
    people.to_parquet(out, index=False)
    note(f"\nFinal analysis frame: {len(people):,} rows x {people.shape[1]} cols")
    note(f"-> {out.relative_to(PROJ).as_posix()}")

    (RESULTS / "sample_flow.md").write_text("\n".join(flow), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
