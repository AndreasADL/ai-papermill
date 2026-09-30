# Study 2 — Mercury retrograde and daily event rates

Seed 20260918. Primary inference: circular block permutation (10,000 shifts). Regression companion: OLS with Newey-West HAC SEs (lag 14).

BTS daily series: 9,132 days, 2000-01-01 .. 2024-12-31
Total flights: 159,638,862

Mercury retrograde periods 2000-2024: 85 (3.40/yr; canonical ~3.2/yr)
  mean duration: 22.2 days
  mean retrograde+shadow span: 56.1 days
  2024 validation (computed vs published astrological sources):
    rx 2024-04-01 -> 2024-04-25, shadow 2024-03-19 -> 2024-05-13   PASS
    rx 2024-08-05 -> 2024-08-28, shadow 2024-07-17 -> 2024-09-11   PASS
    rx 2024-11-26 -> 2024-12-15, shadow 2024-11-07 -> 2025-01-03   PASS
  days in retrograde:          1,753 (19.2% of the series)
  days in retrograde + shadow: 4,420 (48.4%)

## Confirmatory tests

  H2-a: delay_share ~ retrograde (base rate 19.30%, SESOI 0.50 pp)
    regression (HAC): +0.00048 [-0.00571, +0.00666], p = 0.880
    PERMUTATION (primary): observed diff +0.00048, p = 0.8904 (one-sided higher: 0.4031)
    TOST vs +/-0.0050: p = 0.07584 -> not equivalent
    BF01 = 2.02 (data insensitive (not evidence of absence))
    Beta-Binomial BF01 (supplementary, plan §2.3 proportion recipe): 0.247 uniform / 0.308 Jeffreys / 0.261 Beta(2,2); p_rx = 0.19632 vs p_other = 0.19668

  H2-b: cancel_share ~ retrograde (base rate 1.99%, SESOI 0.10 pp)
    regression (HAC): -0.00220 [-0.00590, +0.00150], p = 0.243
    PERMUTATION (primary): observed diff -0.00219, p = 0.3721 (one-sided higher: 0.8374)
    TOST vs +/-0.0010: p = 0.7376 -> not equivalent
    BF01 = 1.09 (data insensitive (not evidence of absence))
    Beta-Binomial BF01 (supplementary, plan §2.3 proportion recipe): 0 uniform / 0 Jeffreys / 0 Beta(2,2); p_rx = 0.01809 vs p_other = 0.01994

  H2-c: delay_share ~ retrograde_shadow (base rate 19.30%, SESOI 0.50 pp)
    regression (HAC): +0.00308 [-0.00233, +0.00850], p = 0.264
    PERMUTATION (primary): observed diff +0.00307, p = 0.2862 (one-sided higher: 0.1526)
    TOST vs +/-0.0050: p = 0.2438 -> not equivalent
    BF01 = 1.49 (data insensitive (not evidence of absence))
    Beta-Binomial BF01 (supplementary, plan §2.3 proportion recipe): 1.65e-89 uniform / 2.06e-89 Jeffreys / 1.74e-89 Beta(2,2); p_rx = 0.19729 vs p_other = 0.19597

  H2-c-cancel: cancel_share ~ retrograde_shadow (base rate 1.99%, SESOI 0.10 pp)
    regression (HAC): +0.00085 [-0.00275, +0.00444], p = 0.644
    PERMUTATION (primary): observed diff +0.00084, p = 0.7961 (one-sided higher: 0.3961)
    TOST vs +/-0.0010: p = 0.4669 -> not equivalent
    BF01 = 1.29 (data insensitive (not evidence of absence))
    Beta-Binomial BF01 (supplementary, plan §2.3 proportion recipe): 0 uniform / 0 Jeffreys / 0 Beta(2,2); p_rx = 0.02055 vs p_other = 0.01868

## H2-d — equity volatility (secondary)
  N = 6,309 trading days, 2000-01-03 .. 2024-12-31
  log(VIX) effect: +0.00759 [-0.02856, +0.04375], HAC p = 0.681
  PERMUTATION p = 0.8754; TOST vs +/-0.02: not equivalent

## Robustness
  Excluding 2020-2021 (COVID): diff -0.00070, permutation p = 0.7995, N = 8,401
  Volume-weighted: +0.00041 (p = 0.895)