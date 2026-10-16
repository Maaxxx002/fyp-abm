"""
Step 9 (register C51). Capability test, NOT an arm. No API calls.

Every case: step C (agents' own mean of 70%-reported deaths, decisions once per day at the start
of the day, p = 1, A55 stop) with a 7-DAY mean instead of A24's 28 days; 10 seeds (0-9); own
AlwaysNormal control on the same seeds; C42 pass mark; E26 as revised in C50.
  9a  N = 15,000 and 20,000, normal per-agent f_D, C43 per-capita delta_c (N*delta_c 0.075 / 0.10)
  9b  N = 3,000, f_D in {0.05, 0.10}, N*delta_c = half the C45 edge (as C48: 0.2228 / 0.4446)
  9c  N = 3,000, normal f_D, C43 per-capita delta_c (N*delta_c 0.015)

Usage:  python experiments/step9_7day_signal.py --timing | --sim | --score
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

SEEDS = s8.SEEDS
CACHE = os.path.join(cp.OUT, "step9_runs.npz")


def cases():
    nd = s8.ndc_8b()
    c = [(f"9a step C 7-day, N = {n:,}", "C", n, None, 7, cp.DCRIT * n) for n in (15_000, 20_000)]
    c += [(f"9b step C 7-day, N = 3,000, f_D {f}", "C", cp.N3K, f, 7, nd[f]) for f in s8.F_D_8B]
    c.append(("9c step C 7-day, N = 3,000, normal f_D", "C", cp.N3K, None, 7, cp.DCRIT * cp.N3K))
    return c


def tasks():
    t, ctrl = [], set()
    for _, kind, n, f, w, ndc in cases():
        for s in SEEDS:
            t.append((kind, n, f, ndc, s, w))
        ctrl.add((n, f))
    for n, f in sorted(ctrl, key=str):
        t += [("ctrl", n, f, None, s, 28) for s in SEEDS]   # window has no effect without decisions
    return t


def timing():
    tt = [x for x in tasks() if x[4] == 0]
    t0 = time.time()
    with mp.Pool(16) as pool:
        out = pool.map(cp.run_one, tt)
    for task, rec, dt in out:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  {s8.key(task):32s} {dt:6.1f}s (last active day {last})")
    print(f"  wall {time.time() - t0:.1f}s for {len(tt)} runs (16 workers)")


def simulate():
    tt = sorted(tasks(), key=lambda x: -x[1])
    arr, times, t0 = {}, [], time.time()
    with mp.Pool(16) as pool:
        for task, rec, dt in pool.imap_unordered(cp.run_one, tt):
            for k, v in rec.items():
                arr[f"{s8.key(task)}#{k}"] = v
            times.append(dt)
    print(f"{len(tt)} simulations {(time.time() - t0) / 60:.1f} min (per run {min(times):.1f}-{max(times):.1f}s)")
    np.savez_compressed(CACHE, **arr)


def score():
    a = dict(np.load(CACHE))
    out = {}
    fm = lambda x: "undef" if x is None else f"{x:+.3f}"  # noqa: E731
    for label, kind, n, f, w, ndc in cases():
        r = s8.summarise(a, kind, n, f, w)
        g = lambda k: np.array([a[f"{kind}|{n}|{f}|{w}|{s}#{k}"] for s in SEEDS])  # noqa: E731
        sig = np.round(np.array([s8.signal28(d) for d in g("deaths")]), 12)   # deaths_28day_mean (E24)
        e = s8.per_run_rev(sig, g("caution"), g("prevalence"), g("exposed"), g("S"))
        r.update(ndc=ndc, e26=e)
        out[label] = r
        print(f"\n{label} (N*delta_c {ndc:.4g})")
        print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
              f"{' (TRUNCATED)' if r['active_600'] else ''}; median x{r['median']:.2f}; >=x10 {r['ge10']}/10; "
              f">x1.5 {r['gt15']}/10; T10-90 {r['m3']:.1f} vs control {r['m3_ctrl']:.1f} d")
        print(f"  peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
              f"(SD {r['final_S_sd']:.4f}; control {r['final_S_ctrl']:.4f}); attack {r['attack']:.4f}")
        print(f"  active at day 600 {r['active_600']}/10; last active {r['last_active']}; mean people in H "
              f"(main phase, end-of-day) {r['H_main_mean']:.2f} ({r['H_main_range'][0]:.2f}-{r['H_main_range'][1]:.2f}); "
              f"C42 pass mark {'MET' if r['c42_pass'] else 'NOT MET'}")
        print(f"  E26 (C50): max-lag DR {fm(e['drL_mean'])} / {fm(e['drL_median'])} ({e['drL_defined']}), best lag "
              f"{e['lag_median']} {e['lag_range']}; lag-0 DR {fm(e['dr0_mean'])}; caution SD "
              f"{'undef' if e['sd_mean'] is None else format(e['sd_mean'], '.3f')}; runs meeting (i)/(ii)/(iii)/all "
              f"{e['pass_iL']}/{e['pass_ii']}/{e['pass_iii']}/{e['all_rev']} -> {e['verdict_rev']}")
    json.dump(out, open(os.path.join(cp.OUT, "step9_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--timing", timing), ("--sim", simulate), ("--score", score)):
        if flag in sys.argv:
            fn()
