"""
inference.py — The dual-inference machinery required by analysis/plan.md §2.

Every primary test must report (i) estimate + 95% CI, (ii) a TOST equivalence test
against the pre-registered SESOI, and (iii) a Bayes factor with a stated prior and a
prior-sensitivity curve. Reporting only one is not permitted (plan §2.1).

Nothing here depends on any outcome; this module is pure statistics.
"""

from __future__ import annotations

import numpy as np
from scipy import integrate, special, stats

SEED = 20260918  # plan.md line 6


# ---------------------------------------------------------------------------
# Effect-size scale conversion
# ---------------------------------------------------------------------------
def or_to_risk_difference(odds_ratio: float, base_rate: float) -> float:
    """
    Convert an odds ratio to the risk difference it implies at a given base rate.

    The SESOI is pre-registered on the odds-ratio scale (OR = 1.05, anchored to the
    Davies et al. 2003 season-of-birth effect of OR = 1.07), but an RDD on a binary
    outcome estimates a difference in probabilities. The two are only equivalent once
    the base rate is fixed, so the conversion is done per outcome rather than assumed.
    """
    odds = base_rate / (1.0 - base_rate)
    p1 = (odds * odds_ratio) / (1.0 + odds * odds_ratio)
    return p1 - base_rate


# ---------------------------------------------------------------------------
# Frequentist equivalence (TOST)
# ---------------------------------------------------------------------------
def tost(estimate: float, se: float, sesoi: float) -> dict:
    """
    Two one-sided tests of equivalence against the interval [-sesoi, +sesoi].

    p_tost < .05 means effects as large as the SESOI are rejected in BOTH directions:
    the headline "effects larger than X are ruled out" claim of plan §2.2. It is NOT
    the same as failing to reject zero, which is why the plan requires it.
    """
    if not np.isfinite(se) or se <= 0:
        return {"p_tost": np.nan, "equivalent": False,
                "p_lower": np.nan, "p_upper": np.nan, "sesoi": sesoi}
    # H0_lower: theta <= -sesoi   (reject if estimate is far enough ABOVE -sesoi)
    p_lower = stats.norm.sf((estimate + sesoi) / se)
    # H0_upper: theta >= +sesoi   (reject if estimate is far enough BELOW +sesoi)
    p_upper = stats.norm.cdf((estimate - sesoi) / se)
    p_tost = float(max(p_lower, p_upper))
    return {"p_tost": p_tost, "equivalent": bool(p_tost < 0.05),
            "p_lower": float(p_lower), "p_upper": float(p_upper), "sesoi": float(sesoi)}


def equivalence_bound(estimate: float, se: float, alpha: float = 0.05) -> float:
    """
    The SMALLEST symmetric bound against which this estimate would pass TOST.

    This is the plan's headline quantity (§2.2): rather than reporting "no effect",
    report the effect size that the data DO rule out. Inverting TOST gives
    delta_min = |estimate| + z_(1-alpha) * se: any true effect larger than this is
    rejected at alpha, one-sided in each direction.
    """
    if not np.isfinite(se) or se <= 0:
        return np.nan
    return float(abs(estimate) + stats.norm.ppf(1 - alpha) * se)


def risk_difference_to_or(rd: float, base_rate: float) -> float:
    """Inverse of `or_to_risk_difference`: express a risk difference as an odds ratio."""
    p1 = base_rate + rd
    if not (0 < p1 < 1) or not (0 < base_rate < 1):
        return np.nan
    return float((p1 / (1 - p1)) / (base_rate / (1 - base_rate)))


def two_sided_p(estimate: float, se: float) -> float:
    """Conventional two-sided z test against zero."""
    if not np.isfinite(se) or se <= 0:
        return np.nan
    return float(2.0 * stats.norm.sf(abs(estimate / se)))


