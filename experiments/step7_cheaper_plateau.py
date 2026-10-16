"""
Can a plateau be reached more cheaply than N = 30,000? (register C45.) A CAPABILITY TEST, NOT AN
ARM. No API calls. Test rule only: Weitz's g = 1/(1 + (delta/delta_c)^k), k = 2, healthy agents
(never-ill: S or E) stay home with q = 1 - g, as C42/C43. delta_c is tuned (allowed: not an arm).

  1a  Route B -- higher death rate at N = 3,000, f_D in {0.025, 0.05, 0.10} (tuning values given
      by the planning chat; NOT sourced -- supervisor approval to tune, 16 Oct 2026).
      ODE (Weitz model B, S1, N = 3,000, flat f_D): N*delta_c = the LARGEST value on the grid
      0.005 * 10^(j/20), j = 0..80, that meets C42 Step A's plateau criterion (T10-90 stretch
      >= x10 vs the no-behaviour ODE, or E + I >= 1 person at day 600).
      ABM step B at that delta_c: shared world, N = 3,000, seeds 0-9, delta = n_H / T_H, every
      never-ill agent redrawn each sub-step. Per-agent f_D = IFR_10age[band] * f_D / 0.009718,
      capped at 1.0. Control: AlwaysNormal, same f_D array, same seeds.
      Step C for the best f_D only (largest step-B mean stretch; tie -> smaller f_D): delta = the
      agents' 28-day mean of 70%-reported deaths, daily decisions at the start of the day,
      p = 1.0, A55 stop.
  1b  Route A -- step B at N = 15,000 and 20,000, normal per-agent f_D, seeds 0-9, per-capita
      delta_c = 0.5e-5/day (C43), i.e. N*delta_c = 0.075 / 0.10.

Usage:  python experiments/step7_cheaper_plateau.py --ode | --timing | --sim | --score
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
from step6_plateau_size_sweep import LoggedWeitzSubstep  # noqa: E402

N3K, DAYS, SUB = 3000, 600, 48
SEEDS = list(range(10))
F_D_REF = 0.009718                       # frozen population mean IFR (A26)
F_D_LIST = [0.025, 0.05, 0.10]
NDC_GRID = [0.005 * 10 ** (j / 20) for j in range(81)]   # 0.005 .. 50 deaths/day, 20 per decade
SIZES_1B = [15_000, 20_000]
DCRIT = 0.5e-5                           # Weitz per-capita Dcrit (C42/C43)
OUT = os.path.join(ROOT, "results", "step7")
ODE_JSON = os.path.join(OUT, "cheaper_plateau_ode.json")
CACHE = os.path.join(OUT, "cheaper_plateau_runs.npz")
_POP = {}


# ------------------------------------------------------------------ ODE (Weitz model B, flat f_D)

def ode(ndc, f_D, N=N3K, days=DAYS):
    """pc.ode with f_D as a parameter (same equations, tolerances and initial condition)."""
    from scipy.integrate import solve_ivp
    beta, mu, gamma, gH = pc.R0 / pc.INF, 1 / pc.LAT, 1 / pc.INF, 1 / pc.T_H

    def rhs(t, y):
        S, E, I, R, H, D = y
        g = 1.0 if ndc is None else 1.0 / (1.0 + (gH * H * N / ndc) ** pc.K)
        foi = beta * S * I * g
        return [-foi, foi - mu * E, mu * E - gamma * I, gamma * I * (1 - f_D),
                gamma * I * f_D - gH * H, gH * H]

    y0 = [1 - 10 / N, 0, 10 / N, 0, 0, 0]
    sol = solve_ivp(rhs, [0, days], y0, t_eval=np.arange(days + 1), rtol=1e-10, atol=1e-14,
                    method="LSODA")
    S, E, I, H = sol.y[0], sol.y[1], sol.y[2], sol.y[4]
    return dict(incidence=(S[:-1] - S[1:]) * N, prevalence=I[1:] * N, exposed=E[1:] * N,
                S=S[1:], H=H[1:] * N)


def _ode_row(args):
    ndc, f_D = args
    o = ode(ndc, f_D)
    oc = ode(None, f_D)
    r = pc.ode_summary(o, oc)
    r["plateau"] = bool(r["stretch"] >= 10 or r["active_600"])
    act = (o["exposed"] + o["prevalence"]) >= 1.0
    r["H_main_mean"] = float(o["H"][act].mean()) if act.any() else 0.0
    return ndc, f_D, r


def step_ode():
    os.makedirs(OUT, exist_ok=True)
    tasks = [(ndc, f) for f in [F_D_REF] + F_D_LIST for ndc in NDC_GRID]
    t0 = time.time()
    with mp.Pool(16) as pool:
        rows = pool.map(_ode_row, tasks)
    out = {}
    for f in [F_D_REF] + F_D_LIST:
        rr = [(ndc, r) for ndc, ff, r in rows if ff == f]
        ok = [ndc for ndc, r in rr if r["plateau"]]
        best = max(ok) if ok else None
        out[str(f)] = dict(chosen_ndc=best, rows={f"{ndc:.6g}": r for ndc, r in rr})
        print(f"\nf_D = {f}: largest grid N*delta_c meeting the plateau criterion = "
              f"{best if best is None else round(best, 6)}")
        print("  N*delta_c | T10-90 | stretch | peak red | final S | E+I@600 | plateau | mean H (E+I>=1)")
        for ndc, r in rr:
            if best is not None and best / 10 ** 0.35 <= ndc <= best * 10 ** 0.35:
                print(f"  {ndc:9.4f} | {r['m3']:5.0f} | x{r['stretch']:6.2f} | {r['peak_red']:5.1f}% | "
                      f"{r['final_S']:.4f} | {r['active_600_EI']:7.2f} | {r['plateau']} | {r['H_main_mean']:.2f}")
    print(f"\n{len(tasks)} ODE solves, {time.time() - t0:.0f}s")
    json.dump(out, open(ODE_JSON, "w"), indent=1)
    return out


def chosen_ndc():
    o = json.load(open(ODE_JSON))
    return {f: o[str(f)]["chosen_ndc"] for f in F_D_LIST}


# ------------------------------------------------------------------ ABM

def f_D_array(vul, f_D):
    """Scale IFR_10age by f_D / 0.009718 (age pattern kept), cap at 1.0. f_D None -> unscaled."""
    if f_D is None:
        return vul
    return np.minimum(1.0, vul * (f_D / F_D_REF))


def run_one(task):
    """task = (kind, n_agents, f_D or None, ndc or None, seed[, window]); kind in ctrl / B / C.
    window (default 28, A24) is the length of the world's reported-death mean (C47: 7-day test)."""
    kind, n, f_D, ndc, seed = task[:5]
    window = task[5] if len(task) > 5 else 28
    from population import build_population
    from shared_world import (run_shared_world, AlwaysNormal, STAY_HOME, PRECAUTIONS)
    if n not in _POP:
        _POP[n] = build_population(N=n, seed=0)
    pop = _POP[n]
    kw = dict(N=n, seed=seed, days=DAYS, f_D=f_D_array(pop.vulnerability, f_D), window=window,
              detection_rate=0.7, R0=pc.R0, T_H=pc.T_H)
    t0 = time.time()
    h_sub = None
    if kind == "ctrl":
        o = run_shared_world(decision=AlwaysNormal(), **kw)
    elif kind == "B":
        d = LoggedWeitzSubstep(ndc)
        o = run_shared_world(decision=d, **kw)
        hh = np.asarray(d.h, float)
        nd = len(hh) // SUB
        h_sub = np.zeros(DAYS)
        h_sub[:nd] = hh[:nd * SUB].reshape(nd, SUB).mean(1)
    else:
        o = run_shared_world(decision=pc.WeitzDaily(ndc), redecide_prob=1.0,
                             stop_deciding_when_no_infection=True, **kw)
    rec = {k: np.asarray(o[k], float) for k in ("incidence", "prevalence", "exposed", "S",
                                                "awareness_signal", "recovered", "deaths")}
    deciders = o["S_by_action"].sum(1) + o["E_by_action"].sum(1)   # whole agents (C47, E24 rounding fix)
    cautious = (o["S_by_action"][:, STAY_HOME] + o["S_by_action"][:, PRECAUTIONS]
                + o["E_by_action"][:, STAY_HOME] + o["E_by_action"][:, PRECAUTIONS])
    with np.errstate(invalid="ignore", divide="ignore"):
        rec["caution"] = np.where(deciders > 0, cautious / deciders, np.nan)
    # end-of-day H = N - S - E - I - R - cumulative D
    rec["H_eod"] = (n - np.rint(o["S"] * n) - o["exposed"] - o["prevalence"] - o["recovered"]
                    - np.cumsum(o["deaths"]))
    if h_sub is not None:
        rec["H_sub"] = h_sub
    return task, rec, time.time() - t0


