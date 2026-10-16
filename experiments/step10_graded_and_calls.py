"""
Step 10 (register C52). No API calls (arm 2 is replaced by a fixed stub; nothing is sent anywhere).

  10a  Graded-ness at N = 15,000 with the agents' own 7-day signal (step C: 70%-reported deaths,
       daily decisions, p = 1, A55 stop; Weitz's q = 1 - g, k = 2). Per-capita delta_c grid
       {1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 3e-4, 5e-4}; N*delta_c = delta_c * N.
       Spread = max - min over grid points of the mean final S (C5's arithmetic). Primary grid =
       C7's range [1e-6, 3e-4]; also C5's grid {1e-6, 5e-6, 2e-5, 1e-4, 5e-4} and its 20x
       sub-range {1e-6, 5e-6, 2e-5}. 10 seeds, S1.
  10b  Exact arm-2 call count: arm 2's decision loop (shared world, never-ill agents re-asked with
       p = 0.3/day, A55 stop) with a stub returning a fixed answer, S1, 600 days. Stubs
       A/B/C = 10/60/30 and 40/50/10. N = 3,000 (seeds 0-29; 0-9 reported separately),
       N = 10,000 and 15,000 (seeds 0-9). Calls = agents asked.
  10c  Step C with the 7-day signal at N = 10,000 (as C51 9a), 10 seeds.

Usage:  python experiments/step10_graded_and_calls.py --timing | --sim | --score
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
import step7_cheaper_plateau as cp  # noqa: E402
import step8_plateau_followup as s8  # noqa: E402
from shared_world import DecisionFunction, NORMAL, PRECAUTIONS, STAY_HOME  # noqa: E402

SEEDS = list(range(10))
N_DIAL = 15_000
DIAL = [1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 3e-4, 5e-4]
GRID_C7 = [d for d in DIAL if d <= 3e-4]
GRID_C5 = [1e-6, 5e-6, 2e-5, 1e-4, 5e-4]
GRID_20X = [1e-6, 5e-6, 2e-5]
SPREAD_PASS = 0.593
STUBS = {"10/60/30": (0.10, 0.60, 0.30), "40/50/10": (0.40, 0.50, 0.10)}
CALL_SEEDS = {3000: range(30), 10_000: range(10), 15_000: range(10)}
COST_PER_CALL = 0.0000427                 # C34: thinking OFF, measured mean
OUT = cp.OUT
CACHE = os.path.join(OUT, "step10_runs.npz")
CALLS_JSON = os.path.join(OUT, "step10_calls.json")
_POP = {}


class Arm2Stub(DecisionFunction):
    """Arm 2's decision loop with the LLM replaced by a fixed answer (probabilities for stay home /
    precautions / normal, A56); the action is drawn from the decision stream as for arm 3 (A52).
    Counts every agent asked (= one LLM call each; no retries, since the stub is always valid)."""
    mode = "discrete"
    redecides = True

    def __init__(self, probs):
        self.p_home, self.p_prec, _ = probs
        self.calls = []

    def decide(self, day, agents, view, rng):
        self.calls.append((day, len(agents)))
        u = rng.random(len(agents))
        return np.where(u < self.p_home, STAY_HOME,
                        np.where(u < self.p_home + self.p_prec, PRECAUTIONS, NORMAL)).astype(np.int8)


def run_calls(task):
    stub, n, seed = task
    from population import build_population
    from shared_world import run_shared_world
    if n not in _POP:
        _POP[n] = build_population(N=n, seed=0)
    d = Arm2Stub(STUBS[stub])
    t0 = time.time()
    o = run_shared_world(N=n, seed=seed, decision=d, days=600, f_D=_POP[n].vulnerability, window=28,
                         detection_rate=0.7, R0=3.0, T_H=14.0, redecide_prob=0.3,
                         stop_deciding_when_no_infection=True)
    calls = int(sum(c for _, c in d.calls))
    return task, dict(calls=calls, ask_days=len(d.calls), final_S=float(o["S"][-1]),
                      max_per_day=int(max((c for _, c in d.calls), default=0))), time.time() - t0


def dial_tasks():
    t = [("C", N_DIAL, None, dc * N_DIAL, s, 7) for dc in DIAL for s in SEEDS]
    t += [("ctrl", N_DIAL, None, None, s, 28) for s in SEEDS]
    return t


def c10_tasks():
    return ([("C", 10_000, None, cp.DCRIT * 10_000, s, 7) for s in SEEDS]
            + [("ctrl", 10_000, None, None, s, 28) for s in SEEDS])


def call_tasks():
    return [(stub, n, s) for stub in STUBS for n, ss in CALL_SEEDS.items() for s in ss]


def dkey(task):
    """10c runs (N = 10,000, one delta_c) use step 8's key so s8.summarise reads them directly;
    10a dial runs also carry N*delta_c."""
    kind, n, f, ndc, s, w = task
    if n == 10_000:
        return s8.key(task)
    return f"{kind}|{n}|{f}|{w}|{'' if ndc is None else f'{ndc:.6g}'}|{s}"


def timing():
    sim = [t for t in dial_tasks() + c10_tasks() if t[4] == 0]
    calls = [(stub, n, 0) for stub in STUBS for n in CALL_SEEDS]
    t0 = time.time()
    with mp.Pool(16) as pool:
        a = pool.map_async(cp.run_one, sim)
        b = pool.map(run_calls, calls)
        a = a.get()
    for task, rec, dt in a:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  {dkey(task):36s} {dt:6.1f}s (last active day {last})")
    for task, r, dt in b:
        print(f"  stub {task[0]} N {task[1]:>6,}: {dt:6.1f}s, {r['calls']:,} calls over {r['ask_days']} days")
    print(f"  wall {time.time() - t0:.1f}s for {len(sim) + len(calls)} runs (16 workers)")


def simulate():
    sim = sorted(dial_tasks() + c10_tasks(), key=lambda x: -x[1])
    t0, arr, times = time.time(), {}, []
    with mp.Pool(16) as pool:
        calls = pool.map_async(run_calls, call_tasks())
        for task, rec, dt in pool.imap_unordered(cp.run_one, sim):
            for k, v in rec.items():
                arr[f"{dkey(task)}#{k}"] = v
            times.append(dt)
        calls = calls.get()
    np.savez_compressed(CACHE, **arr)
    json.dump([dict(stub=t[0], N=t[1], seed=t[2], **r) for t, r, _ in calls], open(CALLS_JSON, "w"), indent=1)
    print(f"{len(sim)} simulations + {len(calls)} call-count runs {(time.time() - t0) / 60:.1f} min "
          f"(simulation per run {min(times):.1f}-{max(times):.1f}s)")


def score():
    a = dict(np.load(CACHE))
    out = {}
    # ---- 10a
    fs_ctrl = np.array([a[f"{dkey(('ctrl', N_DIAL, None, None, s, 28))}#S"][-1] for s in SEEDS])
    print(f"10a  N = {N_DIAL:,}, step C, 7-day signal; control final S {fs_ctrl.mean():.4f}")
    print("  per-capita delta_c | N*delta_c | mean final S (SD) | runs active at 600")
    fs = {}
    for dc in DIAL:
        S = np.array([a[f"{dkey(('C', N_DIAL, None, dc * N_DIAL, s, 7))}#S"][-1] for s in SEEDS])
        n_act = int(sum((a[f"{dkey(('C', N_DIAL, None, dc * N_DIAL, s, 7))}#exposed"][-1]
                         + a[f"{dkey(('C', N_DIAL, None, dc * N_DIAL, s, 7))}#prevalence"][-1]) > 0 for s in SEEDS))
        fs[dc] = dict(mean=float(S.mean()), sd=float(S.std(ddof=1)), active_600=n_act)
        print(f"  {dc:8.0e} | {dc * N_DIAL:7.3f} | {S.mean():.4f} ({S.std(ddof=1):.4f}) | {n_act}/10")
    spreads = {}
    for name, grid in (("C7 range [1e-6, 3e-4] (primary)", GRID_C7), ("C5 grid (500x)", GRID_C5),
                       ("C5 20x sub-range", GRID_20X)):
        v = [fs[d]["mean"] for d in grid]
        spreads[name] = float(max(v) - min(v))
        mono = all(x >= y for x, y in zip(v, v[1:]))
        print(f"  spread, {name}: {spreads[name]:.3f} (max {max(v):.4f} at {grid[int(np.argmax(v))]:.0e}, "
              f"min {min(v):.4f} at {grid[int(np.argmin(v))]:.0e}; non-increasing in delta_c: {mono})")
    p = spreads["C7 range [1e-6, 3e-4] (primary)"]
    print(f"  pass rule: graded if primary spread >= {SPREAD_PASS} -> {'GRADED' if p >= SPREAD_PASS else 'NOT GRADED'}"
          f" (C7 references: N 10,000 + 7-day 0.629; N 3,000 + 28-day 0.593)")
    out["10a"] = dict(final_S=fs, control_final_S=float(fs_ctrl.mean()), spreads=spreads,
                      graded=bool(p >= SPREAD_PASS))
    # ---- 10c (same columns as C51)
    b = a
    r = s8.summarise(b, "C", 10_000, None, 7)
    g = lambda k: np.array([b[f"C|10000|None|7|{s}#{k}"] for s in SEEDS])  # noqa: E731
    sig = np.round(np.array([s8.signal28(d) for d in g("deaths")]), 12)
    e = s8.per_run_rev(sig, g("caution"), g("prevalence"), g("exposed"), g("S"))
    r["e26"] = e
    out["10c"] = r
    print(f"\n10c  step C, 7-day signal, N = 10,000 (N*delta_c {cp.DCRIT * 10_000:.3g})")
    print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
          f"{' (TRUNCATED)' if r['active_600'] else ''}; median x{r['median']:.2f}; >=x10 {r['ge10']}/10; "
          f"peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
          f"(SD {r['final_S_sd']:.4f}; control {r['final_S_ctrl']:.4f}); attack {r['attack']:.4f}")
    print(f"  active at day 600 {r['active_600']}/10; last active {r['last_active']}; mean people in H "
          f"(end-of-day) {r['H_main_mean']:.2f} ({r['H_main_range'][0]:.2f}-{r['H_main_range'][1]:.2f}); "
          f"C42 pass mark {'MET' if r['c42_pass'] else 'NOT MET'}")
    print(f"  E26: max-lag DR {e['drL_mean']:+.3f} (best lag {e['lag_median']} {e['lag_range']}); caution SD "
          f"{e['sd_mean']:.3f}; runs meeting (i)/(ii)/(iii)/all {e['pass_iL']}/{e['pass_ii']}/{e['pass_iii']}/"
          f"{e['all_rev']} -> {e['verdict_rev']}")
    # ---- 10b
    rows = json.load(open(CALLS_JSON))
    print(f"\n10b  arm-2 call count, stub decision loop, S1, p = 0.3, A55 stop; ${COST_PER_CALL} per call (C34), +/-30% band")
    print("  stub | N | seeds | calls per run mean (SD, min-max) | asking days mean | total calls | cost total "
          "[-30%, +30%] | stub final S")
    out["10b"] = []
    for stub in STUBS:
        for n, ss in [(3000, range(10)), (3000, range(30)), (10_000, range(10)), (15_000, range(10))]:
            rr = [x for x in rows if x["stub"] == stub and x["N"] == n and x["seed"] in ss]
            c = np.array([x["calls"] for x in rr])
            tot = int(c.sum())
            cost = tot * COST_PER_CALL
            row = dict(stub=stub, N=n, seeds=len(rr), mean=float(c.mean()), sd=float(c.std(ddof=1)),
                       min=int(c.min()), max=int(c.max()), ask_days=float(np.mean([x["ask_days"] for x in rr])),
                       total=tot, cost=cost, cost_lo=0.7 * cost, cost_hi=1.3 * cost,
                       per_run_cost=float(c.mean()) * COST_PER_CALL,
                       final_S=float(np.mean([x["final_S"] for x in rr])))
            out["10b"].append(row)
            print(f"  {stub} | {n:>6,} | {len(rr)} | {row['mean']:,.0f} ({row['sd']:,.0f}, {row['min']:,}-{row['max']:,}) | "
                  f"{row['ask_days']:.1f} | {tot:,} | ${cost:,.2f} [${0.7 * cost:,.2f}, ${1.3 * cost:,.2f}] | "
                  f"{row['final_S']:.4f}")
    json.dump(out, open(os.path.join(OUT, "step10_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--timing", timing), ("--sim", simulate), ("--score", score)):
        if flag in sys.argv:
            fn()
