# Data provenance

All access dates 2026-09-18 to 2026-09-20. Retrieval is reproduced by
`analysis/00_verify_sources.py`; the full pipeline by `analysis/run_all.py`.

## Derived files (written by the pipeline, never edited by hand)

| File | Written by | Contents |
|---|---|---|
| `data/raw/wikidata/people.parquet` | `02_extract_wikidata.py` | one row per person: qid, dob, gender, sitelinks |
| `data/raw/wikidata/occupations.parquet` | `02_extract_wikidata.py` | long person × occupation table |
| `data/raw/wikidata/occupation_labels.parquet` | `02_extract_wikidata.py` | English label per occupation QID |
| `data/processed/study1.parquet` | `03_clean.py` | Study 1 analysis frame, 4,407,456 × 35 |
| `data/processed/gss.parquet` | `04_extract_gss.py` | Study 3 variables, recoded |
| `data/processed/bts_monthly_cache/*.parquet` | `02b_extract_bts.py` | per-month daily aggregates (resume cache) |
| `data/processed/bts_daily.parquet` | `02b_extract_bts.py` | one row per calendar day |
| `data/processed/study2_daily.parquet` | `06_study2_its.py` | daily series + retrograde/shadow indicators |
| `data/processed/ingresses_{body}.parquet` | `08_diagnostics.py` | cached ephemeris ingress times |

Raw inputs under `data/raw/` are never modified after download, with one documented
exception: BTS monthly zips are streamed, reduced and discarded rather than retained
(~9.4 GB against 27 GB free). Each is recorded in `data/raw/bts/manifest.csv` with its
source URL, SHA-256, byte size and row count, so every file remains re-obtainable and
hash-verifiable from a stable public URL. `--keep-zips` retains them.

---

## 1. Wikidata — Study 1 (running variable + outcomes)

- **Source:** Wikidata, queried via the **QLever** public SPARQL endpoint,
  `https://qlever.cs.uni-freiburg.de/api/wikidata`
- **Why not WDQS:** `query.wikidata.org` times out (>60 s) on the reified birth-date precision join
  (`p:P569 → psv:P569 → wikibase:timePrecision`) even at one-month scale. QLever indexes the same
  Wikidata dump and answers the identical query in ~1 s. Verified directly, not assumed.
- **Properties used:** `P31` (instance of → `Q5` human), `P569` (date of birth, restricted to
  `wikibase:timePrecision = 11`, i.e. day precision), `P106` (occupation), sitelink count
  (notability proxy), `P27` (citizenship), `P21` (sex or gender).
- **Measured coverage:** 5,046,592 humans with day-precision DOB; 7,140,199 person–occupation
  statement pairs.
- **License:** CC0 1.0 (Wikidata data is public domain).
- **Transformations:** extraction in `02_extract_wikidata.py` (QLever, 10-year chunks);
  cleaning, ephemeris join and occupation coding in `03_clean.py`. Occupation classes are
  built by word-boundary keyword match against the English P106 label
  (`hypotheses.py: build_occupation_classes`), audited in
  `results/occupation_mapping_audit.csv`.
- **Known gap:** citizenship (`P27`) is named in the script docstring but is NOT pulled
  by the SPARQL query, so the pre-registered citizenship-region balance check
  (plan §3) could not be run. Gender, birth year and notability balance were.

## 2. Laouenan et al. (2022) cross-verified notable people — demoted to reference

- **Citation of record:** Laouenan, M., Bhargava, P., Eyméoud, J.-B., Gergaud, O., Plique, G. &
  Wasmer, E. (2022). A cross-verified database of notable people, 3500BC–2018AD. *Scientific Data*,
  9, 290. https://doi.org/10.1038/s41597-022-01369-4
- **Dataset of record:** Sciences Po Dataverse, `doi:10.21410/7E4/RDAG3O`
- **Actually retrieved from:** the CC-BY-SA-4.0 Hugging Face mirror
  `jstet/laouenan-notable-people`, file `cross-verified-database.csv.gz`.
  - **Reason:** `data.sciencespo.fr` (like nature.com, PMC and hal.science) serves an Anubis
    anti-bot challenge to automated clients. No attempt was made to defeat it.
  - **Integrity check:** retrieved file is **249.4 MB**, byte-size-matching the size reported for the
    Dataverse original. SHA-256
    `FE44AA6F97CF9F6C12D040137F92A9F4D0FD1F50E28F7F5D80EEAE29B487828D`.
- **License:** CC-BY-SA 4.0. Citation requirement is to the *Scientific Data* paper, not the
  dataset record.