# ---------------------------------------------------------------------------
# Bayes factors
# ---------------------------------------------------------------------------
def bf01_normal_likelihood(estimate: float, se: float, scale: float,
                           prior: str = "cauchy", one_sided: int = 0) -> float:
    """
    BF01 (evidence for the null) by Savage-Dickey, treating the estimate as normal.

    H0: theta = 0
    H1: theta ~ Cauchy(0, scale)  [default, per plan §2.3] or Normal(0, scale)

    `one_sided`: 0 for a two-sided H1; +1 or -1 to restrict H1 to the pre-registered
    direction (a half-prior). The directional version is the one the hypotheses
    actually make, and it is the stricter test of astrology: a directional H1 is
    easier to support, so a BF01 favouring the null under it is more telling.

    Returns BF01 = P(data | H0) / P(data | H1). BF01 >= 3 is "moderate evidence for
    the null", >= 10 "strong"; 1/3 < BF01 < 3 is data insensitivity, NOT evidence of
    absence (Dienes 2014; plan §2.3).
    """
    if not np.isfinite(se) or se <= 0 or scale <= 0:
        return np.nan

    m0 = stats.norm.pdf(estimate, loc=0.0, scale=se)

    if prior == "normal":
        if one_sided == 0:
            m1 = stats.norm.pdf(estimate, loc=0.0, scale=np.hypot(se, scale))
        else:
            # Half-normal prior on the predicted side.
            def integrand(theta):
                return (stats.norm.pdf(estimate, loc=theta, scale=se)
                        * 2.0 * stats.norm.pdf(theta, loc=0.0, scale=scale))
            lo, hi = (0.0, np.inf) if one_sided > 0 else (-np.inf, 0.0)
            m1, _ = integrate.quad(integrand, lo, hi, limit=200)
    elif prior == "cauchy":
        def integrand(theta):
            return (stats.norm.pdf(estimate, loc=theta, scale=se)
                    * stats.cauchy.pdf(theta, loc=0.0, scale=scale))
        if one_sided == 0:
            m1, _ = integrate.quad(integrand, -np.inf, np.inf, limit=200)
        else:
            lo, hi = (0.0, np.inf) if one_sided > 0 else (-np.inf, 0.0)
            m1, _ = integrate.quad(lambda t: 2.0 * integrand(t), lo, hi, limit=200)
    else:
        raise ValueError(f"unknown prior {prior!r}")

    if m1 <= 0 or not np.isfinite(m1):
        return np.nan
    return float(m0 / m1)


def bf_prior_sensitivity(estimate: float, se: float, unit_scale: float,
                         r_grid=(0.1, 0.25, 0.5, 0.707, 1.0, 1.25, 1.5),
                         prior: str = "cauchy", one_sided: int = 0) -> dict:
    """
    Prior-sensitivity curve, required for every primary test by plan §2.3.

    The prior scale is expressed in SESOI units: scale = r * unit_scale, so r = 0.707
    (the JZS default of Rouder et al. 2009) places half the prior mass within 0.707
    SESOIs of zero. This keeps the prior on the same substantive scale as the
    equivalence bound rather than on an arbitrary raw scale.
    """
    return {f"r={r}": bf01_normal_likelihood(estimate, se, r * unit_scale,
                                             prior=prior, one_sided=one_sided)
            for r in r_grid}


def bf01_beta_binomial(k1: int, n1: int, k2: int, n2: int,
                       a: float = 1.0, b: float = 1.0) -> float:
    """
    BF01 for two independent proportions, Beta-Binomial with a Beta(a, b) prior
    on each side (plan §2.3: uniform Beta(1,1) primary; Beta(0.5,0.5), Beta(2,2)
    as robustness).

    H0: p1 = p2 = p, p ~ Beta(a, b)
    H1: p1 ~ Beta(a, b), p2 ~ Beta(a, b) independently

    Exact, computed in log space via the Beta function.
    """
    def lbeta(x, y):
        return special.betaln(x, y)

    if min(n1, n2) <= 0:
        return np.nan
    log_m0 = lbeta(a + k1 + k2, b + (n1 - k1) + (n2 - k2)) - lbeta(a, b)
    log_m1 = ((lbeta(a + k1, b + n1 - k1) - lbeta(a, b))
              + (lbeta(a + k2, b + n2 - k2) - lbeta(a, b)))
    return float(np.exp(log_m0 - log_m1))


def bf_label(bf01: float) -> str:
    """Verbal label per Dienes (2014), including the insensitivity band."""
    if not np.isfinite(bf01):
        return "not computable"
    if bf01 >= 10:
        return "strong evidence for the null"
    if bf01 >= 3:
        return "moderate evidence for the null"
    if bf01 > 1 / 3:
        return "data insensitive (not evidence of absence)"
    if bf01 > 1 / 10:
        return "moderate evidence for an effect"
    return "strong evidence for an effect"


