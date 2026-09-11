"""
Diagnosis of tests/test_meanfield_recovery.py's ~26% failure (Decision_Register.md D10).

Test 2 was originally specified with delta(t) = "raw death count from the running
simulation" (a tally of realized D-transitions, previous-day-lagged in
src/model.py's run_weitz_behaviour). That fails hard against the ODE. This script
isolates why, by testing four variants against the same ODE target, smallest seed
counts that show the effect clearly -- NOT a full-scale (N=100,000/30-seed)
re-validation, which is deliberately deferred (see E16).

Variants, in the order they were tried:

1. lagged-q       -- src/model.py's actual run_weitz_behaviour: two-sided q,
                     delta(t) = deaths(t-1) (a realized count, previous day).
2. sameday-q       -- delta(t) = that day's OWN realized death count, via a
                     two-pass split (progression-only, then contact-only) so the
                     day's death count is known before that day's behaviour is
                     decided. Tests whether the lag itself was the problem.
3. direct-g-lagged -- deterministic: no q, no per-agent draws at all, just
                     multiply transmission by g(delta) directly, same lagged
                     delta as (1). Isolates whether the q/Bernoulli mechanism
                     itself is the bug, independent of delta's definition.
4. continuous-g    -- deterministic direct-g, but delta recomputed every
                     sub-step from the CURRENT H stock (delta = death_delay_rate
                     * n_H), exactly mirroring the ODE's continuous gH*H(t) --
                     no lag, not a realized count at all.
5. continuous-q    -- the actual two-sided q mechanism with continuous-g's delta,
                     redrawn every sub-step.
6. daily-q         -- continuous-g's delta, but q decided ONCE per day (the
                     cadence actually specified), using H at the start of the day.

Result (Decision_Register.md D10/E16): (1) and (2) fail by ~26-48%. (3) fails
almost identically to (1) (~26%), ruling out the q-mechanism as the cause. (4)
gets to ~1.6% -- confirms delta must be the continuous H-based rate, not a
realized death count. (5) and (6) are much closer (~4.4% and ~7.1%) but still
outside Test 2's 2% tolerance -- an open residual, see E16 (decision cadence).
"""
import numpy as np
from scipy.integrate import solve_ivp

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


def _ode_final_S(N, delta_c=DELTA_C, k=K, days=DAYS):
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


def _rates_and_probs(dt):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate
    return (transmission_rate,
            1 - np.exp(-latent_rate * dt),
            1 - np.exp(-infectious_rate * dt),
            1 - np.exp(-death_delay_rate * dt),
            death_delay_rate)


def run_lagged_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (1): src/model.py's run_weitz_behaviour, reproduced standalone."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    daily_deaths = np.zeros(days)
    S_frac = np.zeros(days)
    for t in range(days):
        delta_t = daily_deaths[t - 1] if t > 0 else 0.0
        q = 1.0 - (1.0 + (delta_t / delta_c) ** k) ** (-0.5)
        out = rng.random(N) > q
        day_new_d = 0
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
            day_new_d += np.count_nonzero(new_d)
        daily_deaths[t] = day_new_d
        S_frac[t] = np.count_nonzero(state == S_) / N
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            S_frac[t + 1:] = S_frac[t]
            break
    return S_frac[-1]


def run_sameday_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (2): delta(t) = that day's own realized death count (two-pass)."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    S_frac = np.zeros(days)
    for t in range(days):
        day_new_d = 0
        for _ in range(n_substeps):
            infectious_mask = (state == I_)
            new_i = (state == E_) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < F_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H_) & (rng.random(N) < p_h_to_d)
            state[new_d] = D_; state[to_h] = H_; state[to_r] = R_; state[new_i] = I_
            day_new_d += np.count_nonzero(new_d)
        q = 1.0 - (1.0 + (day_new_d / delta_c) ** k) ** (-0.5)
        out = rng.random(N) > q
        for _ in range(n_substeps):
            infectious_mask = (state == I_)
            n_infectious_out = np.count_nonzero(infectious_mask & out)
            foi = transmission_rate * n_infectious_out / N
            p_s_to_e = 1 - np.exp(-foi * dt)
            new_e = (state == S_) & out & (rng.random(N) < p_s_to_e)
            state[new_e] = E_
        S_frac[t] = np.count_nonzero(state == S_) / N
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            S_frac[t + 1:] = S_frac[t]
            break
    return S_frac[-1]


def run_direct_g_lagged(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (3): no q at all -- multiply transmission by g(delta) directly, same lagged delta as (1)."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    daily_deaths = np.zeros(days)
    S_frac = np.zeros(days)
    for t in range(days):
        delta_t = daily_deaths[t - 1] if t > 0 else 0.0
        g = 1.0 / (1.0 + (delta_t / delta_c) ** k)
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
        S_frac[t] = np.count_nonzero(state == S_) / N
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            S_frac[t + 1:] = S_frac[t]
            break
    return S_frac[-1]


def run_continuous_g(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (4): delta recomputed every sub-step from the CURRENT H stock -- no lag, no q."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
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


def run_continuous_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (5): two-sided q, continuous H-based delta, redrawn every sub-step."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    S_frac = np.zeros(days)
    for t in range(days):
        for _ in range(n_substeps):
            n_H = np.count_nonzero(state == H_)
            delta_now = death_delay_rate * n_H
            q = 1.0 - (1.0 + (delta_now / delta_c) ** k) ** (-0.5)
            out = rng.random(N) > q
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


def run_daily_q(N, seed, delta_c=DELTA_C, k=K, days=DAYS, n_substeps=N_SUBSTEPS):
    """Variant (6): two-sided q, continuous H-based delta, decided ONCE per day (the
    cadence actually specified) using H at the start of the day."""
    dt = 1.0 / n_substeps
    transmission_rate, p_e_to_i, p_i_to_leave, p_h_to_d, death_delay_rate = _rates_and_probs(dt)
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


def main(N=100_000, n_seeds=5):
    """Small-scale diagnostic only -- NOT the full N=100,000/30-seed validation
    (Decision_Register.md E16 defers that). Enough seeds to see which variants
    are close and which are not."""
    ode_S = _ode_final_S(N)
    print(f"ODE final S (with Weitz behaviour, N={N}) = {ode_S:.5f}\n")

    variants = {
        "1. lagged-q (original spec, src/model.py)": run_lagged_q,
        "2. sameday-q (two-pass, same-day count)": run_sameday_q,
        "3. direct-g-lagged (no q, isolates q-mechanism)": run_direct_g_lagged,
        "4. continuous-g (no lag, H-based, no q)": run_continuous_g,
        "5. continuous-q (two-sided, substep-redrawn)": run_continuous_q,
        "6. daily-q (two-sided, once/day, H-based)": run_daily_q,
    }
    for name, fn in variants.items():
        finals = np.array([fn(N, s) for s in range(n_seeds)])
        mean_S = finals.mean()
        rel_err = abs(mean_S - ode_S) / ode_S
        print(f"{name}")
        print(f"  {n_seeds}/{n_seeds} seeds, mean final S = {mean_S:.5f}, "
              f"relative error = {rel_err*100:.2f}%")


if __name__ == "__main__":
    main()
