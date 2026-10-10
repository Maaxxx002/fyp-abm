"""
E23 plateau-reachability check (register C42). A CAPABILITY TEST, NOT AN ARM. No API calls.

Weitz's awareness rule g = 1/(1 + (delta/delta_c)^k), k = 2 (figseir_Hlong_k2D.m). In the shared
world stay home is one-sided (A39) and ill agents do not decide (A38), so each never-ill agent
stays home with probability q = 1 - g; precautions and normal-with-precautions are unused.
delta_c is CHOSEN to obtain a plateau (allowed: reachability test). Units: delta and delta_c
are deaths per day in the whole town (Weitz Table 1's N*delta_c; model.run_weitz_behaviour's
convention).

  A   Weitz model B ODE with this g, N = 3,000, S1 (R0 3, latent 2 d, infectious 6 d,
      T_H 14), f_D = the frozen population's mean IFR 0.009718, I(0) = 10/N (the ABM's start),
      delta = gamma_H * N * H. Control: the same ODE without behaviour.
  B   shared world, S1, 30 seeds, delta = n_H / T_H (Weitz's own, zero lag), q redrawn for
      every never-ill agent every sub-step (run_shared_world mode "substep").
  C   shared world, S1, 30 seeds, delta = the agents' perceived signal (28-day mean of 70%-
      reported deaths, A24/A25), decisions once per day at the start of the day, p = 1.0.
  C2  as C with p = 0.3.
Controls (B, C, C2): AlwaysNormal in the same world, same seeds.

Usage:  python experiments/step6_plateau_check.py --ode | --timing | --sim | --score | --plot
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
from shared_world import DecisionFunction, NORMAL, STAY_HOME  # noqa: E402

N, DAYS, SEEDS, K = 3000, 600, list(range(30)), 2
R0, LAT, INF, T_H = 3.0, 2.0, 6.0, 14.0
F_D_MEAN = 0.009718
NDC_WEITZ = 0.5e-5 * N          # Weitz Dcrit 0.5e-5 per capita per day -> 0.015 deaths/day
NDC_GRID = [0.005, 0.015, 0.05, 0.15, 0.5, 1.5, 5.0]
OUT = os.path.join(ROOT, "results", "step6")
CACHE = os.path.join(OUT, "plateau_runs.npz")
N_BOOT, BOOT_SEED = 1000, 20261005
_POP = {}


def q_of(delta, ndc):
    return 1.0 - 1.0 / (1.0 + (delta / ndc) ** K)


class WeitzSubstep(DecisionFunction):
    """Step B: q from delta = n_H / T_H, redrawn every sub-step."""
    mode = "substep"

    def __init__(self, ndc):
        self.ndc = ndc

    def substep_actions(self, view, n, rng):
        q = q_of(view["death_delay_rate"] * view["n_H"], self.ndc)
        return np.where(rng.random(n) < q, STAY_HOME, NORMAL).astype(np.int8)


class WeitzDaily(DecisionFunction):
    """Steps C/C2: q from the perceived signal (28-day mean of reported deaths), re-asked once
    per day at the start of the day."""
    mode = "discrete"
    redecides = True

    def __init__(self, ndc):
        self.ndc = ndc

    def decide(self, day, agents, view, rng):
        q = q_of(float(view["awareness_signal"]), self.ndc)
        return np.where(rng.random(len(agents)) < q, STAY_HOME, NORMAL).astype(np.int8)


# ------------------------------------------------------------------ Step A (ODE)

def ode(ndc=None, days=DAYS):
    """Weitz model B per capita; I(0) = 10/N. Returns daily incidence (counts), prevalence I
    (counts, end of day), E (counts), S fraction, all length `days`."""
    from scipy.integrate import solve_ivp
    beta, mu, gamma, gH = R0 / INF, 1 / LAT, 1 / INF, 1 / T_H

    def rhs(t, y):
        S, E, I, R, H, D = y
        g = 1.0 if ndc is None else 1.0 / (1.0 + (gH * H * N / ndc) ** K)
        foi = beta * S * I * g
        return [-foi, foi - mu * E, mu * E - gamma * I, gamma * I * (1 - F_D_MEAN),
                gamma * I * F_D_MEAN - gH * H, gH * H]

    y0 = [1 - 10 / N, 0, 10 / N, 0, 0, 0]
    sol = solve_ivp(rhs, [0, days], y0, t_eval=np.arange(days + 1), rtol=1e-10, atol=1e-14,
                    method="LSODA")
    S, E, I = sol.y[0], sol.y[1], sol.y[2]
    return dict(incidence=(S[:-1] - S[1:]) * N, prevalence=I[1:] * N, exposed=E[1:] * N,
                S=S[1:])


def ode_summary(o, oc):
    import step3_shape_metrics as sm
    m3, m3c = sm.duration(o["incidence"]), sm.duration(oc["incidence"])
    return dict(m3=m3, m3_ctrl=m3c, stretch=m3 / m3c,
                peak_red=float(100 * (1 - o["prevalence"].max() / oc["prevalence"].max())),
                peak_I=float(o["prevalence"].max()), final_S=float(o["S"][-1]),
                attack=float(1 - o["S"][-1]),
                active_600_EI=float(o["exposed"][-1] + o["prevalence"][-1]),
                active_600=bool(o["exposed"][-1] + o["prevalence"][-1] >= 1.0))


def step_a():
    os.makedirs(OUT, exist_ok=True)
    oc = ode(None)
    rows = {}
    print("Step A, ODE N = 3,000, S1: N*delta_c | T10-90 (d) | stretch vs no-behaviour ODE | "
          "peak I red | final S | E+I at day 600 (persons) | active at 600 (>= 1 person)")
    for ndc in sorted(set(NDC_GRID + [NDC_WEITZ])):
        r = ode_summary(ode(ndc), oc)
        rows[ndc] = r
        print(f"  {ndc:7.3f} | {r['m3']:5.0f} | x{r['stretch']:6.2f} | {r['peak_red']:5.1f}% | "
              f"{r['final_S']:.4f} | {r['active_600_EI']:8.2f} | {r['active_600']}")
    print(f"  control: T10-90 {rows[NDC_WEITZ]['m3_ctrl']:.0f} d, final S {oc['S'][-1]:.4f}, "
          f"peak I {oc['prevalence'].max():.1f}")
    json.dump({str(k): v for k, v in rows.items()}, open(os.path.join(OUT, "plateau_ode.json"), "w"),
              indent=1)
    return rows


# ------------------------------------------------------------------ Steps B, C, C2

def run_one(task):
    step, ndc, seed = task
    from population import build_population
    from shared_world import run_shared_world, AlwaysNormal
    if "pop" not in _POP:
        _POP["pop"] = build_population(N=N, seed=0)
    pop = _POP["pop"]
    kw = dict(N=N, seed=seed, days=DAYS, f_D=pop.vulnerability, window=28, detection_rate=0.7,
              R0=R0, T_H=T_H)
    t0 = time.time()
    if step == "ctrl":
        o = run_shared_world(decision=AlwaysNormal(), **kw)
    elif step == "B":
        o = run_shared_world(decision=WeitzSubstep(ndc), **kw)
    else:
        o = run_shared_world(decision=WeitzDaily(ndc), redecide_prob=1.0 if step == "C" else 0.3,
                             stop_deciding_when_no_infection=True, **kw)
    rec = {k: np.asarray(o[k], float) for k in ("incidence", "prevalence", "exposed", "S",
                                                "awareness_signal")}
    rec["stay_home_share"] = o["S_by_action"][:, STAY_HOME] / np.maximum(o["S"] * N, 1)
    return step, seed, rec, time.time() - t0


def timing(ndc):
    tasks = [(s, ndc, 0) for s in ("ctrl", "B", "C", "C2")] * 4
    t0 = time.time()
    with mp.Pool(16) as pool:
        out = pool.map(run_one, tasks)
    for st in ("ctrl", "B", "C", "C2"):
        ts = [o[3] for o in out if o[0] == st]
        print(f"  {st:4s} per run {min(ts):.1f}-{max(ts):.1f}s")
    print(f"  wall {time.time() - t0:.1f}s for {len(tasks)} runs")


def simulate(ndc):
    from step5_arm3_runs import waves
    tasks = [(st, ndc, s) for st in ("ctrl", "B", "C", "C2") for s in SEEDS]
    t0 = time.time()
    res = {}
    with mp.Pool(16) as pool:
        for st, seed, rec, _ in pool.imap_unordered(run_one, tasks):
            res[(st, seed)] = rec
    t_sim = time.time() - t0
    keys = [(st, s) for st in ("ctrl", "B", "C", "C2") for s in SEEDS]
    t0 = time.time()
    with mp.Pool(16) as pool:
        m1 = pool.map(waves, [res[k]["incidence"] for k in keys], chunksize=2)
    print(f"{len(tasks)} simulations {t_sim / 60:.1f} min; {len(keys)} wave counts "
          f"{(time.time() - t0) / 60:.1f} min")
    arr = {}
    for st in ("ctrl", "B", "C", "C2"):
        for key in res[(st, 0)]:
            arr[f"{st}#{key}"] = np.array([res[(st, s)][key] for s in SEEDS])
        arr[f"{st}#m1"] = np.array([m for (k, m) in zip(keys, m1) if k[0] == st])
    oa, oc = ode(ndc), ode(None)
    for nm, o in (("A", oa), ("A_ctrl", oc)):
        for key in ("incidence", "prevalence", "exposed", "S"):
            arr[f"{nm}#{key}"] = o[key]
    arr["A#m1"] = np.array(waves(oa["incidence"]))
    arr["A_ctrl#m1"] = np.array(waves(oc["incidence"]))
    arr["ndc"] = np.array(ndc)
    np.savez_compressed(CACHE, **arr)


def score():
    import step3_shape_metrics as sm
    from step5_arm3_runs import mean_sem
    a = dict(np.load(CACHE))
    ndc = float(a["ndc"])
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    out = {}
    oa = {k: a[f"A#{k}"] for k in ("incidence", "prevalence", "exposed", "S")}
    oc = {k: a[f"A_ctrl#{k}"] for k in ("incidence", "prevalence", "exposed", "S")}
    out["A"] = dict(ode_summary(oa, oc), m1=float(a["A#m1"]), m1_ctrl=float(a["A_ctrl#m1"]))
    r = out["A"]
    print(f"N*delta_c = {ndc}")
    print(f"A (ODE): T10-90 {r['m3']:.0f} d vs control {r['m3_ctrl']:.0f} d -> stretch x{r['stretch']:.2f}"
          f"{' (TRUNCATED at day 600)' if r['active_600'] else ''}; peak I reduction {r['peak_red']:.1f}%; "
          f"final S {r['final_S']:.4f}; attack {r['attack']:.4f}; waves {r['m1']:.0f} (control "
          f"{r['m1_ctrl']:.0f}); E+I at day 600 {r['active_600_EI']:.2f} persons")
    inc_c, prev_c, S_c = a["ctrl#incidence"], a["ctrl#prevalence"], a["ctrl#S"]
    m3c = np.array([sm.duration(y) for y in inc_c])
    act_c = int(((a["ctrl#exposed"] + prev_c)[:, -1] > 0).sum())
    print(f"control (shared world): T10-90 {m3c.mean():.1f} d, peak I {prev_c.max(1).mean():.1f}, "
          f"final S {S_c[:, -1].mean():.4f}, active at 600 {act_c}/30, waves {a['ctrl#m1'].mean():.2f}")
    for st in ("B", "C", "C2"):
        inc, prev, exp_, S = (a[f"{st}#{k}"] for k in ("incidence", "prevalence", "exposed", "S"))
        m3 = np.array([sm.duration(y) for y in inc])
        ok = np.isfinite(m3) & np.isfinite(m3c)
        ratio = m3 / m3c
        bt = [m3[i[ok[i]]].mean() / m3c[i[ok[i]]].mean() for i in boot_idx]
        dI = mean_sem(prev.max(1) - prev_c.max(1))
        active = int(((exp_ + prev)[:, -1] > 0).sum())
        w = a[f"{st}#m1"]
        r = dict(stretch=float(m3[ok].mean() / m3c[ok].mean()),
                 stretch_ci=tuple(np.percentile(bt, [2.5, 97.5])), median=float(np.median(ratio[ok])),
                 gt15=int((ratio[ok] > 1.5).sum()), gt10=int((ratio[ok] >= 10).sum()), n_m3=int(ok.sum()),
                 m3_mean=float(m3[ok].mean()), peak_red=float(-dI[0] / prev_c.max(1).mean() * 100),
                 peak_sems=dI[0] / dI[1], final_S=float(S[:, -1].mean()),
                 final_S_sem=float(S[:, -1].std(ddof=1) / np.sqrt(30)), attack=float(1 - S[:, -1].mean()),
                 m1=float(w.mean()), m1_multi=int((w > 1).sum()), active_600=active,
                 mean_stay_home_active=float(np.nanmean([sh[(e + p) > 0].mean() for sh, e, p in
                                                         zip(a[f"{st}#stay_home_share"], exp_, prev)])))
        out[st] = r
        print(f"{st}: stretch x{r['stretch']:.3f} [{r['stretch_ci'][0]:.3f}, {r['stretch_ci'][1]:.3f}]"
              f"{' (TRUNCATED: runs active at 600)' if active else ''}; median x{r['median']:.3f}; "
              f">x1.5 {r['gt15']}/{r['n_m3']}; >=x10 {r['gt10']}/{r['n_m3']}; T10-90 mean {r['m3_mean']:.1f} d; "
              f"peak red {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
              f"+/- {r['final_S_sem']:.4f}; attack {r['attack']:.4f}; waves {r['m1']:.2f} (>1: {r['m1_multi']}/30); "
              f"active at day 600 {active}/30; mean stay-home share of S while E+I>0 "
              f"{r['mean_stay_home_active']:.3f}")
    b = out["B"]
    passed = b["stretch"] >= 10 or (b["active_600"] > 15 and b["peak_red"] >= 80)
    print(f"\nPASS MARK (plateau reachable): B stretch >= x10 [{b['stretch'] >= 10}] or majority "
          f"active at 600 [{b['active_600']}/30 > 15: {b['active_600'] > 15}] with peak red >= 80% "
          f"[{b['peak_red'] >= 80}] -> {'PASS' if passed else 'NOT MET'}")
    out["pass"] = bool(passed)
    json.dump(out, open(os.path.join(OUT, "plateau_scores.json"), "w"), indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def plot(seed=0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    a = dict(np.load(CACHE))
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), dpi=130, sharex=True)
    panels = [("A", "A: Weitz model B ODE, N = 3,000", a["A#incidence"], a["A_ctrl#incidence"]),
              ("B", f"B: shared world, delta = H/T_H, q every sub-step (seed {seed})",
               a["B#incidence"][seed], a["ctrl#incidence"][seed]),
              ("C", f"C: perceived 28-day reported signal, daily, p = 1.0 (seed {seed})",
               a["C#incidence"][seed], a["ctrl#incidence"][seed]),
              ("C2", f"C2: as C, p = 0.3 (seed {seed})", a["C2#incidence"][seed],
               a["ctrl#incidence"][seed])]
    t = np.arange(DAYS)
    for ax, (_, title, y, yc) in zip(axes.flat, panels):
        ax.plot(t, yc, color="#9a9a9a", lw=1.2, label="no-behaviour control")
        ax.plot(t, y, color="#c2410c", lw=1.4, label="Weitz rule (stay home with q = 1 - g)")
        ax.set_yscale("symlog", linthresh=1.0)
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_ylabel("new infections per day")
        ax.grid(alpha=0.25)
    axes[1, 0].set_xlabel("day"); axes[1, 1].set_xlabel("day")
    axes[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle(f"E23 plateau-reachability check, S1, N = 3,000, N*delta_c = {float(a['ndc']):.3g}, k = 2",
                 fontsize=10)
    fig.tight_layout()
    path = os.path.join(OUT, "plateau_examples.png")
    fig.savefig(path)
    print(path)


if __name__ == "__main__":
    mp.freeze_support()
    ndc = float(sys.argv[sys.argv.index("--ndc") + 1]) if "--ndc" in sys.argv else NDC_WEITZ
    if "--ode" in sys.argv:
        step_a()
    if "--timing" in sys.argv:
        timing(ndc)
    if "--sim" in sys.argv:
        simulate(ndc)
    if "--score" in sys.argv:
        score()
    if "--plot" in sys.argv:
        plot()
