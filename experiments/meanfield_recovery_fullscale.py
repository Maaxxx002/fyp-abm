"""
Full-scale re-run of the mean-field recovery comparison (Decision_Register.md
D10/E16), at actual Test 2 conditions: N=100,000, 30 seeds, 900 days, 48
sub-steps/day -- same scale as Test 1 (C9/C10). The earlier ~1.6%/4.4%/7.1%
numbers (D10/E16) came from a 5-seed diagnostic, not this scale.

Three variants, all using the CORRECTED delta(t) = gamma_H * H(t) (continuous,
recomputed from the current H stock, zero lag -- D10's fix; the previous
death-tally definition is not run here, it is already disconfirmed):

  a. direct-g   -- deterministic, no per-agent draws at all (transmission
                   multiplied by g(delta) directly). Sanity check.
  b. continuous-q -- the actual two-sided q mechanism, delta/q recomputed
                   and redrawn every sub-step (finest cadence; this is what
                   src/model.py's run_weitz_behaviour now implements).
  c. daily-q    -- two-sided q mechanism, decided once per day from the
                   day's starting H count (the cadence in the original spec).

Runs variant x seed combinations in parallel via multiprocessing (this
machine has multiple cores; each run is single-threaded numpy). Writes a
JSON summary to results/.
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from model import run_weitz_behaviour  # noqa: E402

S_, E_, I_, H_, R_, D_ = 0, 1, 2, 3, 4, 5

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N_SUBSTEPS = 48
DELTA_C = 0.5
K = 2
SEEDS_INFECTED = 10
DAYS = 900
N = 100_000
N_SEEDS = 30


def _ode_final_S(N=N, delta_c=DELTA_C, k=K, days=DAYS):
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
    return sol.sol(days)[0]


def _rates(dt):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate
    return (transmission_rate,
            1 - np.exp(-latent_rate * dt),
            1 - np.exp(-infectious_rate * dt),
            1 - np.exp(-death_delay_rate * dt),
            death_delay_rate)


def run_direct_g(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (a): deterministic, no per-agent draws, continuous H-based delta."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    S_frac = np.zeros(days)
    for t in range(days):
        for _ in range(n_substeps):
            n_H = np.count_nonzero(state == H_)
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
        S_frac[t] = np.count_nonzero(state == S_) / N
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            S_frac[t + 1:] = S_frac[t]
            break
    return S_frac[-1]


def run_daily_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (c): two-sided q, continuous H-based delta, decided once per day."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    S_frac = np.zeros(days)
    for t in range(days):
        n_H = np.count_nonzero(state == H_)
        delta_t = death_delay_rate * n_H
        q = 1.0 - (1.0 + (delta_t / delta_c) ** k) ** (-0.5)
        out = rng.random(N) > q
        for _ in range(n_substeps):
            infectious_mask = (state == I_)
            n_infectious_out = np.count_nonzero(infectious_mask & out)
            foi = transmission_rate * n_infectious_out / N
            p_s_to_e = 1 - np.exp(-foi * dt)
            new_e = (state == S_) & out & (rng.random(N) < p_s_to_e)
            new_i = (state == E_) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < F_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H_) & (rng.random(N) < p_h_to_d)
            state[new_d] = D_; state[to_h] = H_; state[to_r] = R_; state[new_i] = I_; state[new_e] = E_
        S_frac[t] = np.count_nonzero(state == S_) / N
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            S_frac[t + 1:] = S_frac[t]
            break
    return S_frac[-1]


def run_continuous_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (b): src/model.py's actual run_weitz_behaviour (continuous-q)."""
    return run_weitz_behaviour(
        N=N, seed=seed, days=days, seeds_infected=SEEDS_INFECTED,
        R0=R0, latent_period_days=LATENT_PERIOD_DAYS,
        infectious_period_days=INFECTIOUS_PERIOD_DAYS,
        f_D=F_D, T_H=T_H, n_substeps=n_substeps,
        delta_c=delta_c, k=k,
    )["S"][-1]


VARIANTS = {
    "a_direct_g": run_direct_g,
    "b_continuous_q": run_continuous_q,
    "c_daily_q": run_daily_q,
}


def _worker(args):
    name, seed = args
    fn = VARIANTS[name]
    t0 = time.time()
    s = fn(N, seed)
    return name, seed, float(s), time.time() - t0


def main(n_seeds=N_SEEDS, n_workers=None):
    ode_S = _ode_final_S()
    print(f"ODE final S (with Weitz behaviour, N={N}, days={DAYS}) = {ode_S:.5f}", flush=True)

    tasks = [(name, seed) for name in VARIANTS for seed in range(n_seeds)]
    n_workers = n_workers or min(len(tasks), os.cpu_count() or 4)
    print(f"Running {len(tasks)} (variant, seed) tasks on {n_workers} workers...", flush=True)

    results = {name: [None] * n_seeds for name in VARIANTS}
    t_start = time.time()
    done = 0
    with mp.Pool(n_workers) as pool:
        for name, seed, s_final, dt in pool.imap_unordered(_worker, tasks):
            results[name][seed] = s_final
            done += 1
            print(f"[{done}/{len(tasks)}] {name} seed={seed} final_S={s_final:.5f} "
                  f"({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)", flush=True)

    summary = {"ode_final_S": ode_S, "N": N, "days": DAYS, "n_substeps": N_SUBSTEPS,
               "n_seeds": n_seeds, "variants": {}}
    print("\n=== SUMMARY ===")
    print(f"ODE final S = {ode_S:.5f}  (N={N}, days={DAYS}, 48 substeps/day)")
    for name, finals in results.items():
        arr = np.array(finals, dtype=float)
        n_defined = np.count_nonzero(~np.isnan(arr))
        mean_S = float(np.nanmean(arr))
        rel_err = abs(mean_S - ode_S) / ode_S
        summary["variants"][name] = {
            "finals": finals, "n_seeds_used": int(n_defined),
            "mean_final_S": mean_S, "relative_error": rel_err,
        }
        print(f"{name}: {n_defined}/{n_seeds} seeds, mean final S = {mean_S:.5f}, "
              f"relative error = {rel_err*100:.2f}%")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results",
                             "meanfield_recovery_fullscale.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
