"""
00_download.py

Downloads all raw data for the pesticide/breast-cancer-mortality ecological study
(mainland France, department grain) into data/raw/, and writes data/provenance.md
documenting source, URL, download date, license, and any transformation/deviation
encountered along the way.

Sources (see data/candidates.md for scouting detail; see analysis/plan.md for the
approved design):
  1. Outcome (primary):  Odisse API, dataset cancer-incidence-et-mortalite-estimees-departement
     -> female breast cancer ("Sein") mortality, period 2007-2014, all departments.
  2. Outcome (robustness / E2): Odisse API, dataset
     cancer-incidence-observee-en-zone-registres-departement -> female breast cancer
     incidence, FRANCIM registry departments, period 2018-2022.
  3. Exposure (primary): BNV-D VENTE_DPT_SUBSTANCE files, years 2008-2014 (distributor
     sales, by department).
  4. Exposure (E2 robustness, same sales-based measure): BNV-D VENTE_DPT_SUBSTANCE,
     years 2018-2022.
  5. Exposure (E1 robustness, purchase-based): BNV-D ACHAT_CP_SUBSTANCE files, years
     2013-2023 (buyer postal code).
  6. Normalizer: Agreste SAU (surface agricole utilisee) by department, via the
     Observatoire des Territoires GC_API_download endpoint.
  7. Confounders: poverty rate (FiLoSoFi tx_pauv_60) and population density (dens_pop),
     department level, same Observatoire des Territoires endpoint.
  8. Department boundaries: france-geojson project (GitHub), for the Queen-contiguity
     spatial weights matrix (Moran's I diagnostic, plan.md SS4/SS6).

IMPORTANT — logged deviations from plan.md SS2 (confirmed during this download pass,
see full justification in data/provenance.md and plan.md's Deviations section):
  - Agreste SAU: plan.md specified "RA2010 vintage" as the better-matched normalizer
    for the 2007-2014 mortality period. The Observatoire des Territoires portal (the
    documentation-verified source in data/candidates.md) currently serves ONLY the
    RA2020 census vintage for this indicator (confirmed by inspecting the page's
    download-link dropdown, which lists only "sau2020"; RA2010-named indicator values
    were probed directly against the download API and returned 404). RA2020 is used
    for BOTH the primary model and the E2 robustness subsample (which already called
    for RA2020). This is logged as a deviation, not a silent substitution.
  - Poverty rate (FiLoSoFi tx_pauv_60): plan.md targeted "nearest available vintage to
    ~2012". The Observatoire des Territoires department-level download for this
    indicator currently serves only 2020 and 2021 vintages (INSEE's own direct FiLoSoFi
    downloads for ~2012 are commune-level only, not a ready-made department aggregate,
    and would require an independent population-weighted aggregation this pipeline does
    not perform). 2020 (earliest available in the confirmed working endpoint) is used
    instead. Logged as a deviation.
  - Population density: 2011 vintage used (available in the same endpoint), which DOES
    align well with the 2007-2014 mortality period as originally intended — no
    deviation here.
"""

import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import requests

SEED = 42

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROVENANCE_PATH = ROOT / "data" / "provenance.md"

CONTACT = os.environ.get("PAPERMILL_CONTACT_EMAIL", "ai-papermill@example.org")
HEADERS = {
    "User-Agent": "ai-papermill/pesticide-breast-cancer-france "
    f"(academic ecological study; contact {CONTACT})"
}

DOWNLOAD_DATE = "2026-08-08"

# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------


def get(url, params=None, timeout=60, retries=3, backoff=3):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"  [retry {attempt}/{retries}] {url} -> {exc}")
            time.sleep(backoff * attempt)
    raise RuntimeError(f"FAILED after {retries} attempts: {url}") from last_exc


def download_file(url, dest: Path, params=None, timeout=120):
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [skip, exists] {dest.name}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = get(url, params=params, timeout=timeout)
    dest.write_bytes(r.content)
    print(f"  [ok] {dest.name} ({len(r.content):,} bytes)")
    return dest