def tasks_main(ndc_by_f):
    t = []
    for f in F_D_LIST:
        for s in SEEDS:
            t += [("B", N3K, f, ndc_by_f[f], s), ("ctrl", N3K, f, None, s)]
    for n in SIZES_1B:
        for s in SEEDS:
            t += [("B", n, None, DCRIT * n, s), ("ctrl", n, None, None, s)]
    return t


def timing():
    ndc = chosen_ndc()
    tasks = ([("B", N3K, f, ndc[f], 0) for f in F_D_LIST] + [("C", N3K, F_D_LIST[-1], ndc[F_D_LIST[-1]], 0)]
             + [("B", n, None, DCRIT * n, 0) for n in SIZES_1B]
             + [("ctrl", N3K, F_D_LIST[0], None, 0)] + [("ctrl", n, None, None, 0) for n in SIZES_1B])
    t0 = time.time()
    with mp.Pool(len(tasks)) as pool:
        out = pool.map(run_one, tasks)
    for task, rec, dt in out:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  {task[0]:4s} N {task[1]:>6,} f_D {task[2]} ndc {task[3]}: {dt:6.1f}s "
              f"(last active day {last})")
    print(f"  wall {time.time() - t0:.1f}s for {len(tasks)} runs in parallel")


def _key(task):
    kind, n, f, ndc, s = task
    return f"{kind}|{n}|{f}|{s}"


