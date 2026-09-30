# Data provenance

Study: Department-level agricultural pesticide sales intensity and female breast
cancer mortality, mainland France. All downloads performed by `analysis/00_download.py`
on 2026-08-08. Raw files are never modified after download; all transformations happen in
`analysis/01_clean.py` onward and are logged separately in `results/results.md`.

---

## 1. Outcome (primary) — breast cancer mortality

- **Source**: Sante publique France / Francim-HCL-InVS joint modeled estimates,
  Odisse open-data portal.
- **Dataset**: `cancer-incidence-et-mortalite-estimees-departement`
- **API**: `https://odisse.santepubliquefrance.fr/api/records/1.0/search/` with `refine.sexe=Femmes`, `refine.indic=Mortalité`,
  `refine.lib=Sein` (paginated, all pages retrieved).
- **Downloaded to**: `data/raw/odisse/mortality_femmes_sein_2007_2014.json`
- **Records retrieved**: 98
- **Period**: 2007-2014 (pooled, single cross-section per department).
- **Fields used**: `dept` (department code — Corsica appears unified as `20`, not
  split `2A`/`2B`), `libgeo`, `est` (age-standardized rate per 100,000), `low`, `up`
  (95% CI bounds).
- **Coverage**: all French departments (mainland + DOM), no known suppression (modeled
  estimate).
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: 2026-08-08.

## 2. Outcome (robustness, E2) — FRANCIM observed breast cancer incidence

- **Source**: FRANCIM registry network, via Odisse.
- **Dataset**: `cancer-incidence-observee-en-zone-registres-departement`
- **API**: same base, `refine.sexe=Femmes`, `refine.site_label=Sein`,
  `refine.periode=2018-2022`.
- **Downloaded to**: `data/raw/odisse/francim_incidence_femmes_sein_2018_2022.json`
- **Records retrieved**: 22 (registry zones; includes 3 DOM zones —
  Guadeloupe [971], Martinique [972], La Reunion [974] — excluded at the mainland
  filter in `01_clean.py`; 19 mainland registry departments/zones
  remain).
- **Fields used**: `dept`, `zr` (registry zone name), `ratemonde` (world-age-standardized
  rate per 100,000), `rate_inf`/`rate_sup`, `k` (observed cases), `pa` (population at
  risk).
- **Caveat**: a small number of registry zones cover only part of a department (e.g.
  `zr="Lille metropole"` reported under `dept="59"`, which is the whole Nord
  department) — inherited from the source data, documented here per plan.md's
  requirement to flag such caveats rather than silently accept them.
- **License**: Licence Ouverte / Etalab 2.0. Free, no registration.
- **Download date**: 2026-08-08.

## 3. Exposure (primary + E2 robustness) — BNV-D sales by department

- **Source**: Banque Nationale des Ventes de produits phytopharmaceutiques (BNV-D),
  OFB / French water agencies, mirrored on data.gouv.fr and hosted on data.ofb.fr.
- **Dataset**: `ventes-de-pesticides-par-departement`, resource family
  `VENTE_DPT_SUBSTANCE` (active-substance quantities sold, by department, by year).
- **Resource list confirmed via**: `https://www.data.gouv.fr/api/1/datasets/ventes-de-pesticides-par-departement/`
- **Exact files downloaded** (12 annual vintages — 2008-2014 for the primary model,
  2018-2022 for the E2 robustness subsample):
  - `VENTE_DPT_SUBSTANCE_2008.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2009.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2010.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2011.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2012.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2013.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2014.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2018.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2019.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2020.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2021.csv.gz`
  - `VENTE_DPT_SUBSTANCE_2022.csv.gz`
- **Downloaded to**: `data/raw/bnvd_vente/VENTE_DPT_SUBSTANCE_{year}.csv.gz`
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
- **Download date**: 2026-08-08.

## 4. Exposure (robustness, E1) — BNV-D purchases by buyer postal code

- **Source**: same BNV-D program, `achats-de-pesticides-par-code-postal` dataset.
- **Resource family**: `ACHAT_CP_SUBSTANCE`.
- **Resource list confirmed via**: `https://www.data.gouv.fr/api/1/datasets/achats-de-pesticides-par-code-postal/`
- **Years downloaded**: 2013-2023 inclusive (11 files), per plan.md SS7.1.
- **Downloaded to**: `data/raw/bnvd_achat/ACHAT_CP_SUBSTANCE_{year}.csv.gz`
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
- **Download date**: 2026-08-08.

## 5. Normalizer — Agreste SAU (surface agricole utilisee) by department

- **Source**: Agreste (French Ministry of Agriculture), redistributed via
  L'Observatoire des Territoires (ANCT).
- **Endpoint**: `https://www.observatoire-des-territoires.gouv.fr/outils/cartographie-interactive/api/v1/functions/GC_API_download.php?type=stat&nivgeo=dep&dataset=agri&indic=sau2020`
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
- **Download date**: 2026-08-08.

## 6. Confounder — poverty rate (FiLoSoFi, taux de pauvrete a 60% du revenu median)

- **Source**: INSEE-DGFIP-Cnaf-Cnav-CCMSA FiLoSoFi, redistributed via L'Observatoire
  des Territoires.
- **Endpoint**: `https://www.observatoire-des-territoires.gouv.fr/outils/cartographie-interactive/api/v1/functions/GC_API_download.php?type=stat&nivgeo=dep&dataset=filosofi&indic=tx_pauv_60`
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
- **Download date**: 2026-08-08.

## 7. Confounder — population density

- **Source**: INSEE Recensement de population (historical series since 1968),
  redistributed via L'Observatoire des Territoires.
- **Endpoint**: `https://www.observatoire-des-territoires.gouv.fr/outils/cartographie-interactive/api/v1/functions/GC_API_download.php?type=stat&nivgeo=dep&dataset=insee_rp_hist_1968&indic=dens_pop`
- **Downloaded to**: `data/raw/confounders/density_dens_pop_dep.xlsx` (`Data` sheet,
  columns `codgeo`, `libgeo`, `an`, `dens_pop`; inhabitants/km2).
- **Vintage used**: 2011 (available years in the file: 1968, 1975, 1982, 1990, 1999,
  2010, 2011, 2015, 2016, 2021, 2022) — chosen as the closest available year to the
  2007-2014 mortality period. **No deviation from plan.md** — this is the well-aligned
  vintage the plan anticipated.
- **License**: Licence Ouverte / Etalab-style. Free, no registration.
- **Download date**: 2026-08-08.

## 8. Department boundaries (spatial weights matrix)

- **Source**: `france-geojson` open-source project (community-maintained, widely used;
  GitHub user gregoiredavid).
- **URL**: `https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson`
- **Downloaded to**: `data/raw/geo/departements.geojson`
- **Contents confirmed**: valid GeoJSON FeatureCollection, polygon geometries, one
  feature per department, properties `code` (department code, `2A`/`2B` split for
  Corsica — matches BNV-D/confounder coding, will need aggregation to match the
  outcome's unified `20` Corsica code, same as other sources) and `nom`.
- **Used for**: Queen-contiguity spatial weights matrix (`libpysal.weights.Queen.from_dataframe`)
  for the Moran's I diagnostic in `analysis/03_main_models.py` (plan.md SS4/SS6).
- **License**: MIT (per the france-geojson repository).
- **Download date**: 2026-08-08.

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