# ---------------------------------------------------------------------------
# 1/2. Odisse API (outcome, primary + robustness)
# ---------------------------------------------------------------------------

ODISSE_BASE = "https://odisse.santepubliquefrance.fr/api/records/1.0/search/"


def fetch_odisse_all(dataset, refine: dict, page_size=100):
    """Paginate the Opendatasoft v1 records API until all records are retrieved."""
    all_records = []
    start = 0
    while True:
        params = {"dataset": dataset, "rows": page_size, "start": start}
        for k, v in refine.items():
            params[f"refine.{k}"] = v
        r = get(ODISSE_BASE, params=params)
        payload = r.json()
        nhits = payload["nhits"]
        records = payload["records"]
        all_records.extend(records)
        start += page_size
        if start >= nhits or not records:
            break
    assert len(all_records) == nhits, f"paginated {len(all_records)} != nhits {nhits}"
    return all_records


def download_outcome_data():
    print("\n== Outcome (Odisse) ==")
    dest_dir = RAW / "odisse"
    dest_dir.mkdir(parents=True, exist_ok=True)

    mortality_path = dest_dir / "mortality_femmes_sein_2007_2014.json"
    if not mortality_path.exists():
        records = fetch_odisse_all(
            "cancer-incidence-et-mortalite-estimees-departement",
            {"sexe": "Femmes", "indic": "Mortalité", "lib": "Sein"},
        )
        mortality_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  [ok] {mortality_path.name} ({len(records)} records)")
    else:
        print(f"  [skip, exists] {mortality_path.name}")

    francim_path = dest_dir / "francim_incidence_femmes_sein_2018_2022.json"
    if not francim_path.exists():
        records = fetch_odisse_all(
            "cancer-incidence-observee-en-zone-registres-departement",
            {"sexe": "Femmes", "site_label": "Sein", "periode": "2018-2022"},
        )
        francim_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  [ok] {francim_path.name} ({len(records)} records)")
    else:
        print(f"  [skip, exists] {francim_path.name}")

    return mortality_path, francim_path


# ---------------------------------------------------------------------------
# 3/4. BNV-D VENTE_DPT_SUBSTANCE (sales-based exposure)
# ---------------------------------------------------------------------------

BNVD_VENTE_URL_TMPL = (
    "https://data.ofb.fr/catalogue/Donnees-geographiques-OFB/api/records/"
    "bd45f801-45f7-4f8c-b128-a1af3ea2aa3e/attachments/"
    "BNVD_TRACABILITE_20251125_VENTE_DPT_SUBSTANCE_{year}.csv.gz"
)
# Primary window (2008-2014) + E2 robustness window (2018-2022): 12 distinct years.
VENTE_YEARS = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2018, 2019, 2020, 2021, 2022]


def download_vente_files():
    print("\n== Exposure: BNV-D VENTE_DPT_SUBSTANCE (sales) ==")
    dest_dir = RAW / "bnvd_vente"
    paths = []
    for year in VENTE_YEARS:
        url = BNVD_VENTE_URL_TMPL.format(year=year)
        dest = dest_dir / f"VENTE_DPT_SUBSTANCE_{year}.csv.gz"
        paths.append(download_file(url, dest))
    return paths


# ---------------------------------------------------------------------------
# 5. BNV-D ACHAT_CP_SUBSTANCE (purchase-based exposure, E1 robustness)
# ---------------------------------------------------------------------------

BNVD_ACHAT_URL_TMPL = (
    "https://data.ofb.fr/catalogue/data-eaufrance/api/records/"
    "a69c8e76-13e1-4f87-9f9d-1705468b7221/attachments/"
    "BNVD_TRACABILITE_20251125_ACHAT_CP_SUBSTANCE_{year}.csv.gz"
)
ACHAT_YEARS = list(range(2013, 2024))  # 2013-2023 inclusive, per plan.md SS7.1


