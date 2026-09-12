"""
Diagnostic for Decision_Register.md D11: does the ~4.56% direct-g bias (C11)
shrink as delta_c grows (i.e. as the implied H-compartment threshold moves
away from small integer counts)?

Isolates ONE variable: delta_c. Uses ONLY the deterministic direct-g variant
(no per-agent draws, no q, no cadence question) -- the cleanest signal,
per Decision_Register.md D11's speculation about a Jensen's-gap-style effect
at small H counts. Two-sided q and cadence are untouched this round.

Same scale as the full run (C11): N=100,000, 30 seeds, 900 days, 48
sub-steps/day. The ODE reference is recomputed separately for each delta_c
(it is NOT the same target as C11's 0.52502, which was for delta_c=0.5 only
-- correct, since delta_c=0.5 there matches this sweep's own baseline point).

delta_c values and their approximate implied H-count threshold
(H ~ delta_c * T_H, T_H=14): 0.5 (~7), 2.0 (~28), 3.5 (~49), 7.0 (~98).
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
from scipy.integrate import solve_ivp

S_, E_, I_, H_, R_, D_ = 0, 1, 2, 3, 4, 5

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N_SUBSTEPS = 48
K = 2
SEEDS_INFECTED = 10
DAYS = 900
N = 100_000
N_SEEDS = 30
DELTA_C_VALUES = [0.5, 2.0, 3.5, 7.0]


def _ode_final_S(N, delta_c, k=K, days=DAYS):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    def rhs(t, y):
        Sf, Ef, If, Hf, Rf, Df = y
        delta = death_delay_rate * Hf * N
        g = 1.0 / (1.0 + (delta / delta_c) ** k)
        foi = transmission_rate * g * Sf * If
        return [-foi, foi - latent_rate * Ef, latent_rate * Ef - infectious_rate * If,
                F_D * infectious_rate * If - death_delay_rate * Hf,
                (1 - F_D) * infectious_rate * If, death_delay_rate * Hf]

    I0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1 - I0, 0, I0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    y = sol.sol(days)
    return y[0], y[3] * N  # final S, final H (agent-count units)


def run_direct_g(N, seed, delta_c, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Deterministic direct-g: no per-agent draws, no q. Also tracks the
    peak H count reached (agent-count units) as a scaling sanity check --
    peak H, not a whole-run average, is the comparable figure against the
    D11 approximation H ~ delta_c*T_H (evaluated near the behavioural
    turning point where delta=delta_c, not diluted by the pre-epidemic
    ramp-up or post-fadeout zeros)."""
    dt = 1.0 / n_substeps
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate
    p_e_to_i = 1 - np.exp(-latent_rate * dt)
    p_i_to_leave = 1 - np.exp(-infectious_rate * dt)
    p_h_to_d = 1 - np.exp(-death_delay_rate * dt)

    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_

    peak_H = 0
    for t in range(days):
        for _ in range(n_substeps):
            n_H = np.count_nonzero(state == H_)
            if n_H > peak_H:
                peak_H = n_H
            delta_now = death_delay_rate * n_H
            g = 1.0 / (1.0 + (delta_now / delta_c) ** k)
            infectious_mask = (state == I_)
            n_infectious = np.count_nonzero(infectious_mask)
            foi = transmission_rate * g * n_infectious / N
            p_s_to_e = 1 - np.exp(-foi * dt)
            new_e = (state == S_) & (rng.random(N) < p_s_to_e)
            new_i = (state == E_) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < F_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H_) & (rng.random(N) < p_h_to_d)
            state[new_d] = D_; state[to_h] = H_; state[to_r] = R_; state[new_i] = I_; state[new_e] = E_
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            break
    s_final = np.count_nonzero(state == S_) / N
    return s_final, peak_H


def _worker(args):
    delta_c, seed = args
    t0 = time.time()
    s_final, peak_H = run_direct_g(N, seed, delta_c)
    return delta_c, seed, float(s_final), float(peak_H), time.time() - t0


def main(n_seeds=N_SEEDS, n_workers=None):
    ode_targets = {}
    print("ODE references (recomputed per delta_c):")
    for dc in DELTA_C_VALUES:
        ode_S, ode_H = _ode_final_S(N, dc)
        ode_targets[dc] = (ode_S, ode_H)
        print(f"  delta_c={dc}: ODE final S = {ode_S:.5f}, ODE final H (agents) = {ode_H:.2f}")
    print(flush=True)

    tasks = [(dc, seed) for dc in DELTA_C_VALUES for seed in range(n_seeds)]
    n_workers = n_workers or min(len(tasks), os.cpu_count() or 4)
    print(f"Running {len(tasks)} (delta_c, seed) tasks on {n_workers} workers...", flush=True)

    results = {dc: {"S": [None] * n_seeds, "peakH": [None] * n_seeds} for dc in DELTA_C_VALUES}
    t_start = time.time()
    done = 0
    with mp.Pool(n_workers) as pool:
        for dc, seed, s_final, peak_H, dt in pool.imap_unordered(_worker, tasks):
            results[dc]["S"][seed] = s_final
            results[dc]["peakH"][seed] = peak_H
            done += 1
            print(f"[{done}/{len(tasks)}] delta_c={dc} seed={seed} final_S={s_final:.5f} "
                  f"peak_H={peak_H:.0f} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)", flush=True)

    summary = {"N": N, "days": DAYS, "n_substeps": N_SUBSTEPS, "n_seeds": n_seeds,
               "delta_c_values": {}}
    print("\n=== SUMMARY (direct-g only) ===")
    for dc in DELTA_C_VALUES:
        ode_S, ode_H = ode_targets[dc]
        s_arr = np.array(results[dc]["S"])
        h_arr = np.array(results[dc]["peakH"])
        mean_S = float(s_arr.mean())
        std_S = float(s_arr.std(ddof=1))
        sem_S = std_S / np.sqrt(len(s_arr))
        rel_err = abs(mean_S - ode_S) / ode_S
        gap_sems = (mean_S - ode_S) / sem_S
        mean_peak_H = float(h_arr.mean())
        summary["delta_c_values"][str(dc)] = {
            "ode_final_S": ode_S, "ode_final_H": ode_H,
            "finals_S": results[dc]["S"], "finals_peakH": results[dc]["peakH"],
            "n_seeds_used": int(len(s_arr)),
            "mean_final_S": mean_S, "std_final_S": std_S, "sem_final_S": sem_S,
            "relative_error": rel_err, "gap_sems": gap_sems,
            "mean_peak_H": mean_peak_H,
        }
        print(f"delta_c={dc}: {len(s_arr)}/{n_seeds} seeds, "
              f"mean peak H = {mean_peak_H:.1f}, "
              f"mean final S = {mean_S:.5f} (ODE {ode_S:.5f}), "
              f"relative error = {rel_err*100:.2f}% ({gap_sems:.2f} SEMs)")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results",
                             "meanfield_deltac_sweep.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
