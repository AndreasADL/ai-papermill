# Idea: Pesticide use and breast cancer in France

## Research question
Is department-level pesticide use in mainland France associated with department-level
female breast cancer mortality, after adjusting for socioeconomic deprivation and
urbanization/population density?

## Hypothesis (directional, as stated by user framing)
Higher agricultural pesticide use (sales/ha or intensity) at the department level is
associated with higher age-standardized female breast cancer mortality rates.

This is an **ecological (area-level) correlational study**. No public dataset links
individual pesticide exposure to individual breast cancer outcomes in France (privacy
restrictions on health microdata). Area-level association does not imply individual-level
causation (ecological fallacy risk) — this will be stated explicitly as a limitation.

## Population / unit of analysis
- ~96 metropolitan French departments (INSEE codes 01–95, excl. Corsica codes as needed
  depending on data availability), most recent year(s) for which both exposure and
  outcome data are available.
- Unit: department-year or department (single cross-section / pooled years — TBD by
  data-scout findings and analysis plan).

## Outcome
- **Primary**: Age-standardized female breast cancer mortality rate by department
  (INSERM CépiDc death-certificate data — full national coverage, all departments).
- **Secondary / robustness (if feasible)**: Age-standardized incidence rate from FRANCIM
  registry-covered departments (~20 of 96) — smaller sample, more direct measure of new
  cases (mortality conflates incidence with survival/treatment access/screening).

## Exposure
- Department-level agricultural pesticide use (BNVD — Banque Nationale des Ventes de
  produits phytopharmaceutiques — sales data by department) or an equivalent public
  intensity/use proxy identified by data-scout. Likely need to normalize by agricultural
  area (kg or dose-units per hectare of utilized agricultural area).

## Candidate confounders (to prioritize in the plan)
- Socioeconomic/deprivation index (INSEE — e.g., median income, unemployment rate)
- Urbanization / population density (INSEE)
- Age structure — handled via age-standardization of rates regardless of the above
- Mammography screening participation rate flagged as a candidate but not mandated by
  user; data-scout/analysis-plan to assess availability and whether to include as
  confounder or robustness check, given it may sit on the causal pathway to *detected*
  incidence (less relevant for mortality as primary outcome).

## Constraints / decisions from intake (user-approved)
- Geographic unit: **department-level**, most recent available year(s).
- Primary outcome: **mortality** (full national coverage) over incidence (registry
  subsample), due to power/coverage tradeoff. Incidence may be used as secondary/
  robustness outcome if feasible.
- Confounders to prioritize: **socioeconomic/deprivation index** and
  **urbanization/population density**.
- Language: associational only ("is associated with", "predicts") — never causal.

## Open items for Phase 1 scouting
- Exact BNVD data structure, years covered, department-level availability, and whether
  it's sales (proxy for use) vs. actual use/application data.
- Exact CépiDc mortality data access (by cause ICD-10 code, by department, by sex, by
  year) and age-standardization availability (or raw counts + population for own
  standardization).
- INSEE data for deprivation index and density by department.
- FRANCIM registry department list and incidence data access, for secondary outcome.