def download_achat_files():
    print("\n== Exposure: BNV-D ACHAT_CP_SUBSTANCE (purchases, E1 robustness) ==")
    dest_dir = RAW / "bnvd_achat"
    paths = []
    for year in ACHAT_YEARS:
        url = BNVD_ACHAT_URL_TMPL.format(year=year)
        dest = dest_dir / f"ACHAT_CP_SUBSTANCE_{year}.csv.gz"
        paths.append(download_file(url, dest))
    return paths


# ---------------------------------------------------------------------------
# 6/7. Observatoire des Territoires (SAU normalizer + confounders)
# ---------------------------------------------------------------------------

OBS_TERR_API = (
    "https://www.observatoire-des-territoires.gouv.fr/outils/"
    "cartographie-interactive/api/v1/functions/GC_API_download.php"
)


def download_obs_terr(dataset, indic, dest_name):
    dest = RAW / "confounders" / dest_name
    url = f"{OBS_TERR_API}?type=stat&nivgeo=dep&dataset={dataset}&indic={indic}"
    return download_file(url, dest)


def download_confounders_and_normalizer():
    print("\n== Normalizer (SAU) + confounders (poverty, density) ==")
    sau_path = download_obs_terr("agri", "sau2020", "sau2020_dep.xlsx")
    poverty_path = download_obs_terr("filosofi", "tx_pauv_60", "poverty_tx_pauv_60_dep.xlsx")
    density_path = download_obs_terr(
        "insee_rp_hist_1968", "dens_pop", "density_dens_pop_dep.xlsx"
    )
    return sau_path, poverty_path, density_path


# ---------------------------------------------------------------------------
# 8. Department boundaries (for Moran's I spatial weights)
# ---------------------------------------------------------------------------

GEOJSON_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements.geojson"
)


def download_geo():
    print("\n== Department boundaries (france-geojson) ==")
    dest = RAW / "geo" / "departements.geojson"
    return download_file(GEOJSON_URL, dest)


# ---------------------------------------------------------------------------
# provenance.md
# ---------------------------------------------------------------------------

