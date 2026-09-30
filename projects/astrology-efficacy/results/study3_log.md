# Study 3 — Sun sign, sociability, and self-attribution

Seed 20260918. WLS with GSS weights (wtssps), year fixed effects, SEs clustered on PSU within stratum.

GSS cumulative file: 75,699 respondents, 1972-2024
Analysis sample (valid sign + sociability composite): 39,125
Design variables missing for 0.0% of the sample

## H3-a — main effect of odd ('positive') vs even sign
  d = +0.0101 [-0.0143, +0.0344], p = 0.417, N = 39,125 (6,337 clusters)
  TOST vs +/-0.1: p = 2.213e-13 -> EQUIVALENT
  BF01 = 5.38 (moderate evidence for the null)

## H3-b — sign x belief interaction (the discriminating test)
  Astrology predicts a NULL interaction; self-attribution predicts a POSITIVE one.

  Primary belief measure: astrolgy (ever read a horoscope), N = 5,971
  NOTE: the GATE 1 plan cited joint zodiac x astrolgy N = 8,531. The sociability
  items sit on a different ballot rotation, so the realized moderation sample is
  5,971. Logged as a deviation; the equivalence test is still powered (see below).
  interaction d = -0.0124 [-0.1311, +0.1064], p = 0.838, N = 5,971
  TOST vs +/-0.1: p = 0.07397 -> not equivalent
  BF01 = 2.06 (data insensitive (not evidence of absence))
    simple slope, believers (read horoscopes)  d = +0.0093 [-0.0760, +0.0946], N = 2,919
    simple slope, non-believers                d = +0.0220 [-0.0623, +0.1064], N = 3,052

  Pre-registered replication with astrosci (ordinal), N = 5,791
  interaction = +0.0487 [-0.0525, +0.1498], p = 0.346; TOST p = 0.16 -> not equivalent

## Robustness
  H3-a with wtssall weight: d = -0.0043 (primary +0.0101)
  H3-a unweighted:            d = +0.0100
  H3-a on the H3-b subsample: d = +0.0157 (N = 5,971)
  H3-a, all four items answered: d = +0.0098 (N = 38,890, 99.4% of the sample; TOST equivalent)
  H3-b, all four items answered: interaction -0.0179 (N = 5,962)

## Exploratory (NOT confirmatory — labelled as such in all outputs)
  Water sign -> happiness (proxy for emotionality): b = +0.0002, p = 0.982, N = 59,871
  Omnibus test of all 12 signs: F(11.0, .) = 0.85, p = 0.586