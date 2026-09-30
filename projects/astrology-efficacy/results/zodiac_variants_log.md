# Zodiac variants — tropical vs sidereal vs actual sky (EXPLORATORY)

NOT pre-registered. Hypotheses are unchanged and still come from the frozen
hypotheses.py; only the sign-boundary definition varies.

## Ayanamsa, computed from Spica's actual apparent position
   1850: 21.7558 deg   2020: 24.1281 deg
   J2000 computed 23.84943 deg vs published Lahiri 23.85306 deg (difference -0.22 arcmin)
   quadratic fit max residual: 19.16 arcsec (one day of solar motion is 3600 arcsec)

Analysis sample: 3,701,431 people with >=1 coded occupation

## Building the sidereal zodiac
   mercury  2,568 crossings,  24 cusp types,  16 dignity-relevant  (7s)
   venus    2,191 crossings,  22 cusp types,  11 dignity-relevant  (7s)
   mars     1,186 crossings,  23 cusp types,  12 dignity-relevant  (7s)

## Building the iau zodiac
   mercury  2,942 crossings,  27 cusp types,  16 dignity-relevant  (7s)
   venus    2,447 crossings,  26 cusp types,  12 dignity-relevant  (7s)
   mars     1,313 crossings,  26 cusp types,  12 dignity-relevant  (7s)

   Ophiuchus appears in 11.3% of Mercury's nearest-cusp labels — a constellation with no astrological sign, so those cusps are dignity-neutral and excluded from pooling.

## Pooled directional estimates under each zodiac
   Primary estimator: local randomization (+/-3 days), per 08_diagnostics.py.
   Positive = the direction astrology predicts.

   MERCURY  (base rate 18.67%)
     tropical  +0.00017 [-0.00181, +0.00214]  randomization p = 0.8666  16 cusps  N =   599,417  rules out OR > 1.012
     sidereal  +0.00016 [-0.00180, +0.00213]  randomization p = 0.8726  16 cusps  N =   604,326  rules out OR > 1.012
     iau       +0.00071 [-0.00112, +0.00255]  randomization p = 0.4418  16 cusps  N =   706,875  rules out OR > 1.015

   VENUS  (base rate 3.11%)
     tropical  +0.00098 [-0.00014, +0.00209]  randomization p = 0.0745   9 cusps  N =   380,406  rules out OR > 1.063
     sidereal  -0.00066 [-0.00174, +0.00043]  randomization p = 0.2444  11 cusps  N =   384,881  rules out OR > 1.052
     iau       -0.00064 [-0.00167, +0.00038]  randomization p = 0.2279  12 cusps  N =   441,874  rules out OR > 1.050

   MARS  (base rate 0.71%)
     tropical  +0.00017 [-0.00054, +0.00089]  randomization p = 0.6472  12 cusps  N =   208,574  rules out OR > 1.110
     sidereal  -0.00043 [-0.00115, +0.00029]  randomization p = 0.2354  12 cusps  N =   207,355  rules out OR > 1.147
     iau       -0.00081 [-0.00148, -0.00014]  randomization p = 0.0200  12 cusps  N =   244,725  rules out OR > 1.196

## Which zodiac performs better?
   mercury  smallest randomization p: iau (p = 0.4418, estimate +0.00071)
   venus    smallest randomization p: tropical (p = 0.0745, estimate +0.00098)
   mars     smallest randomization p: iau (p = 0.0200, estimate -0.00081)

   Across all 9 zodiac x planet tests, 1 reached p < .05.
   Expected by chance alone at alpha = .05: 0.5.
   The pre-registered placebo battery (plan §4.2) rejected at 11.4% on cutoffs known to be meaningless, which is the reference rate any 'winner' here must beat.