PROVENANCE_TEMPLATE = """# Data provenance

Study: Department-level agricultural pesticide sales intensity and female breast
cancer mortality, mainland France. All downloads performed by `analysis/00_download.py`
on {date}. Raw files are never modified after download; all transformations happen in
`analysis/01_clean.py` onward and are logged separately in `results/results.md`.

---

## 1. Outcome (primary) — breast cancer mortality

- **Source**: Sante publique France / Francim-HCL-InVS joint modeled estimates,
  Odisse open-data portal.
- **Dataset**: `cancer-incidence-et-mortalite-estimees-departement`
- **API**: `{odisse_base}` with `refine.sexe=Femmes`, `refine.indic=Mortalité`,
  `refine.lib=Sein` (paginated, all pages retrieved).
- **Downloaded to**: `data/raw/odisse/mortality_femmes_sein_2007_2014.json`
- **Records retrieved**: {n_mortality}
- **Period**: 2007-2014 (pooled, single cross-section per department).
- **Fields used**: `dept` (department code — Corsica appears unified as `20`, not
  split `2A`/`2B`), `libgeo`, `est` (age-standardized rate per 100,000), `low`, `up`
  (95% CI bounds).
- **Coverage**: all French departments (mainland + DOM), no known suppression (modeled
  estimate).
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: {date}.

## 2. Outcome (robustness, E2) — FRANCIM observed breast cancer incidence

- **Source**: FRANCIM registry network, via Odisse.
- **Dataset**: `cancer-incidence-observee-en-zone-registres-departement`
- **API**: same base, `refine.sexe=Femmes`, `refine.site_label=Sein`,
  `refine.periode=2018-2022`.
- **Downloaded to**: `data/raw/odisse/francim_incidence_femmes_sein_2018_2022.json`
- **Records retrieved**: {n_francim} (registry zones; includes 3 DOM zones —
  Guadeloupe [971], Martinique [972], La Reunion [974] — excluded at the mainland
  filter in `01_clean.py`; {n_francim_mainland} mainland registry departments/zones
  remain).
- **Fields used**: `dept`, `zr` (registry zone name), `ratemonde` (world-age-standardized
  rate per 100,000), `rate_inf`/`rate_sup`, `k` (observed cases), `pa` (population at
  risk).
- **Caveat**: a small number of registry zones cover only part of a department (e.g.
  `zr="Lille metropole"` reported under `dept="59"`, which is the whole Nord
  department) — inherited from the source data, documented here per plan.md's
  requirement to flag such caveats rather than silently accept them.
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: {date}.

## 3. Exposure (primary + E2 robustness) — BNV-D sales by department

- **Source**: Banque Nationale des Ventes de produits phytopharmaceutiques (BNV-D),
  OFB / French water agencies, mirrored on data.gouv.fr and hosted on data.ofb.fr.
- **Dataset**: `ventes-de-pesticides-par-departement`, resource family
  `VENTE_DPT_SUBSTANCE` (active-substance quantities sold, by department, by year).
- **Resource list confirmed via**: `https://www.data.gouv.fr/api/1/datasets/ventes-de-pesticides-par-departement/`
- **Exact files downloaded** (12 annual vintages — 2008-2014 for the primary model,
  2018-2022 for the E2 robustness subsample):
{vente_file_list}
- **Downloaded to**: `data/raw/bnvd_vente/VENTE_DPT_SUBSTANCE_{{year}}.csv.gz`
- **Columns confirmed by opening a raw file**: `annee`, `code_departement`
  (zero-padded, Corsica split as `2A`/`2B`), `departement` (name), `amm` (product
  authorization number), `substance`, `cas` (CAS number), `fonction` (e.g.
  Insecticide/Herbicide/Fongicide), `classification`, `classification_mention`,
  `quantite_substance` (kg of active substance).
- **Key caveat (from candidates.md, confirmed still applicable)**: sales are recorded
  at the distributor's department, not necessarily the department of use — sales !=
  use at the department level. Addressed via the E1 purchase-based robustness check
  (below).
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: {date}.

## 4. Exposure (robustness, E1) — BNV-D purchases by buyer postal code

- **Source**: same BNV-D program, `achats-de-pesticides-par-code-postal` dataset.
- **Resource family**: `ACHAT_CP_SUBSTANCE`.
- **Resource list confirmed via**: `https://www.data.gouv.fr/api/1/datasets/achats-de-pesticides-par-code-postal/`
- **Years downloaded**: 2013-2023 inclusive (11 files), per plan.md SS7.1.
- **Downloaded to**: `data/raw/bnvd_achat/ACHAT_CP_SUBSTANCE_{{year}}.csv.gz`
- **Columns confirmed by opening a raw file**: `annee`, `code_postal_acheteur` (5-digit
  buyer postal code), `achat_etranger` (Oui/Non — foreign purchase flag), `amm`,
  `substance`, `cas`, `fonction`, `classification`, `classification_mention`,
  `quantite_substance` (kg active substance).
- **Department mapping caveat**: this file gives postal code, not department code
  directly. `01_clean.py` maps postal code -> department using the first two digits
  of the 5-digit postal code, with the standard Corsica correction (postal codes
  20000-20199 -> department 2A, 20200-20999 -> department 2B) and DOM postal-code
  prefixes (971-976) mapped to their DOM department codes and then excluded under the
  mainland-only inclusion criterion. This is a standard, documented simplification
  (a handful of postal codes straddle department borders in ways this simple mapping
  will not catch); rows with `achat_etranger="Oui"` are excluded (no French department
  to assign).
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: {date}.

## 5. Normalizer — Agreste SAU (surface agricole utilisee) by department

- **Source**: Agreste (French Ministry of Agriculture), redistributed via
  L'Observatoire des Territoires (ANCT).
- **Endpoint**: `{obs_terr_api}?type=stat&nivgeo=dep&dataset=agri&indic=sau2020`
- **Downloaded to**: `data/raw/confounders/sau2020_dep.xlsx` (`Data` sheet, columns
  `codgeo`, `libgeo`, `an`, `sau2020`; hectares).
- **DEVIATION FROM PLAN.MD SS2** (logged here and in `analysis/plan.md`'s Deviations
  section): the plan specified RA2010 (2010 agricultural census) as the better-aligned
  SAU vintage for the 2007-2014 mortality period. The Observatoire des Territoires page
  for this indicator (`https://www.observatoire-des-territoires.gouv.fr/surface-agricole-utilisee-sau`)
  currently exposes **only the RA2020 vintage** through its download-link dropdown
  (`indic=sau2020`); direct probes of the download API with candidate RA2010 indicator
  names (`sau2010`, `sau10`, `sau_2010`) all returned 404. RA2020 is used for both the
  primary model and the E2 robustness subsample (E2 already specified RA2020).
  **Justification for proceeding rather than stopping**: SAU is a slow-changing
  structural land-use variable at department grain (candidates.md already flagged this
  as "only two census years available, ~2010/~2020" and anticipated a vintage
  mismatch); using the one confirmed-accessible vintage consistently across both models
  is preferred over fabricating or estimating a RA2010 figure.
- **License**: Licence Ouverte / Etalab-style. Free, no registration.
- **Download date**: {date}.

## 6. Confounder — poverty rate (FiLoSoFi, taux de pauvrete a 60% du revenu median)

- **Source**: INSEE-DGFIP-Cnaf-Cnav-CCMSA FiLoSoFi, redistributed via L'Observatoire
  des Territoires.
- **Endpoint**: `{obs_terr_api}?type=stat&nivgeo=dep&dataset=filosofi&indic=tx_pauv_60`
- **Downloaded to**: `data/raw/confounders/poverty_tx_pauv_60_dep.xlsx` (`Data` sheet,
  columns `codgeo`, `libgeo`, `an`, `tx_pauv_60`; % of population below 60% of median
  income).
- **DEVIATION FROM PLAN.MD SS2** (logged here and in `analysis/plan.md`'s Deviations
  section): the plan targeted "nearest available vintage to ~2012" (the earliest
  FiLoSoFi vintage, matching the mortality outcome period better than later vintages).
  The confirmed-working Observatoire des Territoires endpoint for this indicator
  currently serves **only 2020 and 2021** vintages. INSEE's own direct FiLoSoFi
  downloads for ~2012-2016 (checked at `insee.fr/fr/statistiques/1895078` and
  `insee.fr/fr/statistiques/4190004`) are **commune-level only** ("base-cc-filosofi-*"
  files) with no ready-made department aggregate; computing one ourselves would require
  an independent population-weighted aggregation across communes (including handling
  commune-level secret-statistique suppression), which this pipeline does not attempt
  in order to avoid introducing an unaudited derived statistic. **2020** (the earliest
  vintage available through the confirmed working department-level endpoint) is used
  instead. This is a **materially larger temporal gap than planned** (2020 vs. the
  targeted ~2012, an 8-year gap vs. mortality period 2007-2014) and is flagged
  explicitly as a limitation in `results/results.md`.
- **License**: Licence Ouverte / Etalab-style. Free, no registration.
- **Download date**: {date}.

## 7. Confounder — population density

- **Source**: INSEE Recensement de population (historical series since 1968),
  redistributed via L'Observatoire des Territoires.
- **Endpoint**: `{obs_terr_api}?type=stat&nivgeo=dep&dataset=insee_rp_hist_1968&indic=dens_pop`
- **Downloaded to**: `data/raw/confounders/density_dens_pop_dep.xlsx` (`Data` sheet,
  columns `codgeo`, `libgeo`, `an`, `dens_pop`; inhabitants/km2).
- **Vintage used**: 2011 (available years in the file: 1968, 1975, 1982, 1990, 1999,
  2010, 2011, 2015, 2016, 2021, 2022) — chosen as the closest available year to the
  2007-2014 mortality period. **No deviation from plan.md** — this is the well-aligned
  vintage the plan anticipated.
- **License**: Licence Ouverte / Etalab-style. Free, no registration.
- **Download date**: {date}.

## 8. Department boundaries (spatial weights matrix)

- **Source**: `france-geojson` open-source project (community-maintained, widely used;
  GitHub user gregoiredavid).
- **URL**: `{geojson_url}`
- **Downloaded to**: `data/raw/geo/departements.geojson`
- **Contents confirmed**: valid GeoJSON FeatureCollection, polygon geometries, one
  feature per department, properties `code` (department code, `2A`/`2B` split for
  Corsica — matches BNV-D/confounder coding, will need aggregation to match the
  outcome's unified `20` Corsica code, same as other sources) and `nom`.
- **Used for**: Queen-contiguity spatial weights matrix (`libpysal.weights.Queen.from_dataframe`)
  for the Moran's I diagnostic in `analysis/03_main_models.py` (plan.md SS4/SS6).
- **License**: MIT (per the france-geojson repository).
- **Download date**: {date}.

---

## Corsica department-code handling (applies to all sources above)

- The primary/robustness **outcome** (Odisse) reports Corsica as a single unified
  department code `20` (legacy pre-1976 coding).
- **BNV-D** (sales and purchases) and all three **Observatoire des Territoires**
  confounder/normalizer files, and the **geojson**, report Corsica split into `2A`
  (Corse-du-Sud) and `2B` (Haute-Corse) — modern INSEE coding.
- To join these consistently with the outcome data, `01_clean.py` aggregates `2A`+`2B`
  into a single `20` row for every exposure/confounder/normalizer source: **summed**
  for extensive quantities (BNV-D kg, SAU hectares) and **simple (unweighted) mean**
  for intensive/rate quantities (poverty rate %, population density) — the latter is a
  documented approximation (a population-weighted mean would be more precise but no
  population-count file was downloaded independently of density; Corsica is 2 of ~95
  mainland departments, so the impact on the overall regression is expected to be
  minimal). This affects exactly one analysis unit (Corsica) out of ~95.

## Missing / suppressed values

Assessed and logged in `results/results.md` (produced by `01_clean.py`), per plan.md
SS3's pre-specified missing-data handling protocol.

## Deviations from plan.md (summary — full text in `analysis/plan.md`'s Deviations
section)

1. SAU normalizer: RA2020 used in place of the planned RA2010 vintage (see SS5 above).
2. Poverty rate: 2020 vintage used in place of the planned ~2012 vintage (see SS6
   above).

No other deviations were required — the Odisse mortality/incidence API, BNV-D sales
and purchase files, population density, and department geojson were all available
exactly as anticipated in `data/candidates.md`.
"""


