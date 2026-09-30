# Data candidates — Pesticide use and female breast cancer mortality, French departments

Scouted 2026-08-08. This is a multi-source ecological study; candidates are grouped by
role (exposure / outcome / confounders). Verification method is noted per source:
"API-verified" = actual JSON records were pulled and inspected (real field names +
real values seen); "documentation-verified" = confirmed via official metadata/
documentation pages describing file structure, but the raw file itself was not opened
byte-for-byte in this scouting pass (no bash/python execution tool available in this
session — only web fetch). Documentation-verified sources should have one sample file
pulled and parsed in Phase 3 before finalizing variable names.

---

## 1. EXPOSURE — agricultural pesticide sales/use by department

### Candidate 1A (recommended): BNV-D Traçabilité — sales data by distributor department
- **Source**: Banque Nationale des Ventes de produits phytopharmaceutiques (BNV-D),
  run by the French water agencies / OFB (Office français de la biodiversité), hosted
  on data.eaufrance.fr and mirrored on data.gouv.fr.
- **URLs**:
  - Query/export tool: https://ventes-produits-phytopharmaceutiques.eaufrance.fr/
  - Open data (sales by dept): https://www.data.gouv.fr/fr/datasets/ventes-de-pesticides-par-departement/
  - Open data (purchases by buyer postcode, 2013+): https://www.data.gouv.fr/fr/datasets/achats-de-pesticides-par-code-postal/
  - Metadata records: data.ofb.fr catalogue (sales: id bd45f801-45f7-4f8c-b128-a1af3ea2aa3e;
    purchases: id a69c8e76-13e1-4f87-9f9d-1705468b7221)
- **Contents / resolution**: Annual files named
  `BNVD_TRACABILITE_{production_date}_VENTE_DPT_SUBSTANCE_{year}` (active-substance
  quantities by department) and `..._VENTE_DPT_PRODUIT_{year}` (commercial product
  quantities). 69 dept-level files + national aggregates; CSV.GZ (`;`-separated, UTF-8)
  through 2024 vintage, Parquet from 2025. **Department-level geographic resolution
  confirmed** (dept of the *selling distributor*, not necessarily of use).
- **Years covered**: Sales 2008–2024 (17 annual vintages); purchases (buyer postal
  code, closer to point of use) 2013–2023.
- **Unit / normalization**: Quantities are in kg of declared product and kg of active
  substance per substance per department per year (documentation-verified; exact
  column list — e.g. presence of a CMR/classification flag — not yet opened from a raw
  file). To get an intensity measure, normalize by Agreste utilized agricultural area
  (candidate 1B) → kg active substance / ha SAU.
- **Access**: Direct download, no registration. **Licence Ouverte / Etalab 2.0.**
- **Key caveat (well-documented, must appear in limitations)**: BNV-D sales are
  recorded at the **distributor's department**, not the department where the product
  is applied — large agri-cooperatives and wholesalers can sell across department
  lines, so sales ≠ use at the department level. The purchase-side file (buyer postal
  code, 2013–2023) is a somewhat closer proxy for use location and should be
  preferred if it can be aggregated to department reliably; flag as a robustness
  check (sales-based vs. purchase-based exposure).
- **Verification status**: documentation-verified (data.gouv.fr resource listing,
  eaufrance.fr open-data announcement). Raw CSV.GZ not opened in this pass — do this
  first in Phase 3 (`00_download.py`) to lock exact column names before analysis.

### Candidate 1B (normalizer, not exposure itself): Agreste — Surface Agricole Utilisée (SAU)
- **Source**: Agreste (French Ministry of Agriculture statistics), Recensement
  Agricole, redistributed via L'Observatoire des Territoires.
- **URL**: https://www.observatoire-des-territoires.gouv.fr/surface-agricole-utilisee-sau
- **Contents**: "Surface agricole utilisée (SAU)" in hectares, downloadable at
  department level (among ~30 territorial levels offered).
- **Years**: Agricultural Census cross-sections — RA2010 and RA2020 (both referenced
  by the platform); **not annual**, a real limitation given BNV-D is annual.
- **Caveat**: SAU is geocoded to the commune of the farm's main production site, so
  department totals can be distorted for farms operating across department borders
  (documented caveat on the source page). Also: only two census years available
  (~2010, ~2020), so normalization will use the census year nearest to whichever
  sales year(s) are chosen, not a perfect year match.
- **Access**: Direct CSV download, no registration. Public/open (Etalab-style).
- **Verification status**: documentation-verified (page content fetched and described
  directly).

---

## 2. OUTCOME — female breast cancer mortality by department

### Candidate 2A (recommended, primary): Santé publique France / InVS-HCL-Francim modeled department estimates
- **Source**: "Estimations nationales de l'incidence et de la mortalité par cancer en
  France" (Francim/HCL/InVS/Santé publique France joint project), distributed via the
  Odissé open-data portal.
- **Dataset**: `cancer-incidence-et-mortalite-estimees-departement`
- **URL / API**: https://odisse.santepubliquefrance.fr/explore/dataset/cancer-incidence-et-mortalite-estimees-departement/
  (API: `.../api/records/1.0/search/?dataset=cancer-incidence-et-mortalite-estimees-departement`)
