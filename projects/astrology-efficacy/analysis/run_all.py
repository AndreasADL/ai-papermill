"""
run_all.py — Single entry point. A fresh run reproduces every number in the paper.

    python analysis/run_all.py            # full pipeline
    python analysis/run_all.py --skip-download
    python analysis/run_all.py --only 05_study1_rdd.py

Stages are ordered by dependency. Download stages are slow (Wikidata ~20 min,
BTS ~3 h at the polite request rate) and are cached: each re-run reuses
data/raw/ and data/processed/bts_monthly_cache/ and refetches only what is missing.

Every stochastic step is seeded from inference.SEED (20260918), fixed in plan.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parent
PROJ = ANALYSIS.parent

# (script, description, is_download)
STAGES = [
    ("00_verify_sources.py", "Verify every source is reachable and has the "
                             "claimed fields", True),
    ("02_extract_wikidata.py", "Wikidata people + occupations via QLever", True),
    ("02b_extract_bts.py", "BTS monthly on-time files -> daily series", True),
    ("03_clean.py", "Build the Study 1 analysis frame (ephemeris join)", False),
    ("04_extract_gss.py", "Extract Study 3 variables from the GSS cumulative file",
     False),
    ("05_study1_rdd.py", "Study 1 — zodiac-cusp RDD", False),
    ("06_study2_its.py", "Study 2 — Mercury retrograde ITS", False),
    ("07_study3_gss.py", "Study 3 — GSS sign x belief", False),
    ("08_diagnostics.py", "Running-variable diagnostics and artifact checks", False),
    ("11_zodiac_variants.py", "EXPLORATORY: tropical vs sidereal vs IAU zodiacs",
     False),
    ("09_synthesis.py", "Multiplicity correction, figures, results.md", False),
    ("10_verify_citations.py", "Resolve every reference against Crossref/DataCite",
     True),
    ("12_build_paper.py", "Render the manuscript to .docx and .pdf", False),
]

# 01_ephemeris.py is a library imported by 03/06, not a stage. Run its self-test with
#   python analysis/01_ephemeris.py --validate


def run(script: str, desc: str) -> float:
    print(f"\n{'=' * 78}\n>>> {script} — {desc}\n{'=' * 78}", flush=True)
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, str(ANALYSIS / script)], cwd=str(PROJ))
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        raise SystemExit(f"\nFAILED: {script} (exit {r.returncode}) after {dt:.0f}s")
    print(f"<<< {script} ok ({dt / 60:.1f} min)", flush=True)
    return dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true",
                    help="skip the three network stages (use cached data/raw)")
    ap.add_argument("--only", nargs="+", metavar="SCRIPT",
                    help="run only these stage scripts, in the given order")
    args = ap.parse_args()

    stages = STAGES
    if args.only:
        by_name = {s[0]: s for s in STAGES}
        missing = [s for s in args.only if s not in by_name]
        if missing:
            raise SystemExit(f"unknown stage(s): {missing}")
        stages = [by_name[s] for s in args.only]
    elif args.skip_download:
        stages = [s for s in STAGES if not s[2]]

    print(f"Pipeline: {len(stages)} stage(s)")
    total = 0.0
    for script, desc, _ in stages:
        total += run(script, desc)

    print(f"\n{'=' * 78}\nAll stages completed in {total / 60:.1f} min.")
    print(f"Results: {PROJ / 'results' / 'results.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