def simulate(stage):
    """stage 'main' = 1a step B + controls and 1b; stage 'C' = step C at the best f_D."""
    os.makedirs(OUT, exist_ok=True)
    ndc = chosen_ndc()
    if stage == "main":
        tasks = tasks_main(ndc)
    else:
        best = json.load(open(os.path.join(OUT, "cheaper_plateau_scores.json")))["best_f_D"]
        tasks = [("C", N3K, best, ndc[best], s) for s in SEEDS]
    tasks.sort(key=lambda t: -t[1])
    arr = dict(np.load(CACHE)) if os.path.exists(CACHE) else {}
    t0, times = time.time(), []
    with mp.Pool(16) as pool:
        for task, rec, dt in pool.imap_unordered(run_one, tasks):
            for k, v in rec.items():
                arr[f"{_key(task)}#{k}"] = v
            times.append(dt)
    print(f"{len(tasks)} simulations {(time.time() - t0) / 60:.1f} min (per run {min(times):.1f}-"
          f"{max(times):.1f}s)")
    np.savez_compressed(CACHE, **arr)


def summarise(a, kind, n, f, ctrl_f):
    import step3_shape_metrics as sm
    from step5_arm3_runs import mean_sem
    get = lambda k_, ff, key: np.array([a[f"{k_}|{n}|{ff}|{s}#{key}"] for s in SEEDS])  # noqa: E731
    inc, prev, exp_, S = (get(kind, f, k) for k in ("incidence", "prevalence", "exposed", "S"))
    incc, prevc, Sc = (get("ctrl", ctrl_f, k) for k in ("incidence", "prevalence", "S"))
    m3 = np.array([sm.duration(y) for y in inc])
    m3c = np.array([sm.duration(y) for y in incc])
    ratio = m3 / m3c
    rng = np.random.default_rng(pc.BOOT_SEED)
    boot = rng.integers(0, len(SEEDS), size=(pc.N_BOOT, len(SEEDS)))
    bt = [m3[i].mean() / m3c[i].mean() for i in boot]
    dI = mean_sem(prev.max(1) - prevc.max(1))
    active = (exp_ + prev) > 0
    hkey = "H_sub" if kind == "B" else "H_eod"
    H = get(kind, f, hkey)
    h_main = [float(h[ac].mean()) if ac.any() else 0.0 for h, ac in zip(H, active)]
    return dict(n_seeds=len(SEEDS), stretch=float(m3.mean() / m3c.mean()),
                stretch_ci=tuple(float(x) for x in np.percentile(bt, [2.5, 97.5])),
                median=float(np.median(ratio)), ge10=int((ratio >= 10).sum()),
                gt15=int((ratio > 1.5).sum()), m3=float(m3.mean()), m3_ctrl=float(m3c.mean()),
                peak_red=float(-dI[0] / prevc.max(1).mean() * 100), peak_sems=float(dI[0] / dI[1]),
                final_S=float(S[:, -1].mean()), final_S_sd=float(S[:, -1].std(ddof=1)),
                final_S_ctrl=float(Sc[:, -1].mean()), attack=float(1 - S[:, -1].mean()),
                active_600=int(active[:, -1].sum()),
                last_active=sorted(int(np.nonzero(ac)[0].max()) + 1 if ac.any() else 0 for ac in active),
                H_main_mean=float(np.mean(h_main)), H_main_range=(float(min(h_main)), float(max(h_main))),
                H_measure=("sub-step mean (C43)" if kind == "B" else "end-of-day"))


