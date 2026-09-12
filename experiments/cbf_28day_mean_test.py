"""
Single test (not a sweep): CBF exactly as arm 1 will actually run it --
Gozzi's own sourced parameters AS-IS (no substituting a friendlier T this
time), but with the project's ACTUAL settled signal (Decision_Register.md
A8/C7, Design_Spec_Perception_and_Population.md Sec 2/3: a 28-day rolling
mean of daily deaths), not Gozzi's own literal "yesterday's raw count".

    g_CBF(D) = 1 - beta_B * (1 - exp(-gamma_beh * D))
    beta_B = 0.5, gamma_beh = 1        (Gozzi's sourced demo default, C13, as-is)
    D = mean of daily deaths over the trailing 28 days (raw count units, NOT
        per-capita -- gamma_beh's sourced value was calibrated against raw
        counts, C13), using a SHRINKING window for the first 28 days (divide
        by however many days are actually available, matching this
        session's state_count_check.py convention), and using only days
        STRICTLY BEFORE today (i.e. the mean ending yesterday) -- the same
        causal convention as CBF's own single-day lag, just widened to a
        28-day window instead of a single day.

Deterministic direct-g only (no per-agent draws, no S/S^B split) -- same
isolation principle as C12/C16.

ODE reference: the 28-day mean is a genuine DELAY (a trailing integral of
the death rate), which solve_ivp cannot express directly (it is a delay
differential equation, not a plain ODE). Implemented here as a fixed-step
(dt=0.25 day) RK4 integrator carrying a stored history of cumulative deaths,
so D_ode(t) = N*(Dcum(t) - Dcum(t-28))/28 for t>=28, or N*Dcum(t)/t for
0<t<28 (shrinking window, matching the ABM's own convention), 0 at t=0.
Within one 0.25-day RK4 step the delay value is held fixed across the 4
stages -- dt=0.25 is negligible next to a 28-day delay, so this introduces
no meaningful error.
"""
import json
import multiprocessing as mp
import os
import time

import numpy as np

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
BETA_B = 0.5     # Gozzi's own sourced demo default (C13), as-is
GAMMA_BEH = 1.0  # Gozzi's own sourced demo default (C13), as-is -- NOT swept this time
WINDOW = 28      # A8/C7's settled awareness window
N_VALUES = [10_000, 30_000]

_LATENT_RATE = 1.0 / LATENT_PERIOD_DAYS
_INFECTIOUS_RATE = 1.0 / INFECTIOUS_PERIOD_DAYS
_DEATH_DELAY_RATE = 1.0 / T_H
_TRANSMISSION_RATE = R0 * _INFECTIOUS_RATE


def _rhs(y, g):
    Sf, Ef, If, Hf, Rf, Df = y
    foi = _TRANSMISSION_RATE * g * Sf * If
    return np.array([
        -foi,
        foi - _LATENT_RATE * Ef,
        _LATENT_RATE * Ef - _INFECTIOUS_RATE * If,
        F_D * _INFECTIOUS_RATE * If - _DEATH_DELAY_RATE * Hf,
        (1 - F_D) * _INFECTIOUS_RATE * If,
        _DEATH_DELAY_RATE * Hf,
    ])


def ode_final_S(N, beta_B=BETA_B, gamma_beh=GAMMA_BEH, window=WINDOW,
                 days=DAYS, dt=0.25):
    n_steps = int(round(days / dt))
    steps_per_window = int(round(window / dt))
    assert abs(steps_per_window * dt - window) < 1e-9, "dt must evenly divide the window"

    I0 = 1e-6
    y = np.array([1 - I0, 0.0, I0, 0.0, 0.0, 0.0])
    dcum_history = np.zeros(n_steps + 1)
    dcum_history[0] = y[5]

    for i in range(n_steps):
        t_days = i * dt
        if i == 0:
            D_delay = 0.0
        elif i < steps_per_window:
            D_delay = N * dcum_history[i] / t_days
        else:
            D_delay = N * (dcum_history[i] - dcum_history[i - steps_per_window]) / window
        g = 1.0 - beta_B * (1.0 - np.exp(-gamma_beh * D_delay))

        k1 = _rhs(y, g)
        k2 = _rhs(y + 0.5 * dt * k1, g)
        k3 = _rhs(y + 0.5 * dt * k2, g)
        k4 = _rhs(y + dt * k3, g)
        y = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        dcum_history[i + 1] = y[5]

    return y[0], y[3] * N  # final S, final H (agent-count units)


