# Results — Pesticide sales intensity and female breast cancer mortality, mainland France

Generated programmatically by `analysis/run_all.py` from `results/estimates.json` and `results/robustness.json` — every number below is read from those files, not typed from memory.

## Sample flow (from `analysis/01_clean.py`)

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


---

# Descriptive statistics

N = 91 mainland French departments (after all exclusions — see `sample_flow.md`).

## Table 1. Analysis variables

| Variable                                             |   N |   Missing |    Mean |      SD |    Min |     Max |
|:-----------------------------------------------------|----:|----------:|--------:|--------:|-------:|--------:|
| Breast cancer mortality rate (age-std., /100,000)    |  91 |         0 |  15.366 |   1.357 | 13.018 |  20.765 |
| Pesticide sales intensity, linear (kg a.s./ha/year)  |  91 |         0 |   2.761 |   2.948 |  0.042 |  19.805 |
| Pesticide sales intensity, log (ln kg a.s./ha/year)  |  91 |         0 |   0.578 |   1.008 | -3.174 |   2.986 |
| Poverty rate (%, 2020 vintage)                       |  91 |         0 |  14.137 |   2.595 |  8.9   |  20.7   |
| Population density, linear (inhab/km2, 2011 vintage) |  91 |         0 | 125.87  | 147.585 | 14.93  | 946.94  |
| Population density, log (ln inhab/km2, 2011 vintage) |  91 |         0 |   4.453 |   0.816 |  2.703 |   6.853 |

## Correlation matrix (Pearson r) — primary model variables

|                         |   mortality_rate_std |   log_pesticide_intensity |   poverty_rate |   log_pop_density |
|:------------------------|---------------------:|--------------------------:|---------------:|------------------:|
| mortality_rate_std      |                1     |                     0.164 |          0.156 |             0.087 |
| log_pesticide_intensity |                0.164 |                     1     |          0.198 |             0.486 |
| poverty_rate            |                0.156 |                     0.198 |          1     |            -0.078 |
| log_pop_density         |                0.087 |                     0.486 |         -0.078 |             1     |



---

## H1 (confirmatory, primary)

**Model**: `mortality_rate_std ~ log_pesticide_intensity + poverty_rate + log_pop_density` (OLS, HC3 robust SE), N = 91.

**Finding**: H1 is NOT supported at the pre-specified alpha = .05 threshold: the estimated association between pesticide sales intensity and breast cancer mortality is positive but not statistically significant.

**Statistics sentence**: beta = 0.158, 95% CI [-0.126, 0.443], SE = 0.145, t(87) = 1.092, p = 0.2748, standardized beta = 0.118, partial r = 0.101 [-0.110, 0.303] (p = 0.3477, classical/non-HC3), N = 91.

Note: the coefficient's p-value uses HC3-robust inference; the partial correlation's p-value uses classical (non-HC3) Pearson-based inference, so the two can differ slightly even though they test the same underlying association.

