# Data candidates — Astrology efficacy studies (Phase 1 scouting)

Scouted with: real SPARQL calls to `query.wikidata.org/sparql`, real HTTP fetches of GSS/SDA
codebook pages, a real download attempt against BTS TranStats PREZIP, and searches for the
Laouenan et al. repository and ephemeris ground truth. Tooling note: this pass had no shell/Bash
access — all "live" checks were done via `WebFetch` (a GET + AI-summarization proxy, no custom
headers, ~60s client timeout, no raw HTTP timing) and `WebSearch`. Anything that needs a real HTTP
client (custom User-Agent, binary parsing, JS-driven apps, long-running queries) is flagged below
for the main agent's download script rather than guessed at.

---

## A. Wikidata (Study 1 primary source)

**Endpoint:** `https://query.wikidata.org/sparql` (keyless). Confirmed reachable.

### Precision qualifier — CONFIRMED retrievable
This query pattern returns both the full timestamp and the precision code together:
```sparql
SELECT ?person ?dob ?precision WHERE {
  ?person wdt:P31 wd:Q5 .
  ?person p:P569 ?statement .
  ?statement psv:P569 ?tv .
  ?tv wikibase:timePrecision ?precision ;
      wikibase:timeValue ?dob .
  FILTER(?precision = 11)
  FILTER(?dob >= "1950-01-01T00:00:00Z"^^xsd:dateTime)
  FILTER(?dob <  "1950-01-10T00:00:00Z"^^xsd:dateTime)
} LIMIT 10
```
Returned 10 rows with `precision = "11"` and full `YYYY-MM-DDT00:00:00Z` dates. `precision=11` = day,
`9` = year, `10` = month — exactly the qualifier needed to exclude year-only records defaulted to
Jan 1.

### Counting / chunking — this is the real obstacle
- A global, unfiltered `COUNT` of all humans with `psv:P569`+`wikibase:timePrecision=11` **timed out**
  (>60s).
- A **single calendar year**, day-precision-filtered `COUNT` (1950-01-01 to 1951-01-01, via the
  `p:/psv:/wikibase:timePrecision` join) **also timed out**. So did the same for 1800–1899,
  1900–1999, and <1800, and every occupation-breakdown / day-of-month `GROUP BY` query that
  included the precision join.
- What *did* work fast: a cheap `wdt:P569` (truthy statement, no precision) range filter.
  - `COUNT` of humans with `wdt:P569` in Jan 1950 → succeeded, returned **42,973**.
  - `SELECT ?person ?dob` for the same month, `LIMIT 500` → succeeded, 500 rows.
  - A precision-filtered `COUNT` restricted to that *same one month* still **timed out**.

**Conclusion on chunking:** the expensive part is not the date-range filter (that's fast via
`wdt:P569`), it's the join through the reified statement node
(`p:P569 → psv:P569 → wikibase:timePrecision`) at any aggregate scale ≥ ~1 month. Per-year
chunking (as sketched in `idea.md`) is **not sufficient** for a live-SPARQL aggregate/GROUP BY
strategy against WDQS. Two workable alternatives for the actual download script:
1. **Two-step pattern**: (a) pull `?person ?dob` in batches via the cheap `wdt:P569` range filter
   (works, LIMIT/OFFSET-paginated, e.g. per month or per 2,000-row page); (b) for each batch of
   person IDs, look up precision via a `VALUES ?person { wd:Q... wd:Q... }` block (bounded to
   ~200–500 IDs per call) rather than doing the precision join as part of a big aggregate. This
   is the standard WDQS-recommended pattern for "known item list" lookups and avoids the timeout.
2. **Offline dump processing**: download the Wikidata JSON/TTL dump (dumps.wikimedia.org) and
   filter for `P569` + precision + `P106` locally with a script — this avoids WDQS entirely and is
   the approach most large Wikidata-scale research pipelines actually use. Slower to set up, but
   the only approach with sub-hour, non-flaky turnaround for a corpus this size.
3. A rough sense of scale: unfiltered `wdt:P569` in one month = ~43,000 rows. That is **far** too
   high to be real day-precision notable-person births (Wikidata has on the order of 2M humans
   with any P569 at all) — this single number is itself strong indirect evidence that most
   `wdt:P569` values in a given month are year/month-only records defaulted to day 1, i.e. the
   heaping problem is large before filtering, which is exactly why the precision filter is
   mandatory and why it should never be skipped for convenience.