def run_direct_g_28day(N, seed, beta_B=BETA_B, gamma_beh=GAMMA_BEH, window=WINDOW,
                        days=DAYS, n_substeps=N_SUBSTEPS):
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

    daily_deaths = np.zeros(days)
    peak_daily_deaths = 0
    for t in range(days):
        window_start = max(0, t - window)
        D_mean = daily_deaths[window_start:t].mean() if t > 0 else 0.0
        g = 1.0 - beta_B * (1.0 - np.exp(-gamma_beh * D_mean))

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
        daily_deaths[t] = day_new_d
        if day_new_d > peak_daily_deaths:
            peak_daily_deaths = day_new_d
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            break
    s_final = np.count_nonzero(state == S_) / N
    return s_final, peak_daily_deaths


def _worker(args):
    N, seed = args
    t0 = time.time()
    s_final, peak_d = run_direct_g_28day(N, seed)
    return N, seed, float(s_final), int(peak_d), time.time() - t0


def main(n_seeds=N_SEEDS):
    ode_targets = {}
    for N in N_VALUES:
        ode_S, ode_H = ode_final_S(N)
        ode_targets[N] = ode_S
        print(f"N={N:,}: ODE final S = {ode_S:.5f}, ODE final H = {ode_H:.2f}")
    print(flush=True)

    tasks = [(N, seed) for N in N_VALUES for seed in range(n_seeds)]
    results = {N: {"S": [None] * n_seeds, "peakD": [None] * n_seeds} for N in N_VALUES}
    t_start = time.time()
    done = 0
    with mp.Pool(min(len(tasks), 16)) as pool:
        for N, seed, s_final, peak_d, dt in pool.imap_unordered(_worker, tasks):
            results[N]["S"][seed] = s_final
            results[N]["peakD"][seed] = peak_d
            done += 1
            print(f"[{done}/{len(tasks)}] N={N} seed={seed} final_S={s_final:.5f} "
                  f"peak_daily_deaths={peak_d} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)",
                  flush=True)

    print("\n=== SUMMARY (direct-g, CBF mechanism, 28-day mean signal, "
          "beta_B=0.5, gamma_beh=1 as sourced) ===")
    summary = {"beta_B": BETA_B, "gamma_beh": GAMMA_BEH, "window": WINDOW,
               "days": DAYS, "n_substeps": N_SUBSTEPS, "n_seeds": n_seeds, "results": {}}
    for N in N_VALUES:
        ode_S = ode_targets[N]
        s_arr = np.array(results[N]["S"])
        d_arr = np.array(results[N]["peakD"])
        mean_S = float(s_arr.mean())
        sem_S = float(s_arr.std(ddof=1) / np.sqrt(len(s_arr)))
        rel_err = abs(mean_S - ode_S) / ode_S
        gap_sems = (mean_S - ode_S) / sem_S
        summary["results"][str(N)] = {
            "ode_final_S": ode_S, "finals_S": results[N]["S"], "finals_peakD": results[N]["peakD"],
            "n_seeds_used": int(len(s_arr)), "mean_final_S": mean_S, "sem_final_S": sem_S,
            "relative_error": rel_err, "gap_sems": gap_sems,
            "mean_peak_daily_deaths": float(d_arr.mean()),
        }
        print(f"N={N:>7,}: {len(s_arr)}/{n_seeds} seeds, "
              f"mean peak daily deaths = {d_arr.mean():.1f}, "
              f"mean final S = {mean_S:.5f} (ODE {ode_S:.5f}), "
              f"relative error = {rel_err*100:.2f}% ({gap_sems:.2f} SEMs)")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "cbf_28day_mean_test.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