**Mandatory power caveat (plan.md SS5)**: at the achieved sample size (N = 91, residual df = 87), this design has 80% power to detect a minimum effect of partial r ~= 0.288 (Cohen's f2 ~= 0.090). The observed partial r (0.101) is BELOW this threshold. Per the pre-registered interpretation rule, this null/non-significant H1 result must be reported as **"no effect detected above partial r ~= 0.288"** — NOT as evidence of no association — because the design is underpowered relative to the smallest comparable prior finding (Reynolds et al. 2004, area-level design).

Full model fit: R2 = 0.044, adj. R2 = 0.011, F(3,87) = 1.056, p = 0.3721.

Other predictors in the model:

- `poverty_rate`: coef = 0.071, 95% CI [-0.073, 0.215], p = 0.3342

- `log_pop_density`: coef = 0.067, 95% CI [-0.427, 0.562], p = 0.7894


See `results/figures/fig1_scatter_pesticide_mortality.png` for the bivariate visualization (N in caption) and `results/diagnostics.md` for full diagnostic detail.


---

# Diagnostics — H1 primary model

Formula: `mortality_rate_std ~ log_pesticide_intensity + poverty_rate + log_pop_density` (HC3 robust SE), N = 91.

**Linearity**: partial-residual plot saved to `results\figures\diagnostic_partial_residual.png` (visual check, see figure).

**Breusch-Pagan**: LM = 17.464, p = 0.0006 (heteroskedastic at alpha=.05). HC3 robust SEs used as baseline regardless of result.

**Shapiro-Wilk**: W = 0.9448, p = 0.0007 (non-normal residuals at alpha=.05). Q-Q plot: `results\figures\diagnostic_qq.png`.

**VIF**: {'log_pesticide_intensity': 1.413596194420669, 'poverty_rate': 1.0857192359633434, 'log_pop_density': 1.3665186916137113} (all < 5, no multicollinearity concern).

**Cook's distance**: threshold 4/n = 0.0440, 5 department(s) flagged: [{'dept': '59', 'dept_name': 'Nord'}, {'dept': '66', 'dept_name': 'Pyrénées-Orientales'}, {'dept': '83', 'dept_name': 'Var'}, {'dept': '06', 'dept_name': 'Alpes-Maritimes'}, {'dept': '62', 'dept_name': 'Pas-de-Calais'}]. Sensitivity refit excluding them: {'n': 86, 'excluded_n': 5, 'log_pesticide_intensity': {'coef': 0.27014242968342855, 'se': 0.11984748206926474, 't': 2.254051774965971, 'p': 0.024192910999603058, 'ci_low': 0.03524568118985977, 'ci_high': 0.5050391781769974}}.

**Heavy-tailed contingency triggered** (Shapiro-Wilk p < .05): Huber-T robust regression coef = 0.1914 (p = 0.1944); Spearman rho (raw bivariate) = 0.1851 (p = 0.0791).

**Moran's I** (Queen contiguity, N=91, 1 island department(s): ['20']): I = 0.8293, E[I] = -0.0111, p (999-permutation) = 0.0010 (SIGNIFICANT at alpha=.05).

**I = 0.8293 is far above the range typically seen for genuine areal disease-risk clustering (~0.2-0.5 in the epidemiological literature).** lambda = 0.969 paired with a low spatial-error pseudo-R2 (0.021) is more consistent with an artifact of the outcome's own model-smoothed construction (see `data/candidates.md` candidate 2A) than with a true omitted spatial confounder. The spatial-lag/error coefficients below are reported as exploratory and model-dependent, not as a validated spatial correction — see `results/results.md` E3 for the full discussion.

**Spatial-lag/error contingency triggered**: {'spatial_lag': {'pesticide_coef': {'coef': 0.11193502946421659, 'se': 0.1309786486653563, 'z': 0.8546051635500136, 'p': 0.39276976807359254, 'ci_low': -0.1447831219198818, 'ci_high': 0.36865318084831494}, 'rho': 0.3839604784903083, 'pseudo_r2': 0.3935040329743963}, 'spatial_error': {'pesticide_coef': {'coef': 0.08042786490463438, 'se': 0.05527519100654867, 'z': 1.4550445405987973, 'p': 0.14565693113423103, 'ci_low': -0.027911509468201007, 'ci_high': 0.18876723927746977}, 'lambda': 0.9694232574071897, 'pseudo_r2': 0.02069556056176412}}


---

## Robustness checks (plan.md SS7)

H1 primary pesticide coefficient (for comparison): 0.158 (p = 0.2748, N = 91).

| Check | Coef | 95% CI | p | N |
|---|---|---|---|---|
| H1 primary (sales-based, log exposure) | 0.158 | [-0.126, 0.443] | 0.2748 | 91 |
| 1. Purchase-based exposure | 0.276 | [0.012, 0.541] | 0.0404 | 91 |
| 2. Linear (non-log) exposure | -0.045 | [-0.158, 0.067] | 0.4315 | 91 |
| 4a. Spatial lag (vs. OLS) | 0.112 | [-0.145, 0.369] | 0.3928 | 91 |
| 4b. Spatial error (vs. OLS) | 0.080 | [-0.028, 0.189] | 0.1457 | 91 |

See `results/figures/fig2_robustness_forest.png` for a visual summary and `results/robustness.md` for full detail.


---

## Exploratory (labeled exploratory per plan.md SS1 — not subject to the confirmatory alpha; nominal/uncorrected p-values shown for reference only)

### E1 — Purchase-based exposure (buyer postal code, 2013-2023)

Coef = 0.276, 95% CI [0.012, 0.541], p = 0.0404, N = 91. Direction MATCHES the H1 primary (sales-based) direction. Purchase-based (buyer postal code, 2013-2023) exposure in place of distributor-sales-based exposure (2008-2014); same mortality outcome and confounders.


### E2 — FRANCIM observed incidence (2018-2022), registry departments

Coef = 0.441, 95% CI [-1.892, 2.774], p = 0.7112 (NOT independently powered — sign/direction only, per plan.md SS5), N = 19 registry departments: 14, 16, 17, 21, 25, 33, 34, 38, 44, 50, 59, 67, 68, 79, 80, 81, 85, 86, 87. Direction MATCHES the H1 primary direction.


### E3 — Spatial autocorrelation (Moran's I) and spatial-model comparison

Moran's I on H1 residuals (Queen contiguity, N = 91, 1 island department excluded from the weights graph: ['20']): I = 0.8293, expected I = -0.0111, p (999-permutation) = 0.0010 — **SIGNIFICANT** at alpha = .05.

**I = 0.8293 is far above the range expected from genuine areal disease-risk clustering (typically ~0.2-0.5 in the epidemiological literature).** The spatial-error model's lambda = 0.969 (neighboring residuals almost perfectly predict each other) combined with a very low spatial-error pseudo-R2 (0.021) is more consistent with an artifact of the outcome's own construction than with a real omitted spatial confounder: `mortality_rate_std` is a **model-smoothed** InVS/Francim estimate, not a raw registry count (see `data/candidates.md` candidate 2A) — spatial smoothing applied at the outcome's own estimation stage would mechanically inflate Moran's I on any downstream residuals, independent of true geographic clustering in breast-cancer risk. Because of this, the spatial-lag/error coefficients below should be read as **exploratory and model-dependent under an assumption (a spatial autoregressive process on the true outcome) that may not match this outcome's actual construction (a smoothing algorithm applied before we ever see the data)** — not as a validated correction for omitted spatial confounding.

With that caveat, the pre-specified spatial-lag/error contingency was triggered: spatial-lag pesticide coef = 0.112 (p = 0.3928); spatial-error pesticide coef = 0.080 (p = 0.1457) — both attenuated relative to the OLS estimate (0.158) and both remain non-significant, so this does not overturn the primary null finding — but given the likely smoothing artifact, that consistency should not be over-read as independent confirmation either.


---

## Limitations and deviations from plan.md

See `data/provenance.md` for full detail. Summary:

1. **SAU normalizer**: RA2020 vintage used in place of the planned RA2010 vintage (only vintage available via the confirmed working Observatoire-des-Territoires endpoint after reasonable effort).

2. **Poverty rate vintage**: 2020 used in place of the planned ~2012 vintage (same reason; INSEE's own direct FiLoSoFi files for ~2012-2016 are commune-level only, not a ready department aggregate).

3. **Non-agricultural department exclusion**: Paris (75), Hauts-de-Seine (92), Seine-Saint-Denis (93) and Val-de-Marne (94) excluded due to near-zero SAU denominators producing implausible pesticide-intensity outliers (a sales-location/distributor-headquarters artifact, not true agricultural intensity) — decided without reference to outcome values (the exclusion rule reads only `sau_ha`, never `mortality_rate_std`), though the outcome column was already merged into the working dataframe by that step.

4. **Corsica department-code handling**: 2A/2B aggregated to a single unified '20' row (sum for extensive quantities, unweighted mean for rates) to match the outcome data's coding.

5. **Moran's I / spatial-model interpretation**: the significant spatial autocorrelation (I = 0.83) detected in H1 residuals is unusually high for genuine areal disease clustering and more likely reflects the outcome's own model-smoothed construction (InVS/Francim spatiotemporal estimates borrow statistical strength across neighboring departments at the estimation stage) than a true omitted spatial confounder — see the E3 section above. The spatial-lag/error coefficients are reported as exploratory and model-dependent, not as a validated correction.


Full deviation justifications are logged in `analysis/plan.md`'s Deviations section.