- **Verification**: **API-verified** — queried directly and inspected real JSON
  records. Confirmed fields: `lib` (cause label — "Sein" confirmed present),
  `sexe` ("Femmes" confirmed), `indic` ("Mortalité" / "Incidence"), `periode`,
  `dept` (department code), `libgeo` (department name), `reg`/`reglib` (region),
  `est` (rate estimate per 100,000), `low`/`up` (95% CI bounds).
- **Coverage**: **All French departments** (mainland + overseas) — this is a
  model-smoothed estimate, not raw registry counts, so there is **no small-department
  suppression** and no gap for non-registry departments. Facet counts: 3,822 records
  tagged `Mortalité` (period 2007–2014, pooled) and 3,038 tagged `Incidence` (period
  2007–2016, pooled) across all cancer sites × sex × department.
- **N / unit**: ~96 metropolitan departments (+ DOM), one pooled estimate per
  department for the given period — i.e., this is a single cross-section, not
  department-year panel.
- **Standardization**: Rates are age-standardized (world-standard-population
  convention used throughout this InVS/Francim series); already computed, no
  additional standardization work needed.
- **Access**: Free, direct API/CSV export, no registration. Licence Ouverte.
- **Key caveat**: **Temporal gap** — periods end in 2014 (mortality) / 2016
  (incidence), i.e. roughly 10–15 years old relative to the most recent BNV-D sales
  vintage (2024). Mitigation: BNV-D sales data starts in 2008, so sales averaged over
  **2008–2014** (mortality) or **2008–2016** (incidence) can be matched to this
  outcome's exact estimation window — this is a genuinely well-aligned pairing, not
  just "use most recent of everything." Agreste RA2010 (rather than RA2020) would be
  the better-matched SAU normalizer for this period.

### Candidate 2B (alternative/robustness, more recent but unconfirmed access): CépiDc/Inserm raw open data
- **Source**: INSERM CépiDc, open-data query tool.
- **URL**: https://opendata-cepidc.inserm.fr/ (interactive query tool; JavaScript
  single-page app — could not be rendered/parsed via fetch in this session). Also
  listed under data.gouv.fr dataset "Causes de décès"
  (https://www.data.gouv.fr/datasets/causes-de-deces), 10 files, 8 xlsx (23–49 KB,
  too small to be the full department × cause × age × sex × year table — these look
  like DREES national/regional summary tables, not the granular file) + 1 CSV
  (312 KB). 2024 data released 2026-06-23.
- **Contents (per CépiDc documentation, not directly opened)**: Deaths by ICD-10
  cause (filterable to C50 for breast cancer), sex, age group, department, year;
  covers 1979 to the most recent release year. An anonymization procedure is applied
  to the department-level open-data extracts.
- **Standardization**: **Not provided directly** — raw counts by age group would
  need to be combined with INSEE population-by-age-department-sex denominators to
  compute age-standardized rates ourselves (extra processing step vs. candidate 2A).
- **Access obstacle (flag explicitly)**: The genuinely granular department-level
  file (dept × ICD-10 × sex × age × year) was **not confirmed accessible** by this
  scouting pass — the interactive JS tool could not be inspected, and the
  data.gouv.fr file sizes are inconsistent with that granularity. This needs a
  hands-on check in Phase 3 (open in an actual browser or find a documented API
  endpoint) before this can be relied on.
- **Suppression caveat**: If the granular file is obtained, small departments will
  likely have low annual breast-cancer-death counts in some age strata, risking
  statistical-secrecy masking/rounding — a real limitation for a department-year
  panel design even if access is resolved.
- **Verdict**: promising for recency but **not verified this round**; use as a
  stretch/robustness source only if Phase 3 confirms clean department-level access,
  otherwise rely on 2A.

---

## 3. SECONDARY OUTCOME (robustness) — breast cancer incidence, registry-covered departments

### Candidate 3: FRANCIM — observed incidence in registry zones (Odissé)
- **Dataset**: `cancer-incidence-observee-en-zone-registres-departement`
- **URL / API**: https://odisse.santepubliquefrance.fr/explore/dataset/cancer-incidence-observee-en-zone-registres-departement/
- **Verification**: **API-verified** — real records inspected. Confirmed fields:
  `site_label` (cancer site — breast confirmed present), `sexe`, `dept`, `zr`
  (registry zone), `periode` (rolling 5-year windows), `rate` (crude rate),
  `ratemonde` (world-age-standardized rate), `k` (observed case count), `pa`
  (population at risk), `rate_inf`/`rate_sup` (95% CI). Sample real values seen:
  Calvados (dept 14) 2018–2022, women, breast: rate=190.5/100k, ratemonde=102.5;
  Charente-Maritime (dept 17) 2018–2022: rate=209.8/100k, ratemonde=99.0.
- **Coverage**: Only departments with an active FRANCIM population-based cancer
  registry — confirmed at least depts 14 (Calvados) and 17 (Charente-Maritime) in
  this pass; per idea.md framing, ~20 of 96 departments total are registry-covered.
  Full department list should be enumerated in Phase 3 (facet query on `dept`).
