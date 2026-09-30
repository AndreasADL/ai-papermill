# Study 1 diagnostics — the running variable (EXPLORATORY)

## 1. Spacing of consecutive sign crossings
   A retrograde planet crosses the same boundary three times in a few weeks.
   mercury  2,566 crossings, median gap   18.8d,  87.0% of gaps < 35d, min 0.32d
   venus    2,195 crossings, median gap   24.7d,  92.1% of gaps < 35d, min 3.53d
   mars     1,192 crossings, median gap   45.5d,   0.6% of gaps < 35d, min 2.21d

## 2. Tagging each birth by whether its nearest cusp is isolated
   mercury    0.0% of births sit at an isolated cusp (nearest other crossing >= 35d away)
   venus      1.8% of births sit at an isolated cusp (nearest other crossing >= 35d away)
   mars      99.0% of births sit at an isolated cusp (nearest other crossing >= 35d away)

## 3. Density-test failures vs cusp crowding
   density rejected at 29% of 69 cusps overall
     mostly-isolated cusps (>=90% isolated): 26% reject  (n = 19)
     crowded cusps      (<90% isolated): 30% reject  (n = 50)
   VERDICT: the crowding hypothesis is NOT SUPPORTED — isolated and crowded cusps reject at similar rates, so retrograde triple-crossings do not explain the density failures.

## 4. Primary estimates restricted to progressively more isolated cusps
   If the pooled effects are artifacts of truncated support, they should
   shrink toward zero as the threshold rises. If they are real, they
   should survive. The analysis window is capped at half the threshold so
   that the retained window is never truncated by the adjacent crossing.
   mercury  gap>=  10d: pooled -0.00636 [-0.01103, -0.00169], 16 cusps, 3,580,543 people (96.7% of sample)
   mercury  gap>=  15d: pooled -0.00438 [-0.00879, +0.00003], 16 cusps, 2,886,980 people (78.0% of sample)
   mercury  gap>=  20d: pooled -0.00449 [-0.01837, +0.00938], 16 cusps, 371,857 people (10.0% of sample)
   mercury  gap>=  35d: only 0 people (0.0%) — too few to estimate, skipped
   venus    gap>=  10d: pooled -0.00092 [-0.00350, +0.00165], 10 cusps, 3,679,969 people (99.4% of sample)
   venus    gap>=  15d: pooled +0.00002 [-0.00217, +0.00221], 10 cusps, 3,668,912 people (99.1% of sample)
   venus    gap>=  20d: pooled +0.00003 [-0.00216, +0.00222], 10 cusps, 3,641,460 people (98.4% of sample)
   venus    gap>=  35d: pooled +0.00432 [-0.02127, +0.02990],  5 cusps, 66,380 people (1.8% of sample)
   mars     gap>=  10d: pooled -0.00015 [-0.00169, +0.00138], 12 cusps, 3,679,642 people (99.4% of sample)
   mars     gap>=  15d: pooled +0.00044 [-0.00086, +0.00174], 12 cusps, 3,669,520 people (99.1% of sample)
   mars     gap>=  20d: pooled +0.00041 [-0.00073, +0.00156], 12 cusps, 3,669,520 people (99.1% of sample)
   mars     gap>=  35d: pooled +0.00036 [-0.00079, +0.00150], 12 cusps, 3,664,812 people (99.0% of sample)

## 5. Density continuity on isolated cusps only
   27.9% of 68 isolated cusps reject (vs 29.0% over all cusps)

## 6. Local-randomization estimator within +/-3 days (PRE-SPECIFIED)
   Assumption-light: no bandwidth, no functional form, no density continuity.
   mercury  pooled +0.00017 [-0.00181, +0.00214], 16 cusps, 599,417 people; randomization p = 0.8666; TOST EQUIVALENT (rules out OR > 1.012)
   venus    pooled +0.00098 [-0.00014, +0.00209], 9 cusps, 380,406 people; randomization p = 0.0745; TOST inconclusive (rules out OR > 1.063)
   mars     pooled +0.00017 [-0.00054, +0.00089], 12 cusps, 208,574 people; randomization p = 0.6472; TOST inconclusive (rules out OR > 1.110)