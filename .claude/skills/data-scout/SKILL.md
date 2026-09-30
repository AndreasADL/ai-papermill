---
name: data-scout
description: Find, evaluate, and download public datasets suitable for a research question (psych/social science, economics/policy, health). Use when a study needs data and the user has not supplied their own.
---

# Data Scout

Goal: identify datasets that actually contain the variables needed, then acquire them reproducibly. Never fabricate or simulate data as a substitute (simulation only if the user explicitly requests it, and clearly labeled).

## Where to look (by domain)

**Cross-domain / easiest first**
- Our World in Data: tidy CSVs, e.g. `https://ourworldindata.org/grapher/{slug}.csv` (find slug on the chart page). Metadata: same URL with `.metadata.json`.
- World Bank API (keyless): `https://api.worldbank.org/v2/country/all/indicator/{INDICATOR}?format=json&per_page=20000&date=2000:2025`. Find indicators via `https://api.worldbank.org/v2/indicator?format=json` or web search "world bank indicator {topic}".
- Kaggle, OSF (osf.io), Zenodo, Harvard Dataverse — search web, download direct file links.

**Psych / social science**
- GSS (General Social Survey): downloadable Stata/SPSS files from gss.norc.org; `pd.read_stata` works.
- World Values Survey, European Social Survey (registration may be needed — if so, tell the user exactly what to download and where to put it).
- OSF repositories attached to published papers (check lit-scan results for data availability statements).

**Economics / policy**
- World Bank (above), OECD SDMX API, Eurostat API, IMF. FRED requires a free API key — if needed, ask the user for one.

**Health**
- NHANES: direct XPT downloads from `wwwn.cdc.gov/Nchs/Nhanes/{cycle}/{FILE}.XPT`; read with `pd.read_sas(path, format="xport")`. Variable docs on the accompanying .htm pages.
- WHO GHO OData API: `https://ghoapi.azureedge.net/api/{IndicatorCode}` (keyless).
- CDC WONDER, GBD results tool (web download).

## Procedure

1. From `idea.md`, list required variables: outcome, predictor(s), plausible confounders, unit of analysis, time span.
2. Search candidate sources. For each candidate, **verify variables exist** by downloading a sample or reading the codebook — do not shortlist on name alone.
3. Produce a shortlist (2–4 candidates) in `data/candidates.md`: source, N, unit, years, exact variable names, license, access method, limitations. Recommend one.
4. After GATE 1 approval, download with a script (`analysis/00_download.py`) so acquisition is reproducible. Save originals untouched in `data/raw/`.
5. Log in `data/provenance.md`: URL, query/parameters, download date, file hash (`sha256sum`), license/terms, and every transformation applied later.

## Rules
- Respect licenses and terms; note any citation requirements for the dataset.
- If merging datasets (e.g., country-year), document join keys and report how many rows dropped.
- If no adequate data exists, report that honestly with the closest alternatives and what each would compromise.