def write_provenance(mortality_path, francim_path, vente_paths):
    import gzip

    mortality_records = json.loads(mortality_path.read_text(encoding="utf-8"))
    francim_records = json.loads(francim_path.read_text(encoding="utf-8"))
    n_francim_mainland = sum(
        1 for r in francim_records if not str(r["fields"]["dept"]).startswith("97")
    )

    vente_file_list = "\n".join(
        f"  - `VENTE_DPT_SUBSTANCE_{year}.csv.gz`" for year in VENTE_YEARS
    )

    text = PROVENANCE_TEMPLATE.format(
        date=DOWNLOAD_DATE,
        odisse_base=ODISSE_BASE,
        n_mortality=len(mortality_records),
        n_francim=len(francim_records),
        n_francim_mainland=n_francim_mainland,
        vente_file_list=vente_file_list,
        obs_terr_api=OBS_TERR_API,
        geojson_url=GEOJSON_URL,
    )
    PROVENANCE_PATH.write_text(text, encoding="utf-8")
    print(f"\n[ok] wrote {PROVENANCE_PATH}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    mortality_path, francim_path = download_outcome_data()
    vente_paths = download_vente_files()
    download_achat_files()
    download_confounders_and_normalizer()
    download_geo()
    write_provenance(mortality_path, francim_path, vente_paths)
    print("\n00_download.py complete.")


if __name__ == "__main__":
    main()
