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