- **Verified schema fact (this is why it was demoted):** `birth`, `birth_min`, `birth_max` are all
  **year-valued floats** (e.g. 1932.0). No month or day field exists in the 49-column schema.
  The file therefore cannot supply an RDD running variable. Retained only as an occupation-taxonomy
  reference (`level1_main_occ` ∈ {Culture, Discovery/Science, Leadership, Sports/Games, Other}) and
  for birth-year-level descriptive cross-checks.
- **Encoding note:** the published CSV is not valid UTF-8; read with `encoding_errors="replace"`.

## 3. GSS — Study 3

- **Source:** NORC, GSS 1972–2024 Cross-Sectional Cumulative Data, Release 3a.
  `https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip`
- **File:** `gss7224_r3a.dta` (570.2 MB extracted; 45.4 MB zipped), 75,699 rows.
- **License / terms:** free public use, no registration.
- **Measured variable coverage:**
  - `zodiac` — valid N 64,451; years 1976–2022 (absent 1972–75, 1979, 1981, 1992, 1995, 1997, 1999,
    2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2020).
  - `astrolgy` — valid N 8,845; years 2006, 2008, 2010, 2012, 2014, 2016, 2018.
  - `astrosci` — valid N 8,553; **years 2006–2018 (all seven waves)**, correcting the Phase-1
    scouting estimate of 2014/2018 only.
  - Joint: `zodiac × astrolgy` N = **8,531**; `zodiac × astrosci` N = **8,263**.
- **Note:** `zodiac` is recoded by NORC from date of birth; no public birth month/day variable
  exists in the cumulative file. GSS therefore cannot support cusp-level analysis.
- **Transformations:** `04_extract_gss.py` reads the 19 pre-specified columns, maps
  `zodiac` 1-12 to sign names, reverses the four sociability items (raw 1 = almost daily
  .. 7 = never) so that higher = more sociable, z-scores each within survey year,
  averages them, and rescales to SD = 1 so coefficients are in Cohen's *d* units.
  `happy` and `life` are likewise reversed. Weight is `wtssps`; SEs cluster on `vpsu`
  within `vstrat`.
- **Realized analysis N:** `zodiac` × sociability 39,125; × `astrolgy` 5,971;
  × `astrosci` 5,791. The moderation N is below the 8,531 joint N reported above because
  the sociability items sit on a different ballot rotation — logged as a deviation in
  `results/results.md`.

## 4. BTS On-Time Performance — Study 2

- **Source:** US DOT Bureau of Transportation Statistics, TranStats "Reporting Carrier On-Time
  Performance (1987–present)", direct PREZIP path:
  `https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_<YYYY>_<M>.zip`
- **Verified:** 2023-01 file downloads without the ASP form (25.8 MB), inner CSV
  `On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2023_1.csv`, 110 columns.
  Required fields all present: `FlightDate`, `ArrDelay`, `ArrDelayMinutes`, `DepDelay`, `Cancelled`,
  `CancellationCode`, `Diverted`, `Reporting_Airline`.
- **License:** US federal government work, public domain.
- **Actual span:** 2000-01 through 2024-12 (300 monthly files). PREZIP returns 404 for
  1995-1999 — probed directly, not assumed — so the planned 1995 start is not available
  from this endpoint.
- **Transformations:** `02b_extract_bts.py` reduces each month to four columns, marks a
  flight delayed at ArrDelayMinutes >= 15 (the BTS standard) among flights that actually
  operated (not cancelled, not diverted), and aggregates to one row per calendar day.
- **Rate limiting:** 2 s between requests with exponential backoff; an unthrottled first
  attempt was dropped by the server after ~60 requests.

## 5. Ephemeris — Studies 1 and 2

- **Source:** JPL Development Ephemeris **DE440s**, via `skyfield` (`de440s.bsp`, downloaded from
  NAIF/JPL on first run into `data/raw/ephemeris/`).
- **Coverage:** 1849–2150. This is the binding constraint on Study 1's sample, which is restricted
  to births 1850–2020.
- **License:** public domain (NASA/JPL).
- **Validation (see `analysis/01_ephemeris.py --validate`, all passing):**
  - Eight cardinal ingresses (2020, 2024 equinoxes/solstices) vs published USNO times: max
    deviation **0.57 minutes**.
  - Exactly 12 solar ingresses per year across 1991–1999.
  - 2024 Mercury retrograde windows computed as 01 Apr–25 Apr, 05 Aug–28 Aug, 26 Nov–15 Dec,
    matching published dates.
  - 381 retrograde periods over 1900–2020 = 3.15/yr against the canonical ~3.2/yr.
- **Note:** computed values are the study's data; USNO/published values are used only as
  ground-truth spot-checks, not as inputs.
