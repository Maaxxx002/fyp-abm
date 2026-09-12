"""
Repeats C12's delta_c sweep methodology, but with CBF's OWN mechanism
(Decision_Register.md C13) instead of Weitz's: a raw, one-day-LAGGED daily
death COUNT (a flow), not a continuous H-compartment stock recomputed with
zero lag. Deterministic direct-g variant only (no per-agent draws, no S/S^B
compartment split -- isolates the count-discreteness question the same way
C12 isolated it for Weitz's mechanism).

CBF's global mechanism, sourced directly from Gozzi's code (C13):

    prob_S_to_SB = beta_B * (1 - exp(-gamma_beh * deaths_yesterday))

`deaths_yesterday` is a raw count, fixed for the whole day (recomputed once
per day, not every sub-step -- there is no "yesterday" to update mid-day).
The direct-g analogue used here multiplies transmission by

    g_CBF(D) = 1 - beta_B * (1 - exp(-gamma_beh * D))

with D = deaths[t-1] (that day's dampener uses YESTERDAY's realized death
count, exactly as CBF's own formula specifies -- unlike the corrected
Weitz mechanism, this lag is not a bug being fixed, it's CBF's actual
published design). The ODE reference has no "yesterday" (continuous time),
so it uses the same instantaneous rate D_now = gamma_H*H(t)*N Weitz's own
ODE reference uses -- the continuous limit of "today's death rate" is the
same quantity regardless of which paper's formula reads it discretely.

beta_B is held at Gozzi's own sourced demo value (0.5, C13) throughout;
only gamma_beh is swept. gamma_beh is parameterised via its "characteristic
count" T = 1/gamma_beh (the e-folding count, C13's second convention) at
the SAME target values as C12's delta_c sweep (0.5, 2.0, 3.5, 7.0), purely
so the two tables sit side by side -- these T values are not independently
sourced, they are chosen to match C12's progression for comparability.

Same scale as C12: N=30,000 (this session's candidate operating N, not
Test 2's N=100,000) and, optionally, N=10,000. 30 seeds, days=900,
48 sub-steps/day.
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
SEEDS_INFECTED = 10
DAYS = 900
N_SEEDS = 30
BETA_B = 0.5   # Gozzi's own sourced demo default (C13), held fixed
T_VALUES = [0.5, 2.0, 3.5, 7.0]   # characteristic count targets, matching C12's delta_c progression
N_VALUES = [30_000, 10_000]


def _ode_final_S(N, gamma_beh, beta_B=BETA_B, days=DAYS):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    def rhs(t, y):
        Sf, Ef, If, Hf, Rf, Df = y
        D_now = death_delay_rate * Hf * N
        g = 1.0 - beta_B * (1.0 - np.exp(-gamma_beh * D_now))
        foi = transmission_rate * g * Sf * If
        return [-foi, foi - latent_rate * Ef, latent_rate * Ef - infectious_rate * If,
                F_D * infectious_rate * If - death_delay_rate * Hf,
                (1 - F_D) * infectious_rate * If, death_delay_rate * Hf]

    I0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1 - I0, 0, I0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    y = sol.sol(days)
    return y[0], y[3] * N  # final S, final H (agent-count units)


def run_direct_g_cbf(N, seed, gamma_beh, beta_B=BETA_B, days=DAYS, n_substeps=N_SUBSTEPS):
    """Deterministic direct-g, CBF's own lagged-raw-death-count trigger."""
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

    peak_daily_deaths = 0
    prev_day_deaths = 0.0
    for t in range(days):
        g = 1.0 - beta_B * (1.0 - np.exp(-gamma_beh * prev_day_deaths))
        day_new_d = 0
        for _ in range(n_substeps):
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
            day_new_d += np.count_nonzero(new_d)
        prev_day_deaths = day_new_d
        if day_new_d > peak_daily_deaths:
            peak_daily_deaths = day_new_d
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            break
    s_final = np.count_nonzero(state == S_) / N
    return s_final, peak_daily_deaths


def _worker(args):
    N, T, seed = args
    gamma_beh = 1.0 / T
    t0 = time.time()
    s_final, peak_d = run_direct_g_cbf(N, seed, gamma_beh)
    return N, T, seed, float(s_final), int(peak_d), time.time() - t0


def main(n_seeds=N_SEEDS, n_workers=None):
    ode_targets = {}
    print("ODE references (recomputed per N, per T):")
    for N in N_VALUES:
        for T in T_VALUES:
            gamma_beh = 1.0 / T
            ode_S, ode_H = _ode_final_S(N, gamma_beh)
            ode_targets[(N, T)] = ode_S
            print(f"  N={N:,} T={T} (gamma_beh={gamma_beh:.3f}): ODE final S = {ode_S:.5f}, "
                  f"ODE final H = {ode_H:.2f}")
    print(flush=True)

    tasks = [(N, T, seed) for N in N_VALUES for T in T_VALUES for seed in range(n_seeds)]
    n_workers = n_workers or min(len(tasks), os.cpu_count() or 4)
    print(f"Running {len(tasks)} (N, T, seed) tasks on {n_workers} workers...", flush=True)

    results = {(N, T): {"S": [None] * n_seeds, "peakD": [None] * n_seeds}
               for N in N_VALUES for T in T_VALUES}
    t_start = time.time()
    done = 0
    with mp.Pool(n_workers) as pool:
        for N, T, seed, s_final, peak_d, dt in pool.imap_unordered(_worker, tasks):
            results[(N, T)]["S"][seed] = s_final
            results[(N, T)]["peakD"][seed] = peak_d
            done += 1
            print(f"[{done}/{len(tasks)}] N={N} T={T} seed={seed} final_S={s_final:.5f} "
                  f"peak_daily_deaths={peak_d} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)",
                  flush=True)

    summary = {"days": DAYS, "n_substeps": N_SUBSTEPS, "n_seeds": n_seeds, "beta_B": BETA_B,
               "results": {}}
    print("\n=== SUMMARY (direct-g, CBF mechanism) ===")
    for N in N_VALUES:
        for T in T_VALUES:
            ode_S = ode_targets[(N, T)]
            s_arr = np.array(results[(N, T)]["S"])
            d_arr = np.array(results[(N, T)]["peakD"])
            mean_S = float(s_arr.mean())
            std_S = float(s_arr.std(ddof=1))
            sem_S = std_S / np.sqrt(len(s_arr))
            rel_err = abs(mean_S - ode_S) / ode_S
            gap_sems = (mean_S - ode_S) / sem_S
            mean_peak_d = float(d_arr.mean())
            key = f"N={N}_T={T}"
            summary["results"][key] = {
                "N": N, "T": T, "gamma_beh": 1.0 / T, "ode_final_S": ode_S,
                "finals_S": results[(N, T)]["S"], "finals_peakD": results[(N, T)]["peakD"],
                "n_seeds_used": int(len(s_arr)), "mean_final_S": mean_S,
                "std_final_S": std_S, "sem_final_S": sem_S,
                "relative_error": rel_err, "gap_sems": gap_sems,
                "mean_peak_daily_deaths": mean_peak_d,
            }
            print(f"N={N:>6,} T={T:>4} (gamma_beh={1/T:.3f}): {len(s_arr)}/{n_seeds} seeds, "
                  f"mean peak daily deaths = {mean_peak_d:.1f}, "
                  f"mean final S = {mean_S:.5f} (ODE {ode_S:.5f}), "
                  f"relative error = {rel_err*100:.2f}% ({gap_sems:.2f} SEMs)")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "cbf_deltac_sweep.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
