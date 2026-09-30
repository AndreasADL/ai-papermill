# Robustness checks (plan.md SS7)

H1 primary pesticide coefficient: 0.1585 (p = 0.2748, N = 91), direction: positive.

## Summary table

| Check                                    |   Coef (pesticide) |      p |   N | Sign matches H1   |
|:-----------------------------------------|-------------------:|-------:|----:|:------------------|
| H1 primary (sales, log)                  |             0.1585 | 0.2748 |  91 | True              |
| 1. Purchase-based exposure               |             0.2765 | 0.0404 |  91 | True              |
| 2. Linear (non-log) exposure             |            -0.0452 | 0.4315 |  91 | False             |
| 3. FRANCIM incidence E2 (direction only) |             0.4407 | 0.7112 |  19 | True              |
| 4a. Spatial lag                          |             0.1119 | 0.3928 |  91 | True              |
| 4b. Spatial error                        |             0.0804 | 0.1457 |  91 | True              |

## Detail

### check_1_purchase_based_exposure

```json
{
  "n": 91,
  "coef": 0.27647491444462036,
  "se": 0.1349138377329916,
  "t": 2.049270253447187,
  "p": 0.040435695711969664,
  "ci_low": 0.012048651471875838,
  "ci_high": 0.5409011774173649,
  "r_squared": 0.06547140686272335,
  "description": "Purchase-based (buyer postal code, 2013-2023) exposure in place of distributor-sales-based exposure (2008-2014); same mortality outcome and confounders."
}
```

### check_2_linear_exposure

```json
{
  "n": 91,
  "coef": -0.04520807674469113,
  "se": 0.05747280562158018,
  "t": -0.7865994404789624,
  "p": 0.43151638692078975,
  "ci_low": -0.15785270585345945,
  "ci_high": 0.06743655236407718,
  "r_squared": 0.041455736876185534,
  "description": "Linear (non-log) pesticide_intensity in place of log-transformed primary specification."
}
```

### check_3_francim_incidence_e2

```json
{
  "n": 19,
  "coef": 0.44074865971474075,
  "se": 1.1902822941037239,
  "t": 0.3702891842532381,
  "p": 0.7111670317139066,
  "ci_low": -1.8921617681642702,
  "ci_high": 2.7736590875937517,
  "r_squared": 0.3310766144124314,
  "description": "FRANCIM observed incidence (2018-2022), registry departments, paired with BNV-D sales 2018-2022 and RA2020 SAU. SIGN/DIRECTION CONSISTENCY CHECK ONLY per the plan.md SS5 power analysis (N too small for an independently powered test) — not interpreted on significance.",
  "departments_used": [
    "14",
    "16",
    "17",
    "21",
    "25",
    "33",
    "34",
    "38",
    "44",
    "50",
    "59",
    "67",
    "68",
    "79",
    "80",
    "81",
    "85",
    "86",
    "87"
  ]
}
```

### check_4_spatial_model_comparison

```json
{
  "ols": {
    "coef": 0.15846429097347126,
    "p": 0.2748459055754008,
    "n": 91
  },
  "moran_i_significant": true,
  "spatial_lag": {
    "coef": 0.11193502946421659,
    "se": 0.1309786486653563,
    "z": 0.8546051635500136,
    "p": 0.39276976807359254,
    "ci_low": -0.1447831219198818,
    "ci_high": 0.36865318084831494
  },
  "spatial_error": {
    "coef": 0.08042786490463438,
    "se": 0.05527519100654867,
    "z": 1.4550445405987973,
    "p": 0.14565693113423103,
    "ci_low": -0.027911509468201007,
    "ci_high": 0.18876723927746977
  },
  "description": "OLS vs. spatial-lag/error pesticide coefficient, triggered because Moran's I on H1 residuals was significant (see results/diagnostics.md)."
}
```


**Overall**: sign of the pesticide coefficient matches the H1 primary direction in 4/5 robustness checks (excluding the H1 row itself; check 3/FRANCIM E2 counted for direction only, per its pre-specified power caveat). 1/5 robustness/sensitivity specifications reach p < .05: 1. Purchase-based exposure (p=0.0404). The H1 primary specification itself is non-significant (p = 0.2748); the fact that one alternative specification (purchase-based exposure) crosses the nominal .05 threshold while the primary, pre-registered specification does not is reported here at face value, not treated as confirmatory — H1's pre-specified inference criterion (plan.md SS4) is the primary model only.