**Occupation breakdown, century breakdown, day-of-month heaping:** none of these could be
retrieved live in this pass — every query that combined a date range with the precision join timed
out. **This is an honest gap, not an estimate I'm willing to fabricate.** The indirect evidence
above (implausibly high unfiltered monthly count) says heaping is a real risk for a ±5–15 day
bandwidth around sign ingress (which falls day 19–23), but I could not quantify the 1st/15th
heap fraction with the tools available in this pass. **This must be measured by the main agent's
actual download script** (via the two-step VALUES-batch pattern or the offline dump) *before*
finalizing the RDD bandwidth in `analysis/plan.md` — treat it as a required pre-analysis check, not
optional robustness.

**Rows/sec:** no reliable number obtainable — `WebFetch` does not expose request latency, and every
query large enough to be informative timed out. The main agent's script should measure this
directly with real timing once it has raw HTTP access.

---

## B. Laouenan et al. 2022 cross-verified notable people database

**Resolvable, working URL found:**
`https://data.sciencespo.fr/dataset.xhtml?persistentId=doi:10.21410/7E4/RDAG3O`
— "A Brief History of Human Time - Cross-verified Dataset" (v2.2), hosted on Sciences Po's own
Dataverse instance (data.sciencespo.fr), contact Guillaume Plique.
- File: `cross-verified-database.csv.gz`, **249.4 MB** (gzip), published 2023-02-02.
- Also `LICENSE.txt` (20.4 KB).
- **License: CC-BY-SA 4.0.** Citation requirement: cite the Scientific Data paper (Laouenan et al.
  2022, *Sci Data* 9:290), not the dataset record directly.
- A companion Dataverse entry "A Brief History of Human Time - Codes & Datasets" holds the
  processing code separately (found via search, not independently opened this pass — confirm URL
  before use rather than trusting the search snippet verbatim).
- A third-party Hugging Face mirror (`jstet/laouenan-notable-people`, CSV, ~262 MB uncompressed)
  corroborates the file exists and is this size — consistent, but **use the Sciences Po Dataverse
  original**, not the HF mirror, as the source of record.

**Confirmed blocked, as reported:** Nature (`nature.com/articles/s41597-022-01369-4`), PMC, and HAL
(`hal.science/hal-03930666...`) all returned **Anubis anti-bot "Access Denied"** pages to automated
fetches in this pass — matches what was already observed. Do not retry these for content.

**Not independently confirmed** (paper text unreachable): the exact occupation/domain coding scheme
and the day-vs-year birth-date precision split. **Do not trust name-only** — a quick websearch
surfaced a plausible-looking DOI (`10.21410/7E4/YLG6YR51`) that **does not resolve (404)**; it was
not used. First step of the actual acquisition script should be to `pd.read_csv` the header +
a sample of rows from the real file above and report the actual column names, occupation field
values, and birth-date field granularity — do not assume a schema from the paper's abstract.

---

## C. GSS (Study 3)

Cumulative file: **GSS 1972–2024 Cross-Sectional Cumulative Data, Release 3a (July 2026)**, Stata
`.dta`, direct link path confirmed via `gss.norc.org/get-the-data/stata.html`:
`https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip`
(exact size not shown on page — confirm at download time). Free, no registration.

### ZODIAC
- Variable `zodiac`, question "ASTROLOGICAL SIGN OF RESPONDENT", coded 1–12 (Aries…Pisces) +
  don't know / inapplicable / no answer.
- **Years asked: 1976–2021, except NOT asked in 1972–1975 or 2000.**
- Cumulative valid N ≈ **61,200** (sum of the 12 category counts read from the codebook: Aries
  4,872; Taurus 4,836; Gemini 5,205; Cancer 5,224; Leo 5,425; Virgo 5,518; Libra 5,401; Scorpio
  4,827; Sagittarius 4,851; Capricorn 4,911; Aquarius 5,004; Pisces 5,113), missing ≈7,500,
  total attempted ≈68,700–68,850 (two AI-summarized reads of the codebook page disagreed on the
  last digits — re-verify the exact total from the real `.dta` file, it's a one-line
  `value_counts()`).
- It is **described as recoded from date of birth**, not a raw self-report of sign — this implies
  an underlying birth-month/day question exists in the interview but I could **not confirm a
  separate public birth-month/day variable** in the cumulative file; it may be interviewer-side
  only and suppressed from the public release for confidentiality. Not a blocker for Study 3
  (which only needs the categorical sign), but flag for the plan: no cusp-level precision is
  available from GSS, so GSS cannot support anything like Study 1's RDD.