def _print(label, r):
    print(f"\n{label}")
    print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
          f"{' (TRUNCATED: runs active at 600)' if r['active_600'] else ''}; median x{r['median']:.2f}; "
          f">=x10 {r['ge10']}/{r['n_seeds']}; >x1.5 {r['gt15']}/{r['n_seeds']}; T10-90 {r['m3']:.1f} vs "
          f"control {r['m3_ctrl']:.1f} d")
    print(f"  peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
          f"(SD {r['final_S_sd']:.4f}; control {r['final_S_ctrl']:.4f}); attack {r['attack']:.4f}")
    print(f"  active at day 600 {r['active_600']}/{r['n_seeds']}; last active day {r['last_active']}; "
          f"mean people in H over the main phase {r['H_main_mean']:.2f} ({r['H_measure']}; per-run "
          f"{r['H_main_range'][0]:.2f}-{r['H_main_range'][1]:.2f})")


def score():
    from population import build_population
    a = dict(np.load(CACHE))
    ndc = chosen_ndc()
    vul = build_population(N=N3K, seed=0).vulnerability
    out = {"ndc": {str(f): ndc[f] for f in F_D_LIST}, "cases": {}}
    print("Capped bands / realised mean f_D (N = 3,000 frozen population):")
    import population as popmod
    bands = np.asarray(popmod.IFR_10AGE, float)
    for f in F_D_LIST:
        scaled = bands * f / F_D_REF
        capped = [int(b) for b in np.nonzero(scaled > 1.0)[0]]
        fa = f_D_array(vul, f)
        out["cases"][f"cap|{f}"] = dict(capped_bands=capped, max_band_fD=float(scaled.max()),
                                        mean_fD=float(fa.mean()))
        print(f"  f_D {f}: capped bands {capped or 'none'}; largest band value {scaled.max():.4f}; "
              f"realised population mean {fa.mean():.6f}")
    for f in F_D_LIST:
        r = summarise(a, "B", N3K, f, f)
        r["ndc"] = ndc[f]
        out["cases"][f"1a_B|{f}"] = r
        _print(f"1a step B, N = 3,000, f_D = {f}, N*delta_c = {ndc[f]:.4g}", r)
    best = max(F_D_LIST, key=lambda f: (out["cases"][f"1a_B|{f}"]["stretch"], -f))
    out["best_f_D"] = best
    print(f"\nbest f_D (largest step-B mean stretch; tie -> smaller f_D): {best}")
    if f"C|{N3K}|{best}|0#incidence" in a:
        r = summarise(a, "C", N3K, best, best)
        r["ndc"] = ndc[best]
        out["cases"][f"1a_C|{best}"] = r
        _print(f"1a step C, N = 3,000, f_D = {best}, N*delta_c = {ndc[best]:.4g} (perceived 28-day "
               f"reported signal, daily, p = 1.0)", r)
    for n in SIZES_1B:
        r = summarise(a, "B", n, None, None)
        r["ndc"] = DCRIT * n
        out["cases"][f"1b_B|{n}"] = r
        _print(f"1b step B, N = {n:,}, N*delta_c = {DCRIT * n:.3g}", r)
    json.dump(out, open(os.path.join(OUT, "cheaper_plateau_scores.json"), "w"), indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


if __name__ == "__main__":
    mp.freeze_support()
    if "--ode" in sys.argv:
        step_ode()
    if "--timing" in sys.argv:
        timing()
    if "--sim" in sys.argv:
        simulate("main")
    if "--simC" in sys.argv:
        simulate("C")
    if "--score" in sys.argv:
        score()