- **Years**: Rolling 5-year periods from 1988–1992 through **2018–2022** — this is
  the **most recent** outcome data found for this study, and could be paired with
  recent BNV-D sales (e.g. 2018–2022 average) and Agreste RA2020 SAU for a
  well-time-aligned robustness subsample.
- **N**: ~20 departments — substantially underpowered for the main model; appropriate
  only as a robustness/sensitivity check on the ~20-department subsample, not the
  primary analysis.
- **Access**: Free, direct API/CSV, no registration. Licence Ouverte.
- **Advantage over 2A**: directly observed (not modeled), both crude and
  age-standardized rates plus raw counts/denominators are given, so own
  standardization checks are possible.

---

## 4. CONFOUNDERS

### 4A. Socioeconomic deprivation — INSEE FiLoSoFi poverty rate (recommended primary)
- **URL**: https://www.observatoire-des-territoires.gouv.fr/taux-de-pauvrete-seuil-60-du-revenu-median
- **Contents**: "Taux de pauvreté (seuil à 60% du revenu médian)" — share of
  population below 60% of median income, department level, source = FiLoSoFi
  (fiscal + social benefit microdata, INSEE/CNAF/CNAV/MSA). Confirmed via search
  that department-level values are published and range realistically (e.g. ~9% in
  Vendée up to much higher in some overseas depts), consistent with known FiLoSoFi
  outputs.
- **Companion indicators on the same platform** (same access pattern as SAU/density
  above, not yet individually URL-confirmed — verify exact slugs in Phase 3): median
  household income, unemployment rate. A direct attempt at
  `.../indicateurs/revenu-median-des-menages` 404'd, so the exact income-indicator
  slug needs re-finding in Phase 3; poverty rate URL is confirmed working.
- **Access**: Direct download, no registration, Licence Ouverte.
- **Temporal caveat**: FiLoSoFi vintages generally start around 2012; matching the
  2007–2014 mortality period (candidate 2A) exactly is not possible with FiLoSoFi
  alone — earliest available vintage (~2012) would have to serve as a reasonable
  proxy for department-level SES, which changes slowly enough that this is a minor
  compromise, but should be stated explicitly in provenance.

### 4B. Socioeconomic deprivation — true FDep index (alternative, more work)
- **Source**: Inserm French Deprivation Index (FDep; Rey et al. methodology).
  Directly downloadable at **commune** or **IRIS** level only (e.g. Odissé dataset
  "indice-de-defavorisation-sociale-fdep-par-commune"); department-level FDep is
  **not directly downloadable** — the official methodology explicitly defines
  department-level FDep as the population-weighted average of commune-level scores,
  which we would need to compute ourselves.
- **Verdict**: only use if the analysis plan specifically wants the validated FDep
  construct over simpler INSEE indicators; adds a real aggregation step. Otherwise
  4A (poverty rate + income + unemployment, already at department level) is
  sufficient and simpler.

### 4C. Urbanization / population density — INSEE via Observatoire des Territoires
- **URL**: https://www.observatoire-des-territoires.gouv.fr/densite-de-population
- **Contents**: Population density (inhabitants/km²), department level, INSEE
  source, multiple years available (annual population estimates over a fixed area).
- **Access**: Direct download, no registration, Licence Ouverte.
- **Caveat**: none identified; straightforward, same platform/access pattern as SAU
  and poverty rate, good for consistent department-code joins.

---

## Recommendation

**Primary analysis pairing** (best-verified, no access obstacles, full department
coverage, reasonably time-aligned):
- Exposure: BNV-D sales, active-substance kg, department, averaged **2008–2014**
  (candidate 1A), normalized by Agreste **RA2010** SAU (candidate 1B) → kg/ha.
- Outcome: Santé publique France modeled **age-standardized female breast cancer
  mortality rate**, department, period **2007–2014** (candidate 2A) — N ≈ 96
  metropolitan departments, unit = department (single cross-section).
- Confounders: FiLoSoFi poverty rate (≥60%-median threshold) + population density,
  department level, nearest available vintage (candidate 4A + 4C).

**Robustness check**: FRANCIM observed incidence, ~20 registry departments, period
2018–2022 (candidate 3), paired with BNV-D sales 2018–2022 and Agreste RA2020 SAU —
tests whether the association replicates with a more recent, directly-observed
(non-modeled) outcome, at the cost of a much smaller N.

**Open obstacles for Phase 3**:
1. BNV-D and CépiDc raw files were documentation-verified, not opened — confirm
   exact column names on first download.
2. CépiDc granular department-level file access is unconfirmed (candidate 2B) — only
   pursue if the plan wants a more recent mortality robustness check than 2007–2014.
3. Exact INSEE median-income and unemployment-rate URLs on Observatoire des
   Territoires need re-finding (poverty rate URL confirmed, income URL 404'd).
4. Full list of FRANCIM registry departments (candidate 3) needs enumeration via a
   facet query before deciding if N≈20 is usable for a meaningful robustness check.
5. No dataset licenses or access requirements found that would block use — all
   sources are Licence Ouverte / Etalab-style open data, free, no registration.
