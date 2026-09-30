# Study 1 — Zodiac-cusp regression discontinuity

Seed 20260918. Estimator: rdrobust local-linear, triangular kernel, vce=hc1, robust bias-corrected inference.

Analysis frame: 4,407,456 people (Wikidata, day-precision DOB, 1852-2020)
Restricted to people with >=1 coded occupation: 3,701,431 (84.0%)
  mercury  24 cusps, 16 dignity-relevant (pooled),  8 neutral (excluded from primary)
  venus    22 cusps, 11 dignity-relevant (pooled), 11 neutral (excluded from primary)
  mars     24 cusps, 12 dignity-relevant (pooled), 12 neutral (excluded from primary)

## Positive controls (plan §4.1)
  (a) Relative-age effect, athletes: OR(Q1 vs Q4) = 1.199 [1.191, 1.207], n = 847,135
  (b) Birth seasonality (heaped days excluded): first-harmonic amplitude 4.32% of mean daily births, peak day-of-year 33
      (raw, including heaps: 4.47%, peak day-of-year 1)
  -> positive controls PASS

## Primary confirmatory tests (H1-Me, H1-Ve, H1-Ma)

  H1-Me (mercury, base rate 18.67%, SESOI = +0.00752 pp on the probability scale)
    pooled signed RD = -0.00485 [-0.00858, -0.00113], p = 0.011, 16 cusps, N = 1,077,174
    TOST vs +/-0.00752: p = 0.0803 -> not equivalent
    BF01 = 0.24 (moderate evidence for an effect); directional BF01 = 12.89
    heterogeneity across cusps: Q = 73.2, p = 1.2e-09, I2 = 80%
    random-effects companion: -0.00352 [-0.01320, +0.00616] -> not equivalent

  H1-Ve (venus, base rate 3.11%, SESOI = +0.00150 pp on the probability scale)
    pooled signed RD = +0.00011 [-0.00207, +0.00230], p = 0.918, 10 cusps, N = 652,611
    TOST vs +/-0.00150: p = 0.1067 -> not equivalent
    BF01 = 1.86 (data insensitive (not evidence of absence)); directional BF01 = 1.76
    heterogeneity across cusps: Q = 5.7, p = 0.766, I2 = 0%
    random-effects companion: +0.00011 [-0.00207, +0.00230] -> not equivalent

  H1-Ma (mars, base rate 0.71%, SESOI = +0.00035 pp on the probability scale)
    pooled signed RD = +0.00036 [-0.00078, +0.00149], p = 0.541, 12 cusps, N = 552,064
    TOST vs +/-0.00035: p = 0.5024 -> not equivalent
    BF01 = 1.29 (data insensitive (not evidence of absence)); directional BF01 = 1.05
    heterogeneity across cusps: Q = 19.3, p = 0.0566, I2 = 43%
    random-effects companion: +0.00067 [-0.00108, +0.00242] -> not equivalent

## Exploratory — Sun sign and leadership occupations
  (H1-Su was dropped from the confirmatory family at GATE 1: Ptolemy IV.4
   assigns occupation to Mars, Venus and Mercury only. See hypotheses.py.)
  36 solar cusp x outcome fits, bandwidth capped at h <= 7 days (plan §0); mean |t| = 0.74

## Falsification and robustness (plan §4)

  Placebo cutoffs (shifted +/-10, +/-20 days; should centre on zero)
    mercury  offset -20d: pooled = +0.00639 [-0.00505, +0.01783]
    mercury  offset -10d: pooled = -0.00518 [-0.01131, +0.00096]
    mercury  offset +10d: pooled = -0.00270 [-0.00862, +0.00323]
    mercury  offset +20d: pooled = -0.00809 [-0.02091, +0.00472]
    venus    offset -20d: pooled = +0.00327 [-0.00295, +0.00949]
    venus    offset -10d: pooled = +0.00091 [-0.00162, +0.00344]
    venus    offset +10d: pooled = -0.00076 [-0.00325, +0.00172]
    venus    offset +20d: pooled = -0.00143 [-0.00412, +0.00125]
    mars     offset -20d: pooled = -0.00016 [-0.00156, +0.00124]
    mars     offset -10d: pooled = +0.00006 [-0.00112, +0.00125]
    mars     offset +10d: pooled = -0.00039 [-0.00162, +0.00083]
    mars     offset +20d: pooled = -0.00052 [-0.00183, +0.00079]
    -> placebo rejection rate 11.4% of 245 fits (nominal 5%)

  Density tests (rddensity; a jump indicates a data artifact)
    29.0% of 69 cusps reject density continuity at .05

  Specification robustness (pooled estimates)
    mercury  primary -0.00485 | donut_1day=-0.00644 drop_heaped_days=-0.00462 h3=-0.00564 h7=-0.00566 h21=-0.00176
    venus    primary +0.00011 | donut_1day=+0.00596 drop_heaped_days=+0.00120 h3=-0.00284 h7=-0.00028 h21=+0.00192
    mars     primary +0.00036 | donut_1day=+0.00019 drop_heaped_days=+0.00009 h3=-0.00070 h7=+0.00025 h21=+0.00032

  Covariate balance at the cutoff (a jump here invalidates the design)
    citizenship region available for 84.0% of the sample; testing balance on indicators for Europe, North America, Asia
    mercury  is_male        jump = -0.00062 (SD 0.421), p = 0.759
    mercury  birth_year     jump = +0.92971 (SD 38.753), p = 0.000
    mercury  log_sitelinks  jump = +0.00054 (SD 0.819), p = 0.888
    mercury  region_europe  jump = +0.00183 (SD 0.500), p = 0.437
    mercury  region_north_america jump = -0.00308 (SD 0.347), p = 0.057
    mercury  region_asia    jump = +0.00154 (SD 0.328), p = 0.309
    venus    is_male        jump = +0.00270 (SD 0.421), p = 0.332
    venus    birth_year     jump = +0.02993 (SD 38.753), p = 0.761
    venus    log_sitelinks  jump = -0.00702 (SD 0.819), p = 0.146
    venus    region_europe  jump = -0.00068 (SD 0.500), p = 0.827
    venus    region_north_america jump = -0.00227 (SD 0.347), p = 0.257
    venus    region_asia    jump = -0.00150 (SD 0.328), p = 0.473
    mars     is_male        jump = -0.00223 (SD 0.421), p = 0.427
    mars     birth_year     jump = +0.93620 (SD 38.753), p = 0.002
    mars     log_sitelinks  jump = +0.00441 (SD 0.819), p = 0.430
    mars     region_europe  jump = -0.00224 (SD 0.500), p = 0.510
    mars     region_north_america jump = +0.00177 (SD 0.347), p = 0.462
    mars     region_asia    jump = -0.00109 (SD 0.328), p = 0.620