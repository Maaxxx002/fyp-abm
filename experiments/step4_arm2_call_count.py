"""
Arm-2 call budget under A38/A42: only never-ill, alive agents (true S or E) decide, each asked
with probability p = 0.3/day (A41, provisional, unsourced). Expected calls per run =
p x (deciding agent-days).

Two reference epidemics (arm 2's own epidemic is not known until it runs): the no-behaviour
control (AlwaysNormal) and arm 1 (CBFArm1), both in run_shared_world, foundation, N=3,000,
600 days, S1/S2/S3, seeds 0-29.

Deciders on day t = agents never ill at the START of day t = (S + E) at the end of day t-1
(day 0: N - 10). With E19 ("stop once E+I = 0"), day t is counted only while E + I > 0 at the
start of day t (day 0 always counted).

Usage:  python experiments/step4_arm2_call_count.py
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from population import build_population  # noqa: E402
from shared_world import AlwaysNormal, CBFArm1, run_shared_world  # noqa: E402

N, DAYS, SEEDS, P = 3_000, 600, list(range(30)), 0.3
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
REFS = {"control": AlwaysNormal, "arm1": CBFArm1}
OUT = os.path.join(HERE, "..", "results", "step4")
_POP = {}


def worker(task):
    ref, scen, seed = task
    if "p" not in _POP:
        _POP["p"] = build_population(N=N, seed=0)
    out = run_shared_world(N=N, seed=seed, decision=REFS[ref](), days=DAYS, seeds_infected=10,
                           f_D=_POP["p"].vulnerability, window=28, detection_rate=0.7,
                           **SCEN[scen])
    s_count = np.rint(out["S"] * N)
    never_ill_end = s_count + out["exposed"]                  # end of day t
    active_end = out["exposed"] + out["prevalence"] > 0
    deciders = np.concatenate([[N - 10], never_ill_end[:-1]])  # start of day t
    active_start = np.concatenate([[True], active_end[:-1]])
    return ref, scen, seed, float(deciders.sum()), float(deciders[active_start].sum()), \
        int(active_start.sum())


def stats(x):
    x = np.asarray(x, float)
    return dict(mean=float(x.mean()), sd=float(x.std(ddof=1)), min=float(x.min()),
                max=float(x.max()), n=len(x))


def main():
    t0 = time.time()
    tasks = [(r, s, x) for r in REFS for s in SCEN for x in SEEDS]
    with mp.Pool(16) as pool:
        rows = pool.map(worker, tasks)
    res = {}
    for ref, scen, seed, full, e19, days_active in rows:
        d = res.setdefault(ref, {}).setdefault(scen, dict(full=[], e19=[], days=[]))
        d["full"].append(full); d["e19"].append(e19); d["days"].append(days_active)
    out = dict(p=P, N=N, days=DAYS, seeds=len(SEEDS),
               upper_bound_per_run=P * N * DAYS, wall_s=time.time() - t0, refs={})
    print(f"{len(rows)} runs in {out['wall_s']:.0f}s. Upper bound per run (all {N} agents, "
          f"{DAYS} d): {P * N * DAYS:,.0f} calls")
    for ref in REFS:
        out["refs"][ref] = {}
        tot_full = tot_e19 = one_full = one_e19 = 0.0
        for scen in SCEN:
            d = res[ref][scen]
            cf = stats(P * np.array(d["full"])); ce = stats(P * np.array(d["e19"]))
            dd = stats(d["days"])
            out["refs"][ref][scen] = dict(calls_full=cf, calls_e19=ce, days_counted_e19=dd,
                                          total_30_full=P * sum(d["full"]),
                                          total_30_e19=P * sum(d["e19"]))
            tot_full += P * sum(d["full"]); tot_e19 += P * sum(d["e19"])
            one_full += cf["mean"]; one_e19 += ce["mean"]
            print(f"{ref:7s} {scen}: per run, no E19 {cf['mean']:,.0f} (sd {cf['sd']:,.0f}, "
                  f"{cf['min']:,.0f}-{cf['max']:,.0f}); with E19 {ce['mean']:,.0f} (sd {ce['sd']:,.0f}, "
                  f"{ce['min']:,.0f}-{ce['max']:,.0f}); days counted with E19 {dd['mean']:.1f} "
                  f"({dd['min']:.0f}-{dd['max']:.0f}); n={cf['n']}")
        out["refs"][ref]["three_scenarios_one_run_each"] = dict(full=one_full, e19=one_e19)
        out["refs"][ref]["three_scenarios_30_seeds"] = dict(full=tot_full, e19=tot_e19)
        print(f"{ref:7s} S1+S2+S3, one run each (mean): no E19 {one_full:,.0f}; with E19 "
              f"{one_e19:,.0f}.  30 seeds each (90 runs): no E19 {tot_full:,.0f}; with E19 "
              f"{tot_e19:,.0f}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "arm2_call_count.json"), "w"), indent=2)


if __name__ == "__main__":
    mp.freeze_support()
    main()
