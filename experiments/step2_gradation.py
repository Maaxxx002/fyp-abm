"""
Gradation sweep (register C26): does arm 1's behavioural response grade with gamma_beh?

Foundation (step2_common.FOUNDATION: real CBF, flat r=0.5 (A29), beta_B=0.5, mu_B=0.01,
window 28, detection 0.7 (A25), per-agent f_D (A26), Weitz disease, 48 sub-steps, 10 initial
infected, 900 days), frozen quota population per N. Sweep gamma_beh in {0.25, 0.5, 1, 2, 4}
x Gozzi's sourced default -- a sensitivity sweep, not a calibration -- at N in {1,000, 3,000}.
One no-behaviour control per N (beta_B=0; gamma_beh irrelevant). Seeds 0-29 for every config.

Pass marks (A27/A28): (a) vs the N's control; (b) vs the DDE at that gamma_beh, with the
90-seed re-run if INCONCLUSIVE.
GRADED pass mark (fixed before running): final S monotonic non-decreasing in gamma_beh AND at
least 2 of the 4 adjacent steps differ by > 2 SEM (paired, same seeds). Classification:
GRADED / SWITCH (exactly one significant step) / FLAT (no significant step); a non-monotonic
sweep with >= 2 significant steps is reported as NON-MONOTONIC.

Usage:  python experiments/step2_gradation.py [--timing]
"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step2_common as c  # noqa: E402

N_VALUES = [1_000, 3_000]
GAMMAS = [0.25, 0.5, 1.0, 2.0, 4.0]
SEEDS = list(range(30))


def configs():
    cfgs = {}
    for N in N_VALUES:
        cfgs[f"N{N}_ctrl"] = dict(c.FOUNDATION, N=N, behaviour=False)
        for g in GAMMAS:
            cfgs[f"N{N}_g{g}"] = dict(c.FOUNDATION, N=N, gamma_beh=g)
    return cfgs


def classify(means, step_sems):
    monotonic = all(b >= a for a, b in zip(means, means[1:]))
    n_sig = sum(abs(z) > 2 for z in step_sems)
    if n_sig == 0:
        cls = "FLAT"
    elif n_sig == 1:
        cls = "SWITCH"
    elif monotonic:
        cls = "GRADED"
    else:
        cls = "NON-MONOTONIC"
    return dict(monotonic=monotonic, n_significant_steps=n_sig, classification=cls,
                passes=cls == "GRADED")


def main():
    cfgs = configs()
    if "--timing" in sys.argv:
        res, times, _ = c.run_pool([(k, v, 0) for k, v in cfgs.items()])
        for k, v in times.items():
            print(f"  {k:12s} seed 0: {v[0]:.1f}s")
        return

    res, _, wall = c.run_pool([(k, v, s) for k, v in cfgs.items() for s in SEEDS])
    print(f"Wall time {wall/60:.1f} min; seeds 0-29 per config.")
    summary = {}
    for N in N_VALUES:
        ctrl = f"N{N}_ctrl"
        print(f"\n=== N={N:,} ===")
        c.print_stats(res, ctrl, SEEDS, behaviour=False)
        block = {"points": {}}
        for g in GAMMAS:
            name = f"N{N}_g{g}"
            print(f"\n--- gamma_beh = {g}")
            c.print_stats(res, name, SEEDS)
            m, se, n = c.mean_sem(c.values(res, name, "adoption_at_peak_signal", SEEDS))
            ms, ses, _ = c.mean_sem(c.values(res, name, "peak_signal", SEEDS))
            print(f"  peak death signal {ms:.3f} +/- {ses:.3f}; adoption rate there "
                  f"{m:.4f} +/- {se:.4f} /day (beta_B cap {c.BETA_B}) (n={n})")
            pa = c.pass_a(res, name, ctrl, SEEDS)
            c.print_pass_a(f"vs N={N} control", pa)
            ref = c.dde_final_S(cfgs[name])
            pbs = c.pass_b_with_rerun(res, name, cfgs[name], ref, SEEDS)
            for pb in pbs:
                c.print_pass_b(f"n={pb['n']}", pb)
            point = {"pass_a": pa, "pass_b": pbs,
                     "adoption_at_peak_signal": dict(mean=m, sem=se, n=n),
                     "peak_signal": dict(mean=ms, sem=ses, n=n)}
            for key in ("final_S", "peak_I", "peak_SB", "peak_daily_deaths"):
                mm, ss, nn = c.mean_sem(c.values(res, name, key, SEEDS))
                point[key] = dict(mean=mm, sem=ss, n=nn)
            block["points"][str(g)] = point

        print(f"\n--- Gradation, N={N:,} (paired adjacent steps, seeds 0-29)")
        means, steps = [], []
        for g in GAMMAS:
            means.append(block["points"][str(g)]["final_S"]["mean"])
        for g0, g1 in zip(GAMMAS, GAMMAS[1:]):
            d = c.paired(res, f"N{N}_g{g1}", f"N{N}_g{g0}", "final_S", SEEDS)
            dI = c.paired(res, f"N{N}_g{g1}", f"N{N}_g{g0}", "peak_I", SEEDS)
            steps.append(d)
            print(f"  gamma {g0} -> {g1}: final S {c.fmt_paired(d)}; peak I {c.fmt_paired(dI)}")
        cl = classify(means, [d["sems"] for d in steps])
        print(f"  final S means: {[round(x, 5) for x in means]}; monotonic: {cl['monotonic']}; "
              f"significant steps: {cl['n_significant_steps']}/4 -> {cl['classification']}")
        block["steps_final_S"] = steps
        block["gradation"] = cl
        block["all_pass_a"] = all(p["pass_a"]["passes"] for p in block["points"].values())
        block["all_pass_b"] = all(p["pass_b"][-1]["verdict"] == "PASS"
                                  for p in block["points"].values())
        summary[str(N)] = block

    out = dict(seeds=SEEDS, gammas=GAMMAS, summary=summary, per_seed=res)
    path = os.path.join(HERE, "..", "results", "step2_gradation.json")
    json.dump(out, open(path, "w"), indent=2, default=str)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