# ---------------------------------------------------------------------------
# Multi-cutoff pooling (Cattaneo, Keele, Titiunik & Vazquez-Bare 2016)
# ---------------------------------------------------------------------------
def pool_signed(estimates, ses, directions) -> dict:
    """
    Pool per-cusp RD estimates into one directionally-signed effect.

    Each person contributes to exactly one cusp for a given planet, so the cusp
    estimates are independent and inverse-variance weighting is efficient and its
    variance is simply 1 / sum(w).

    Signing by the PRE-REGISTERED direction (plan §1.2) is what stops the pooled
    estimate from cancelling to zero by construction: a positive pooled value means
    the data move the way astrology predicts, whatever the raw signs were.

    Cusps with direction 0 (dignity-neutral) are excluded, per the plan.
    """
    est = np.asarray(estimates, dtype=float)
    se = np.asarray(ses, dtype=float)
    d = np.asarray(directions, dtype=float)

    ok = np.isfinite(est) & np.isfinite(se) & (se > 0) & np.isin(d, (-1.0, 1.0))
    if not ok.any():
        return {"estimate": np.nan, "se": np.nan, "ci_low": np.nan,
                "ci_high": np.nan, "n_cusps": 0, "q_het": np.nan, "p_het": np.nan}

    signed = est[ok] * d[ok]
    w = 1.0 / se[ok] ** 2
    pooled = float(np.sum(w * signed) / np.sum(w))
    pooled_se = float(np.sqrt(1.0 / np.sum(w)))

    # Cochran's Q: do the cusps look like they estimate a common effect?
    q = float(np.sum(w * (signed - pooled) ** 2))
    dof = int(ok.sum() - 1)
    p_het = float(stats.chi2.sf(q, dof)) if dof > 0 else np.nan
    i2 = float(max(0.0, (q - dof) / q)) if q > 0 and dof > 0 else 0.0

    # Random-effects (DerSimonian-Laird) companion. The pre-registered primary is the
    # fixed-effect estimate above; this is reported alongside it because cusp-level
    # heterogeneity turns out to be large, and a fixed-effect CI would then be too
    # narrow. Reporting both is more conservative than silently switching.
    if dof > 0:
        s1, s2 = np.sum(w), np.sum(w ** 2)
        tau2 = float(max(0.0, (q - dof) / (s1 - s2 / s1)))
    else:
        tau2 = 0.0
    w_re = 1.0 / (se[ok] ** 2 + tau2)
    re_est = float(np.sum(w_re * signed) / np.sum(w_re))
    re_se = float(np.sqrt(1.0 / np.sum(w_re)))

    return {"estimate": pooled, "se": pooled_se,
            "ci_low": pooled - 1.96 * pooled_se,
            "ci_high": pooled + 1.96 * pooled_se,
            "n_cusps": int(ok.sum()), "q_het": q, "p_het": p_het, "i2": i2,
            "tau2": tau2, "re_estimate": re_est, "re_se": re_se,
            "re_ci_low": re_est - 1.96 * re_se, "re_ci_high": re_est + 1.96 * re_se}


# ---------------------------------------------------------------------------
# Multiplicity
# ---------------------------------------------------------------------------
def benjamini_hochberg(pvals, q: float = 0.05):
    """BH-FDR adjusted p-values and rejection flags (plan §2.4)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    finite = np.isfinite(p)
    adj = np.full(n, np.nan)
    if finite.sum() == 0:
        return adj, np.zeros(n, dtype=bool)

    idx = np.argsort(np.where(finite, p, np.inf))
    m = int(finite.sum())
    ranked = p[idx][:m]
    raw_adj = ranked * m / np.arange(1, m + 1)
    raw_adj = np.minimum.accumulate(raw_adj[::-1])[::-1]
    adj[idx[:m]] = np.minimum(raw_adj, 1.0)
    return adj, np.where(np.isfinite(adj), adj <= q, False)


# ---------------------------------------------------------------------------
# Reporting helper
# ---------------------------------------------------------------------------
def full_test(name: str, estimate: float, se: float, sesoi: float,
              n: int, direction: int = 0, extra: dict | None = None) -> dict:
    """Assemble the complete plan-mandated record for one test."""
    rec = {
        "test": name,
        "estimate": float(estimate),
        "se": float(se),
        "ci_low": float(estimate - 1.96 * se),
        "ci_high": float(estimate + 1.96 * se),
        "z": float(estimate / se) if se > 0 else np.nan,
        "p_two_sided": two_sided_p(estimate, se),
        "n": int(n),
        "sesoi": float(sesoi),
        "predicted_direction": int(direction),
    }
    rec.update({f"tost_{k}": v for k, v in tost(estimate, se, sesoi).items()})
    rec["equivalence_bound"] = equivalence_bound(estimate, se)
    rec["bf01"] = bf01_normal_likelihood(estimate, se, 0.707 * sesoi,
                                         prior="cauchy", one_sided=0)
    rec["bf01_directional"] = bf01_normal_likelihood(
        estimate, se, 0.707 * sesoi, prior="cauchy", one_sided=direction or 1)
    rec["bf01_label"] = bf_label(rec["bf01"])
    rec["bf_sensitivity"] = bf_prior_sensitivity(estimate, se, sesoi)
    if extra:
        rec.update(extra)
    return rec
