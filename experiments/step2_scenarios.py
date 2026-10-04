"""
Scenario separation (register C27, closes E4): S1/S2/S3 from docs/Scenario_Spec.md with the
real CBF arm 1, at N in {1,000, 3,000}.

  S1  R0=3, T_H=14     S2  R0=2, T_H=14 (signal magnitude)     S3  R0=3, T_H=28 (signal timing)

Each with behaviour (step2_common.FOUNDATION: flat r=0.5, beta_B=0.5, mu_B=0.01, gamma_beh=1,
window 28, detection 0.7, per-agent f_D, latent 2 d / infectious 6 d, 48 sub-steps, 10 initial
infected, 900 days) and its own no-behaviour control (beta_B=0). Seeds 0-29 everywhere. Note:
Scenario_Spec's run length is 600 days; this uses the foundation's 900 as instructed.

Pass marks (A27/A28): (a) vs own control; (b) vs the DDE parameterised per scenario, with the
90-seed re-run if INCONCLUSIVE.
SEPARATION pass mark (fixed before running): S2's and S3's behavioural effect (paired
difference from own control) each differ from S1's by > 2 SEM in final S or peak I. The
effect difference is taken per seed, (S_k - ctrl_k) - (S1 - ctrl_1), then mean +/- SEM.
Also checked: S1 and S3 controls are identical in infections on the same seeds (T_H only
moves deaths).

Usage:  python experiments/step2_scenarios.py [--timing]
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
SCENARIOS = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0),
             "S3": dict(R0=3.0, T_H=28.0)}
SEEDS = list(range(30))


def configs():
    cfgs = {}
    for N in N_VALUES:
        for sc, p in SCENARIOS.items():
            cfgs[f"N{N}_{sc}"] = dict(c.FOUNDATION, N=N, **p)
            cfgs[f"N{N}_{sc}_ctrl"] = dict(c.FOUNDATION, N=N, behaviour=False, **p)
    return cfgs


def effect(res, N, sc, key):
    return (c.values(res, f"N{N}_{sc}", key, SEEDS)
            - c.values(res, f"N{N}_{sc}_ctrl", key, SEEDS))


def main():
    cfgs = configs()
    if "--timing" in sys.argv:
        res, times, _ = c.run_pool([(k, v, 0) for k, v in cfgs.items()])
        for k, v in times.items():
            print(f"  {k:14s} seed 0: {v[0]:.1f}s")
        return

    res, _, wall = c.run_pool([(k, v, s) for k, v in cfgs.items() for s in SEEDS])
    print(f"Wall time {wall/60:.1f} min; seeds 0-29 per config.")
    summary = {}
    for N in N_VALUES:
        print(f"\n=== N={N:,} ===")
        block = {"scenarios": {}}
        for sc in SCENARIOS:
            name, ctrl = f"N{N}_{sc}", f"N{N}_{sc}_ctrl"
            print(f"\n--- {sc} {SCENARIOS[sc]}")
            c.print_stats(res, name, SEEDS)
            c.print_stats(res, ctrl, SEEDS, behaviour=False)
            sb = {}
            for nm in (name, ctrl):
                for key in ("final_S", "peak_I", "peak_day", "peak_SB", "peak_daily_deaths"):
                    if key == "peak_SB" and nm == ctrl:
                        continue
                    m, se, n = c.mean_sem(c.values(res, nm, key, SEEDS))
                    sb[f"{'beh' if nm == name else 'ctrl'}_{key}"] = dict(mean=m, sem=se, n=n)
            for who in ("beh", "ctrl"):
                d = sb[f"{who}_peak_day"]
                print(f"  {who:4s} peak day {d['mean']:.1f} +/- {d['sem']:.1f} (n={d['n']})")
            pa = c.pass_a(res, name, ctrl, SEEDS)
            c.print_pass_a("vs own control (= behavioural effect)", pa)
            ref = c.dde_final_S(cfgs[name])
            pbs = c.pass_b_with_rerun(res, name, cfgs[name], ref, SEEDS)
            for pb in pbs:
                c.print_pass_b(f"n={pb['n']}", pb)
            block["scenarios"][sc] = dict(stats=sb, pass_a=pa, pass_b=pbs)

        print(f"\n--- Separation, N={N:,} (difference of behavioural effects vs S1, per seed)")
        sep = {}
        for sc in ("S2", "S3"):
            sep[sc] = {}
            for key in ("final_S", "peak_I"):
                m, se, n = c.mean_sem(effect(res, N, sc, key) - effect(res, N, "S1", key))
                sep[sc][key] = dict(mean_diff=m, sem_diff=se, n=n, sems=m / se)
                print(f"  {sc} - S1 effect on {key:8s}: {m:+.5f} +/- {se:.5f} "
                      f"({m/se:+.2f} SEM, n={n})")
            sep[sc]["separates"] = any(abs(sep[sc][k]["sems"]) > 2 for k in ("final_S", "peak_I"))
        sep["passes"] = sep["S2"]["separates"] and sep["S3"]["separates"]
        print(f"  S2 separates: {sep['S2']['separates']}; S3 separates: {sep['S3']['separates']}"
              f" -> SEPARATION {'PASS' if sep['passes'] else 'FAIL'}")
        block["separation"] = sep

        print(f"\n--- S1 vs S3 control identity in infections, N={N:,}")
        keys = ("final_S", "peak_I", "peak_day", "total_incidence")
        same = sum(all(res[f"N{N}_S1_ctrl"][s][k] == res[f"N{N}_S3_ctrl"][s][k] for k in keys)
                   for s in SEEDS)
        dd = c.mean_sem(c.values(res, f"N{N}_S3_ctrl", "peak_daily_deaths", SEEDS)
                        - c.values(res, f"N{N}_S1_ctrl", "peak_daily_deaths", SEEDS))
        print(f"  identical final S, peak I, peak day, total incidence on {same}/{len(SEEDS)} "
              f"seeds; peak daily deaths S3-S1 {dd[0]:+.3f} +/- {dd[1]:.3f} (n={dd[2]})")
        block["s1_s3_control_identical_infections"] = same
        block["all_pass_a"] = all(v["pass_a"]["passes"] for v in block["scenarios"].values())
        block["all_pass_b"] = all(v["pass_b"][-1]["verdict"] == "PASS"
                                  for v in block["scenarios"].values())
        summary[str(N)] = block

    out = dict(seeds=SEEDS, scenarios=SCENARIOS, summary=summary, per_seed=res)
    path = os.path.join(HERE, "..", "results", "step2_scenarios.json")
    json.dump(out, open(path, "w"), indent=2, default=str)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
