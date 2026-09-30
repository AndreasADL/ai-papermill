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

