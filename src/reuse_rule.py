"""
A78 reuse-rule calculator (register A78, A81). Offline; takes the repeat-pilot answers (C59 step 3c)
and the group sizes of the reference runs (experiments/step16_reuse_groups.py).

k agents asked one identical prompt on one day, each acting on a stay-home probability: with one
call each the stay-home count has variance k*b; with m stored answers and each agent given one at
random, k*b + (k^2 - k)*sigma^2/m. Per phase f:
    R_f(m) = mean_sigma2_f * (sum k^2 - sum k) / (m * mean_b_f * sum k)
mean_sigma2_f, mean_b_f = means over the phase's repeat-pilot situations (sigma^2 with ddof 1,
b = mu(1 - mu)); the sums run over every (day, distinct prompt) of the phase in the reference runs.
PASS for m: R_f(m) < 1 in every phase under every stub; a phase with mean_sigma2_f = 0 passes.
Choice (A78/A81): m = 1 if it passes, else m = 3 if it passes, else the smallest m that passes.

Findings reported alongside, not used in the rule: ICC(1,1) (one-way random effects, single
measure; Koo & Li 2016, Shrout & Fleiss 1979 F-based 95% CI) and a bootstrap interval for R_f.
"""
import math

import numpy as np


def group_sums(k):
    k = np.asarray(k, np.int64)
    return int(k.sum()), int((k * k).sum())


def situation_stats(values):
    """values: one situation's repeat answers (probabilities 0-1). Returns mu, sigma^2 (ddof 1), b."""
    v = np.asarray(values, float)
    mu = float(v.mean())
    sigma2 = 0.0 if np.ptp(v) == 0 else float(v.var(ddof=1))     # identical repeats: exactly 0
    return mu, sigma2, mu * (1 - mu)


def ratio(mean_sigma2, mean_b, sum_k, sum_k2, m):
    if mean_sigma2 == 0 or sum_k2 == sum_k:
        return 0.0
    return mean_sigma2 * (sum_k2 - sum_k) / (m * mean_b * sum_k)


def phase_ratio(situations, sums, m):
    """situations: list of per-situation repeat answers for one phase; sums: (sum k, sum k^2)."""
    st = [situation_stats(v) for v in situations]
    return ratio(float(np.mean([s[1] for s in st])), float(np.mean([s[2] for s in st])), *sums, m)


def all_ratios(sits_by_phase, sums_by_stub_phase, m):
    """{stub: {phase: R_f(m)}}."""
    return {stub: {p: phase_ratio(sits_by_phase[p], sums[p], m) for p in sits_by_phase}
            for stub, sums in sums_by_stub_phase.items()}


def passes(ratios):
    return all(r < 1 for ph in ratios.values() for r in ph.values())


def choose_m(sits_by_phase, sums_by_stub_phase):
    """A78 then A81: m = 1 if it passes, else m = 3, else the smallest m > 3 that passes."""
    if passes(all_ratios(sits_by_phase, sums_by_stub_phase, 1)):
        return 1
    m = 3
    while not passes(all_ratios(sits_by_phase, sums_by_stub_phase, m)):
        m += 1
    return m


def calls(k, m):
    """A81: sum over groups of min(m, k)."""
    return int(np.minimum(np.asarray(k, np.int64), m).sum())


def max_sd_passing(sum_k, sum_k2, m, mean_b):
    """Largest sqrt(mean sigma^2) with R_f(m) < 1 (boundary value), given the phase's sums and mean b."""
    km1 = (sum_k2 - sum_k) / sum_k
    return math.inf if km1 == 0 else math.sqrt(m * mean_b / km1)


def icc_1_1(x, alpha=0.05):
    """x: n situations x k repeats. ICC(1,1) and its F-based (1 - alpha) CI (Shrout & Fleiss 1979)."""
    from scipy.stats import f as fdist
    x = np.asarray(x, float)
    n, k = x.shape
    rows = x.mean(1)
    msb = k * ((rows - x.mean()) ** 2).sum() / (n - 1)
    msw = ((x - rows[:, None]) ** 2).sum() / (n * (k - 1))
    icc = (msb - msw) / (msb + (k - 1) * msw)
    F = msb / msw if msw > 0 else math.inf
    fl = F / fdist.ppf(1 - alpha / 2, n - 1, n * (k - 1))
    fu = F * fdist.ppf(1 - alpha / 2, n * (k - 1), n - 1)
    return float(icc), ((fl - 1) / (fl + k - 1), (fu - 1) / (fu + k - 1))


def bootstrap_ratio(situations, sums, m, n_boot=2000, seed=20261127, alpha=0.05):
    """Interval for R_f(m), resampling each situation's repeats with replacement (situations and
    group sizes fixed)."""
    rng = np.random.default_rng(seed)
    sits = [np.asarray(v, float) for v in situations]
    out = np.empty(n_boot)
    for b in range(n_boot):
        out[b] = phase_ratio([v[rng.integers(len(v), size=len(v))] for v in sits], sums, m)
    return float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))


def bootstrap_ratio_two_level(situations, sums, m, n_boot=2000, seed=20261127, alpha=0.05):
    """Interval for R_f(m), resampling the phase's situations with replacement, then each chosen
    situation's repeats with replacement (group sizes fixed)."""
    rng = np.random.default_rng(seed)
    sits = [np.asarray(v, float) for v in situations]
    out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(len(sits), size=len(sits))
        out[b] = phase_ratio([sits[i][rng.integers(len(sits[i]), size=len(sits[i]))] for i in pick], sums, m)
    return float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))