### Belief variables
- `astrolgy` — "Do you ever read a horoscope or your personal astrology report?" Yes/No.
  **Years: 2006, 2008, 2010, 2012, 2014, 2016, 2018.** Per-year valid N: 2006=1,862; 2008=1,502;
  2010=689; 2012=996; 2014=1,238; 2016=1,386; 2018=1,172. **Cumulative N = 8,845** (verified by
  summation, matches the codebook's stated total exactly).
- `astrosci` — "Would you say that astrology is very scientific, sort of scientific, or not at all
  scientific?" (1/2/3 + DK/NA). Confirmed present in the **2014 and 2018** GSS SPSS codebooks
  (third-party mirrors of the official codebook). Per-year N could **not be confirmed** this pass
  (the SDA codebook page numbering search did not land on the right page); by analogy with
  `astrolgy`'s N in the same years (1,238 and 1,172) expect `astrosci` to be similar order of
  magnitude, but this is an **estimate, not a verified number** — confirm with `value_counts()`
  once the file is local.

### The critical number: realized ZODIAC × belief crosstab N
**Could not obtain a live, verified crosstab N with the tools available in this pass.** SDA's
online crosstab tool (`sda.berkeley.edu/sdaweb/analysis/...`) is a JavaScript application with no
documented GET-based query API (checked `man41h/tables.htm` — it documents a batch-file/CLI mode
only, not a scriptable URL). This is a real gap, not a shortcut — reported honestly per the rules.

Best defensible estimate, not a substitute for measurement: `zodiac` is asked to nearly the entire
cross-section in every year it appears, while `astrolgy`/`astrosci` are topical-module items
given to only a random ballot subsample within their years. So the realized joint N is capped by,
and should be close to (≥85%), the smaller item's yearly N:
- **ZODIAC × ASTROLGY: bounded by ≤8,845, plausibly ~7,500–8,300 after joint item-nonresponse.**
- **ZODIAC × ASTROSCI: bounded by the 2014+2018 ASTROSCI N, plausibly ~2,000–2,500** (using
  ASTROLGY's same-year Ns of 1,238 + 1,172 = 2,410 as a proxy).

**Action required before GATE 1:** the main agent must compute
`pd.crosstab(df.zodiac, df.astrolgy)` and `pd.crosstab(df.zodiac, df.astrosci)` directly on the
downloaded `.dta` (trivial, one line each) and report the real N before the moderation test in
`analysis/plan.md` is finalized. With 12 sign categories × 2–3 belief categories, ~7,500–8,300
(ASTROLGY) is plausibly powered for a moderation/interaction test; ~2,000–2,500 (ASTROSCI) is
thin and may need pooling astrology-belief across ASTROLGY (larger N, binary) as primary and
treating ASTROSCI as a secondary/exploratory check.

### Candidate outcome variables (trait claims)
Verified as real, standard GSS items (not all individually re-confirmed with N/years this pass —
flagged where so):
- `happy` — general happiness (very/pretty/not too happy). **Verified** wording this pass; near-
  universal core item across almost all years.
- `life` — "is life exciting or dull" (exciting/routine/dull). **Verified** wording this pass; core
  item, most years.
- `marital` — marital status. Standard GSS core item, present essentially every year (high
  confidence from domain knowledge; not re-fetched this pass — confirm on load).
- `prestg10` (and `prestg105plus`) — respondent occupational prestige score (2010 Census basis).
  Standard GSS core item; not re-fetched this pass — confirm on load.
- Sociability: `socrel`, `socommun`, `socfrend`, `socbar` — frequency of socializing with
  relatives/neighbors/friends/at a bar. Standard GSS items; not re-fetched this pass.
- No dedicated general "risk attitude" battery was located in this pass; would need a targeted
  codebook search (e.g. `GAMBLE`/finance-risk items in select modules) before committing to it as
  an outcome — treat as tentative, not confirmed.

---

## D. BTS On-Time Performance (Study 2)

**Direct download attempted and it worked.** URL pattern
`https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2023_1.zip`
returned a binary response **larger than 10 MB** (WebFetch's own content cap, "maxContentLength …
exceeded" — not a 404, not an error page; the server served real, large binary content). This is
strong evidence the PREZIP direct-file path works without needing the ASP form.

Caveats / what still needs confirming with a real HTTP client (this pass had no binary download or
header-inspection capability):
- Exact byte size and whether the filename needs parentheses as shown on the BTS site
  (`..._Performance_(1987_present)_2023_1.zip`) — I used the underscore-only form and it worked,
  but I could not confirm this is the *canonical* form vs. a lenient/redirecting server; the main
  agent's script should try the exact string from the download page first.
- Column list (`FL_DATE`, scheduled/actual dep/arr times, `ARR_DELAY`, `CANCELLED`,
  `CANCELLATION_CODE`, etc.) is the well-documented public BTS schema, corroborated by an
  independent open-source mirror project (`github.com/dosedaf/bts-ontime-mirror`, ~30–60 MB/month
  zips, matching the size class we observed) — but I did not personally unzip and inspect headers
  in this pass. First step of the download script should print `pd.read_csv(...).columns` and
  confirm the exact scheduled/actual/cancellation/date fields before building on them.
- No fallback was needed — direct download succeeded, so no degradation to summary tables is
  required for Study 2's daily-granularity requirement.

---

## E. Ephemeris ground truth

No single source tabulates all 12 zodiac sign ingresses *and* Mercury retrograde stations in one
citable table, because only 4 of the 12 ingresses (equinoxes/solstices) are standard almanac
entries. Recommended two-part validation:
1. **The Astronomical Almanac** (joint USNO/HM Nautical Almanac Office publication,
   `aa.usno.navy.mil/publications/asa`, online portal `asa.usno.navy.mil`) — authoritative, citable,
   government-published equinox/solstice (UT) times. Use as gold-standard spot-checks for the
   Aries/Cancer/Libra/Capricorn ingresses (the 4 cardinal ones) each year.
2. **NASA/JPL Horizons** (`ssd.jpl.nasa.gov/horizons`, free, keyless web/API access) queried
   directly for apparent geocentric ecliptic longitude crossings (all 12 ingresses) and for
   Mercury's apparent-motion sign changes (retrograde stations) — this is an independent query
   path against the same underlying JPL ephemeris family used by `skyfield`/DE440, so it won't
   catch a wrong-ephemeris error, but it will catch coding/timezone/frame bugs in the project's own
   ingress/station-finding code, which is the more likely failure mode.
3. Secondary, non-authoritative cross-checks only (not for citation): `trackingmercury.com` states
   it computes 1900–2100 Mercury stations from JPL Horizons; useful as a quick sanity diff against
   the project's own output, not as the cited source in the paper.

**Obstacle:** there is no free, pre-published, citable single table covering the full 1976–2021 (or
3500BC–2018AD) span needed for Study 1's per-birth-year ingress dates — these must be **computed**
by the project's own `skyfield`/DE440 pipeline, with the Astronomical Almanac + JPL Horizons used
only as spot-check validation at a sample of years, not as the primary data source.

---

## Recommendation per study

| Study | Primary source | Status | Key open item before GATE 1 |
|---|---|---|---|
| 1 (RDD) | Wikidata SPARQL, `P569`(day-precision)+`P106` | **Usable, but acquisition strategy must change** from per-year live aggregate queries (they time out) to a two-step VALUES-batch pattern or an offline dump. Occupation/century/heaping breakdowns are unmeasured — must be produced by the download script, not assumed, before the bandwidth is fixed. | Real heaping quantification; confirmed occupation-category counts |
| 1 (cross-val) | Laouenan et al., Sciences Po Dataverse `10.21410/7E4/RDAG3O` | **Real, resolvable, free, CC-BY-SA-4.0.** Schema/precision unconfirmed pending direct file inspection. | Inspect actual CSV columns after download |
| 2 (ITS) | BTS TranStats PREZIP direct zip | **Direct download works**, no ASP-form fallback needed. Column/byte-size confirmation pending a real HTTP client. | Confirm exact filename convention + column names |
| 3 (survey) | GSS cumulative `.dta` | **Real, free, direct link found.** ZODIAC and ASTROLGY years/N fully verified from the codebook. ASTROSCI years plausible but N unverified. **Crosstab N is an estimate (~7.5–8.3k for ASTROLGY, ~2–2.5k for ASTROSCI), not yet measured live** — must be computed from the actual file before the moderation test is finalized in the plan. | Real `pd.crosstab` on downloaded file |
| Ephemeris | JPL Horizons + Astronomical Almanac | **Available, keyless, citable for the 4 cardinal ingresses; JPL Horizons for the rest and for Mercury stations.** No single full-span citable ingress table exists — values must be computed, almanac/Horizons used only as spot-checks. | None blocking |

## Obstacles summary (things the plan should be written around, not hoped past)
- **WDQS live aggregate queries with the precision-qualifier join time out past ~1 month of data.**
  Study 1's heaping/occupation/century breakdowns are not yet measured; the download script must
  either batch via `VALUES` on person-ID lists or use an offline Wikidata dump.
- **GSS ZODIAC × belief crosstab N is an estimate, not a measured number** — resolve with one line
  of pandas immediately after download, before finalizing Study 3's power claims.
- **ASTROSCI's exact years/per-year N unconfirmed** — resolve on file load.
- **Laouenan dataset's occupation coding and birth-date precision are unconfirmed** — the paper is
  blocked everywhere (Nature/PMC/HAL all return anti-bot pages); resolve by inspecting the actual
  downloaded CSV, not the paper text.
- **BTS exact canonical filename and column list unconfirmed by direct binary inspection** — highly
  likely fine given the successful large-file fetch and independent mirror corroboration, but the
  download script should verify on first run rather than assume.
