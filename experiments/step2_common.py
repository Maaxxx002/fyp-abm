"""
Shared runner and pass-mark helpers for the step-2 modifications (register C24/C25).

FOUNDATION (C23 config 2): N=3,000 frozen quota population (seed 0), real CBF
(run_cbf_behaviour), flat r=0.5, beta_B=0.5, mu_B=0.01, gamma_beh=1, window=28,
detection_rate=0.7 (plain multiplier, A25), per-agent f_D (A26), Weitz disease (R0=3,
latent 2 d, infectious 6 d, T_H=14), 48 sub-steps, 10 initial infected, days=900.
Each step-2 config changes exactly one of these. No-behaviour controls are the same call
with beta_B=0 (as in C23), so seeds pair with common random numbers.

Pass marks (register A27/A28):
  (a) lower peak I and higher final S than own control, each by > 2 SEM of the paired diff.
  (b) FAIL only if relative error > 6% AND gap > 2 SEM; > 6% with gap <= 2 SEM is
      INCONCLUSIVE (-> re-run at 90 seeds, same rule).
"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from model import run_cbf_behaviour  # noqa: E402
from population import build_population  # noqa: E402

POPULATION_SEED = 0
WEITZ_DISEASE = dict(R0=3.0, latent_period_days=2.0, infectious_period_days=6.0)
# Gozzi constants.py: mu = 1/2.5 (= 1/infectious period), eps = 1/4 (= 1/latent period);
# example.ipynb R0=2.5. Named explicitly because of the mu/eps symbol collision.
GOZZI_DISEASE = dict(R0=2.5, latent_period_days=4.0, infectious_period_days=2.5)

FOUNDATION = dict(N=3_000, r="flat", behaviour=True, disease="weitz", days=900)
R_FLAT = 0.5
BETA_B, MU_B, GAMMA_BEH, WINDOW, DETECTION = 0.5, 0.01, 1.0, 28, 0.7
T_H = 14.0

_POPS = {}


def population(N):
    if N not in _POPS:
        _POPS[N] = build_population(N=N, seed=POPULATION_SEED)
    return _POPS[N]


def disease_params(name):
    return WEITZ_DISEASE if name == "weitz" else GOZZI_DISEASE


def run_one(args):
    """args = (config name, config dict, seed). Returns (name, seed, metrics, seconds)."""
    name, cfg, seed = args
    pop = population(cfg["N"])
    if cfg["r"] == "flat":
        r_kw = dict(r=R_FLAT)
    else:  # C24's per-agent r, superseded by A29; kept only to reproduce C24
        r_kw = dict(experimental_r_from_response_efficacy=pop.response_efficacy)
    t0 = time.time()
    out = run_cbf_behaviour(
        N=cfg["N"], seed=seed, days=cfg["days"], **r_kw,
        seeds_infected=10, f_D=pop.vulnerability, T_H=T_H, n_substeps=cfg.get("n_substeps", 48),
        beta_B=BETA_B if cfg["behaviour"] else 0.0, mu_B=MU_B, gamma_beh=GAMMA_BEH,
        window=WINDOW, detection_rate=DETECTION, **disease_params(cfg["disease"]),
    )
    rec = dict(
        final_S=float(out["S"][-1]),
        peak_I=float(out["prevalence"].max()),
        peak_SB=float(out["SB"].max()),
        peak_daily_deaths=float(out["deaths"].max()),
        infected_at_end=bool(out["exposed"][-1] + out["prevalence"][-1] > 0),
    )
    return name, seed, rec, time.time() - t0


def mean_sem(x):
    x = np.asarray(x, dtype=float)
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def values(res, name, key, seeds):
    return np.array([res[name][s][key] for s in seeds])


def paired(res, a, b, key, seeds):
    m, se, n = mean_sem(values(res, a, key, seeds) - values(res, b, key, seeds))
    return dict(mean_diff=m, sem_diff=se, n=n, sems=m / se if se > 0 else float("nan"))


def pass_a(res, cfg, ctrl, seeds):
    d_i = paired(res, cfg, ctrl, "peak_I", seeds)
    d_s = paired(res, cfg, ctrl, "final_S", seeds)
    ok_i = d_i["mean_diff"] < 0 and abs(d_i["sems"]) > 2
    ok_s = d_s["mean_diff"] > 0 and abs(d_s["sems"]) > 2
    return dict(peak_I=dict(d_i, passes=bool(ok_i)), final_S=dict(d_s, passes=bool(ok_s)),
                passes=bool(ok_i and ok_s))


def pass_b(final_S, ref):
    m, se, n = mean_sem(final_S)
    rel = abs(m - ref) / ref
    gap = (m - ref) / se
    if rel <= 0.06:
        verdict = "PASS"
    elif abs(gap) > 2:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    return dict(dde=ref, mean=m, sem=se, n=n, relative_error=rel, gap_sems=gap, verdict=verdict)


def fmt_paired(d):
    return f"{d['mean_diff']:+.5f} +/- {d['sem_diff']:.5f} ({d['sems']:+.2f} SEM, n={d['n']})"


def print_pass_a(label, pa):
    print(f"  (a) {label}: peak I {fmt_paired(pa['peak_I'])}; final S {fmt_paired(pa['final_S'])}"
          f" -> {'PASS' if pa['passes'] else 'FAIL'}")


def print_pass_b(label, pb):
    print(f"  (b) {label}: mean final S {pb['mean']:.5f} +/- {pb['sem']:.5f} vs DDE {pb['dde']:.5f}"
          f": rel err {pb['relative_error']*100:.2f}%, gap {pb['gap_sems']:+.2f} SEM "
          f"(n={pb['n']}) -> {pb['verdict']}")


def print_stats(res, name, seeds, behaviour=True):
    keys = ["final_S", "peak_I", "peak_daily_deaths"] + (["peak_SB"] if behaviour else [])
    for key in keys:
        m, se, n = mean_sem(values(res, name, key, seeds))
        print(f"  {name:9s} {key:18s} {m:11.5f} +/- {se:.5f} (n={n})")
    k = int(sum(res[name][s]["infected_at_end"] for s in seeds))
    print(f"  {name:9s} runs with E or I agents at final day: {k}/{len(seeds)}")


def run_pool(tasks, n_workers=None):
    import multiprocessing as mp
    n_workers = n_workers or min(os.cpu_count() or 1, 16)
    res, times = {}, {}
    t0 = time.time()
    with mp.Pool(min(n_workers, len(tasks))) as pool:
        for name, seed, rec, dt in pool.imap_unordered(run_one, tasks):
            res.setdefault(name, {})[seed] = rec
            times.setdefault(name, []).append(dt)
    return res, times, time.time() - t0
