"""
C42 SUPPLEMENTARY (register C43): town-size sweep of Step B only. A capability test, not an arm.

Step B as C42: shared world, S1, Weitz's g = 1/(1 + (delta/delta_c)^k), k = 2, delta = n_H/T_H
(zero lag), every never-ill agent's action redrawn each sub-step (mode "substep"); the SAME
per-capita delta_c = 0.5e-5 per day, i.e. N*delta_c = 0.05 / 0.15 / 0.5 deaths/day at
N = 10,000 / 30,000 / 100,000. Population = the frozen quota population built at each N
(seed 0), per-agent f_D. Each N has its own AlwaysNormal control on the same seeds.

"Main phase" = the days whose end-of-day E + I > 0. Mean people in H = mean over the main
phase of the sub-step H counts (logged by the decision function, which already reads n_H).

Usage:  python experiments/step6_plateau_size_sweep.py --timing | --sim [--seeds100k 5] |
        --score | --plot
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
import step6_plateau_check as pc  # noqa: E402

SIZES = [10_000, 30_000, 100_000]
DCRIT = 0.5e-5
DAYS, SUB = 600, 48
OUT = pc.OUT
CACHE = os.path.join(OUT, "plateau_size_runs.npz")
_POP = {}


class LoggedWeitzSubstep(pc.WeitzSubstep):
    """WeitzSubstep that also records n_H at every sub-step (no effect on any draw)."""

    def __init__(self, ndc):
        super().__init__(ndc)
        self.h = []

    def substep_actions(self, view, n, rng):
        self.h.append(view["n_H"])
        return super().substep_actions(view, n, rng)


def run_one(task):
    kind, n_agents, seed = task
    from population import build_population
    from shared_world import run_shared_world, AlwaysNormal
    if n_agents not in _POP:
        _POP[n_agents] = build_population(N=n_agents, seed=0)
    pop = _POP[n_agents]
    kw = dict(N=n_agents, seed=seed, days=DAYS, f_D=pop.vulnerability, window=28,
              detection_rate=0.7, R0=pc.R0, T_H=pc.T_H)
    t0 = time.time()
    if kind == "ctrl":
        o, h = run_shared_world(decision=AlwaysNormal(), **kw), None
    else:
        d = LoggedWeitzSubstep(DCRIT * n_agents)
        o = run_shared_world(decision=d, **kw)
        h = np.zeros(DAYS)
        hh = np.asarray(d.h, float)
        nd = len(hh) // SUB
        h[:nd] = hh[:nd * SUB].reshape(nd, SUB).mean(1)   # daily mean of sub-step H counts
    rec = {k: np.asarray(o[k], float) for k in ("incidence", "prevalence", "exposed", "S")}
    if h is not None:
        rec["H"] = h
    return kind, n_agents, seed, rec, time.time() - t0


def timing():
    tasks = [(k, n, 0) for n in SIZES for k in ("B", "ctrl")]
    t0 = time.time()
    with mp.Pool(len(tasks)) as pool:
        out = pool.map(run_one, tasks)
    for kind, n, _, rec, dt in out:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  N {n:>7,} {kind:4s} seed 0: {dt:6.1f}s (last active day {last})")
    print(f"  wall {time.time() - t0:.1f}s")


def simulate(seeds_by_n):
    from step5_arm3_runs import waves
    tasks = [(k, n, s) for n in SIZES for s in seeds_by_n[n] for k in ("B", "ctrl")]
    tasks.sort(key=lambda t: -t[1])                       # largest towns first
    t0 = time.time()
    res, times = {}, []
    with mp.Pool(16) as pool:
        for kind, n, seed, rec, dt in pool.imap_unordered(run_one, tasks):
            res[(kind, n, seed)] = rec
            times.append(dt)
    t_sim = time.time() - t0
    keys = sorted(res)
    t0 = time.time()
    with mp.Pool(16) as pool:
        m1 = pool.map(waves, [res[k]["incidence"] for k in keys])
    print(f"{len(tasks)} simulations {t_sim / 60:.1f} min (per run {min(times):.1f}-"
          f"{max(times):.1f}s); {len(keys)} wave counts {(time.time() - t0) / 60:.1f} min")
    arr = {}
    for (kind, n, seed), w in zip(keys, m1):
        for key, v in res[(kind, n, seed)].items():
            arr[f"{kind}|{n}|{seed}#{key}"] = v
        arr[f"{kind}|{n}|{seed}#m1"] = np.array(w)
    np.savez_compressed(CACHE, **arr)


def score():
    import step3_shape_metrics as sm
    from step5_arm3_runs import mean_sem
    a = dict(np.load(CACHE))
    out = {}
    for n in SIZES:
        seeds = sorted({int(k.split("|")[2].split("#")[0]) for k in a if k.startswith(f"B|{n}|")})
        get = lambda kind, key: np.array([a[f"{kind}|{n}|{s}#{key}"] for s in seeds])  # noqa: E731
        inc, prev, exp_, S, H = (get("B", k) for k in ("incidence", "prevalence", "exposed", "S", "H"))
        incc, prevc, Sc = (get("ctrl", k) for k in ("incidence", "prevalence", "S"))
        m3 = np.array([sm.duration(y) for y in inc])
        m3c = np.array([sm.duration(y) for y in incc])
        ratio = m3 / m3c
        rng = np.random.default_rng(pc.BOOT_SEED)
        boot = rng.integers(0, len(seeds), size=(pc.N_BOOT, len(seeds)))
        bt = [m3[i].mean() / m3c[i].mean() for i in boot]
        dI = mean_sem(prev.max(1) - prevc.max(1))
        active = (exp_ + prev) > 0
        h_main = [float(h[ac].mean()) for h, ac in zip(H, active)]
        w, wc = get("B", "m1"), get("ctrl", "m1")
        r = dict(n_seeds=len(seeds), ndc=DCRIT * n,
                 stretch=float(m3.mean() / m3c.mean()), stretch_ci=tuple(np.percentile(bt, [2.5, 97.5])),
                 median=float(np.median(ratio)), gt15=int((ratio > 1.5).sum()), ge10=int((ratio >= 10).sum()),
                 m3=float(m3.mean()), m3_ctrl=float(m3c.mean()),
                 peak_red=float(-dI[0] / prevc.max(1).mean() * 100), peak_sems=float(dI[0] / dI[1]),
                 final_S=float(S[:, -1].mean()), final_S_sd=float(S[:, -1].std(ddof=1)),
                 final_S_ctrl=float(Sc[:, -1].mean()), final_S_ctrl_sd=float(Sc[:, -1].std(ddof=1)),
                 attack=float(1 - S[:, -1].mean()), m1=float(w.mean()), m1_multi=int((w > 1).sum()),
                 m1_ctrl=float(wc.mean()), active_600=int(active[:, -1].sum()),
                 last_active=[int(np.nonzero(ac)[0].max()) + 1 for ac in active],
                 H_main_mean=float(np.mean(h_main)), H_main_range=(float(min(h_main)), float(max(h_main))),
                 peak_I_ctrl=float(prevc.max(1).mean()))
        out[n] = r
        print(f"\nN = {n:,} (N*delta_c = {r['ndc']:.3g} deaths/day), seeds {seeds[0]}-{seeds[-1]} (n={len(seeds)})")
        print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
              f"{' (TRUNCATED: runs active at 600)' if r['active_600'] else ''}; median x{r['median']:.2f}; "
              f">x1.5 {r['gt15']}/{len(seeds)}; >=x10 {r['ge10']}/{len(seeds)}; T10-90 {r['m3']:.1f} vs "
              f"control {r['m3_ctrl']:.1f} d")
        print(f"  peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM; control peak I "
              f"{r['peak_I_ctrl']:.0f}); final S {r['final_S']:.4f} (SD {r['final_S_sd']:.4f}; control "
              f"{r['final_S_ctrl']:.4f}, SD {r['final_S_ctrl_sd']:.4f}); attack {r['attack']:.4f}")
        print(f"  waves {r['m1']:.2f} (>1: {r['m1_multi']}/{len(seeds)}; control {r['m1_ctrl']:.2f}); "
              f"active at day 600 {r['active_600']}/{len(seeds)}; last active day {sorted(r['last_active'])}")
        print(f"  mean people in H over the main phase {r['H_main_mean']:.2f} (per-run "
              f"{r['H_main_range'][0]:.2f}-{r['H_main_range'][1]:.2f})")
    json.dump({str(k): v for k, v in out.items()}, open(os.path.join(OUT, "plateau_size_scores.json"), "w"),
              indent=1)


def plot(seed=0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    a = dict(np.load(CACHE))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), dpi=130, sharey=False)
    t = np.arange(DAYS)
    for ax, n in zip(axes, SIZES):
        y, yc = a[f"B|{n}|{seed}#incidence"] / n * 1000, a[f"ctrl|{n}|{seed}#incidence"] / n * 1000
        ax.plot(t, yc, color="#9a9a9a", lw=1.2, label="no-behaviour control")
        ax.plot(t, y, color="#c2410c", lw=1.3, label="Weitz rule, step B")
        ax.set_yscale("symlog", linthresh=0.1)
        ax.set_title(f"N = {n:,} (N*delta_c = {DCRIT * n:.3g}), seed {seed}", fontsize=9, loc="left")
        ax.set_xlabel("day"); ax.grid(alpha=0.25)
    axes[0].set_ylabel("new infections per day per 1,000 people")
    axes[0].legend(fontsize=8, frameon=False)
    fig.suptitle("C42 supplementary: Step B town-size sweep, S1, per-capita delta_c = 0.5e-5/day, k = 2",
                 fontsize=10)
    fig.tight_layout()
    path = os.path.join(OUT, "plateau_size_examples.png")
    fig.savefig(path)
    print(path)


if __name__ == "__main__":
    mp.freeze_support()
    if "--timing" in sys.argv:
        timing()
    if "--sim" in sys.argv:
        n100 = int(sys.argv[sys.argv.index("--seeds100k") + 1]) if "--seeds100k" in sys.argv else 10
        simulate({10_000: range(10), 30_000: range(10), 100_000: range(n100)})
    if "--score" in sys.argv:
        score()
    if "--plot" in sys.argv:
        plot()
