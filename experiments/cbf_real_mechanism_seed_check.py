"""
Follow-up to C18/C21: does the gap at N=3,000/10,000 survive more seeds, or
was it noise that a 30-seed SEM couldn't rule out? N=30,000 already cleared
~2 SEMs at 30 seeds (C18) and is left alone here. No model or reference
changes -- same run_cbf_behaviour, same DDE reference, same parameters
(beta_B=0.5, mu_B=0.01, gamma_beh=1, 28-day window), same days=900/48
sub-steps -- only the seed count changes, 30 -> 90.

UPDATE (register C21/C22): r is now per-agent (r_i = 1 - response_efficacy_i,
from a real src/population.py Population), not the flat r_factor=0.5 this
script originally used -- imports build_population and constructs one
Population per N, same POPULATION_SEED convention as cbf_real_mechanism_test.py.
The DDE reference is unchanged and still assumes a flat r (see that module).
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cbf_real_mechanism_test import (  # noqa: E402
    _worker, ode_final_S, DAYS, N_SUBSTEPS, POPULATION_SEED,
)
from population import build_population  # noqa: E402

N_SEEDS = 90
N_VALUES = [3_000, 10_000]


def main(n_seeds=N_SEEDS):
    ode_targets = {}
    for N in N_VALUES:
        ode_S, ode_H = ode_final_S(N)
        ode_targets[N] = ode_S
        print(f"N={N:,}: ODE final S = {ode_S:.5f}, ODE final H = {ode_H:.2f}")
    print(flush=True)

    populations = {N: build_population(N=N, seed=POPULATION_SEED) for N in N_VALUES}
    for N in N_VALUES:
        re = populations[N].response_efficacy
        print(f"N={N:,}: population built (seed={POPULATION_SEED}), "
              f"response_efficacy mean={re.mean():.4f} (r_i mean={1-re.mean():.4f})")
    print(flush=True)

    tasks = [
        (N, seed, populations[N].response_efficacy)
        for N in N_VALUES for seed in range(n_seeds)
    ]
    results = {N: {"S": [None] * n_seeds, "peakD": [None] * n_seeds} for N in N_VALUES}
    t_start = time.time()
    done = 0
    with mp.Pool(min(len(tasks), 16)) as pool:
        for N, seed, s_final, peak_d, dt in pool.imap_unordered(_worker, tasks):
            results[N]["S"][seed] = s_final
            results[N]["peakD"][seed] = peak_d
            done += 1
            print(f"[{done}/{len(tasks)}] N={N} seed={seed} final_S={s_final:.5f} "
                  f"peak_daily_deaths={peak_d:.0f} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)",
                  flush=True)

    print(f"\n=== SUMMARY (real CBF mechanism, {n_seeds} seeds -- follow-up to C18's 30-seed result) ===")
    summary = {"days": DAYS, "n_substeps": N_SUBSTEPS, "n_seeds": n_seeds, "results": {}}
    for N in N_VALUES:
        ode_S = ode_targets[N]
        s_arr = np.array([v for v in results[N]["S"] if v is not None])
        d_arr = np.array([v for v in results[N]["peakD"] if v is not None])
        n_used = len(s_arr)
        mean_S = float(s_arr.mean())
        sem_S = float(s_arr.std(ddof=1) / np.sqrt(n_used))
        rel_err = abs(mean_S - ode_S) / ode_S
        gap_sems = (mean_S - ode_S) / sem_S
        summary["results"][str(N)] = {
            "ode_final_S": ode_S, "finals_S": results[N]["S"], "finals_peakD": results[N]["peakD"],
            "n_seeds_used": n_used, "mean_final_S": mean_S, "sem_final_S": sem_S,
            "relative_error": rel_err, "gap_sems": gap_sems,
            "mean_peak_daily_deaths": float(d_arr.mean()),
        }
        print(f"N={N:>7,}: {n_used}/{n_seeds} seeds, "
              f"mean peak daily deaths = {d_arr.mean():.1f}, "
              f"mean final S = {mean_S:.5f} (ODE {ode_S:.5f}), "
              f"relative error = {rel_err*100:.2f}% ({gap_sems:.2f} SEMs)")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "cbf_real_mechanism_seed_check.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
