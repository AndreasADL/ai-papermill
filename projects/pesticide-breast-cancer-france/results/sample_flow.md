# Sample flow — 01_clean.py

Run parameters: SEED=42, sales years=[2008, 2009, 2010, 2011, 2012, 2013, 2014], poverty vintage=2020, density vintage=2011.

1. Outcome (Odisse mortality, Femmes/Mortalité/Sein, 2007-2014): N = 98 (all departments incl. DOM).
   -> after excluding DOM (mainland-only inclusion criterion): N = 95 (dropped 3).

2. Exposure (BNV-D VENTE_DPT_SUBSTANCE, summed 2008-2014, mainland only, Corsica 2A+2B summed to '20'): N = 95 departments with at least one non-suppressed sales record.
   -> every mainland department has at least one non-suppressed sales record across 2008-2014 (no full-department suppression found).

3. Normalizer (Agreste RA2020 SAU, mainland, Corsica summed): N = 95 departments.

4a. Confounder (FiLoSoFi poverty rate, vintage 2020, mainland, Corsica averaged): N = 95 departments.
4b. Confounder (INSEE population density, vintage 2011, mainland, Corsica averaged): N = 95 departments.

5. Merge outcome + exposure: N = 95 (left join on mortality mainland N=95; 0 unmatched on exposure).
   + SAU: N = 95 (0 unmatched on SAU).
   + poverty rate: N = 95 (0 unmatched on poverty).
   + population density: N = 95 (0 unmatched on density).

5b. DEVIATION: excluding 4 department(s) with SAU < 10,000 ha (non-agricultural denominator, sales-location artifact — see plan.md Deviations): [{'dept': '75', 'dept_name': 'Paris', 'sau_ha': 1}, {'dept': '93', 'dept_name': 'Seine-Saint-Denis', 'sau_ha': 526}, {'dept': '92', 'dept_name': 'Hauts-de-Seine', 'sau_ha': 5}, {'dept': '94', 'dept_name': 'Val-de-Marne', 'sau_ha': 1039}].
    -> N = 91 after this exclusion.

6. Missing-data check across the four analysis variables (outcome, exposure/normalizer, poverty, density): 0/91 departments (0.0%) have at least one missing value.
   Missingness < 5% threshold (plan.md SS3): complete-case analysis used, excluded departments listed above/below.

7. Complete-case dataset: N = 91.

8. Range/dtype assertions passed for: ['mortality_rate_std', 'pesticide_intensity', 'poverty_rate', 'pop_density'].

9. FINAL analysis dataset saved to data\processed\analysis_df.parquet: N = 91 mainland departments.
