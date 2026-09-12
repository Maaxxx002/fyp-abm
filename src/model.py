"""
Stochastic SEIR+H epidemic simulator -- disease dynamics only.

No behaviour, no Perception, no arms, no observation model. This is the
plain no-intervention referent dynamics (CLAUDE.md hard constraints: those
layers are separate, later steps). Everyone mixes at the full well-mixed
contact rate; there is no stay-home mechanism here at all.

Compartments: S (susceptible), E (latent/exposed), I (infectious),
H (severe -- on the fatality pathway; models the infection-to-fatality
delay), R (recovered), D (dead). Weitz model B / Decision_Register.md A1.

Symbol-collision note (Decision_Register.md B4): Gozzi's `mu` = 1/infectious
period, `eps` = 1/latent period; Weitz's `mu` = 1/latent, `gamma` =
1/infectious -- same letters, opposite meanings, and the source of a past
bug (D1). This module never uses bare Greek-letter names; only explicit
`latent_period_days`, `infectious_period_days`, etc.

Settled parameters (Decision_Register.md A2, A20, A21, C9; CLAUDE.md Settled
numbers): R0=3.0, latent_period_days=2, infectious_period_days=6,
f_D=0.01 flat, T_H=14 d default, integration = 48 sub-steps/day with
transition probability 1-exp(-rate*dt) (register C9 -- Gozzi's own default
of 12 sub-steps carries a measurable residual bias for this model's extra
H-compartment chain; 48 was measured to bring it below Test 1's tolerance).
"""
import numpy as np

S, E, I, H, R, D = 0, 1, 2, 3, 4, 5


def run(N, seed, days=600, seeds_infected=10,
        R0=3.0, latent_period_days=2.0, infectious_period_days=6.0,
        f_D=0.01, T_H=14.0, n_substeps=48):
    """Well-mixed stochastic SEIR+H, behaviour OFF. Returns daily series.

    Each day is advanced over n_substeps sub-steps of dt=1/n_substeps; each
    transition (S->E force of infection, E->I, I->{H,R}, H->D) uses
    probability 1-exp(-rate*dt) (register A20/C9).
    """
    dt = 1.0 / n_substeps
    latent_rate = 1.0 / latent_period_days
    infectious_rate = 1.0 / infectious_period_days
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate  # well-mixed force-of-infection scale

    p_e_to_i = 1 - np.exp(-latent_rate * dt)
    p_i_to_leave = 1 - np.exp(-infectious_rate * dt)
    p_h_to_d = 1 - np.exp(-death_delay_rate * dt)

    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, seeds_infected, replace=False)] = I

    daily_deaths = np.zeros(days)
    daily_incidence = np.zeros(days)
    prevalence = np.zeros(days)
    S_frac = np.zeros(days)

    for t in range(days):
        day_new_e = 0
        day_new_d = 0
        for _ in range(n_substeps):
            infectious_mask = (state == I)
            n_infectious = np.count_nonzero(infectious_mask)
            force_of_infection = transmission_rate * n_infectious / N
            p_s_to_e = 1 - np.exp(-force_of_infection * dt)

            new_e = (state == S) & (rng.random(N) < p_s_to_e)
            new_i = (state == E) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < f_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H) & (rng.random(N) < p_h_to_d)

            state[new_d] = D
            state[to_h] = H
            state[to_r] = R
            state[new_i] = I
            state[new_e] = E

            day_new_e += np.count_nonzero(new_e)
            day_new_d += np.count_nonzero(new_d)

        daily_incidence[t] = day_new_e
        daily_deaths[t] = day_new_d
        prevalence[t] = np.count_nonzero(state == I)
        S_frac[t] = np.count_nonzero(state == S) / N

        if (prevalence[t] == 0 and np.count_nonzero(state == E) == 0
                and np.count_nonzero(state == H) == 0):
            daily_deaths[t + 1:] = 0
            daily_incidence[t + 1:] = 0
            prevalence[t + 1:] = 0
            S_frac[t + 1:] = S_frac[t]
            break

    return dict(
        S=S_frac, prevalence=prevalence, incidence=daily_incidence,
        deaths=daily_deaths, N=N,
        total_infected=N - np.count_nonzero(state == S),
    )


def run_weitz_behaviour(N, seed, days=600, seeds_infected=10,
                         R0=3.0, latent_period_days=2.0, infectious_period_days=6.0,
                         f_D=0.01, T_H=14.0, n_substeps=48,
                         delta_c=0.5, k=2):
    """Test 2 (mean-field recovery) only -- Weitz's OWN behaviour rule used for
    simulator validation (Decision_Register.md A4/A19), NOT arm 1's CBF or the
    project's Perception design, neither of which exist yet.

    Two-sided stay-home (Sourcing_Pack_v3.md's "Test 3" open point, resolved
    this session): every agent independently draws "out" for the day with
    probability (1-q); an S-I contact only happens if both are out, giving a
    population multiplier of (1-q)^2, which recovers Weitz's own
    g(delta) = 1/(1+(delta/delta_c)^k) when

        q(t) = 1 - (1 + (delta(t)/delta_c)^k)^(-1/2).

    delta(t) = gamma_H * H(t): Weitz's own definition (Decision_Register.md
    D10), a continuous instantaneous rate from the CURRENT H-compartment
    stock -- NOT a tally of realized D-transitions. Recomputed every
    sub-step from the running H count, zero lag, and q is redrawn every
    sub-step from it (register E16's "continuous-q" variant, the finest
    cadence measured). delta_c is a raw count (not per-capita), matching
    Weitz Table 1's N*delta_c units.
    """
    dt = 1.0 / n_substeps
    latent_rate = 1.0 / latent_period_days
    infectious_rate = 1.0 / infectious_period_days
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    p_e_to_i = 1 - np.exp(-latent_rate * dt)
    p_i_to_leave = 1 - np.exp(-infectious_rate * dt)
    p_h_to_d = 1 - np.exp(-death_delay_rate * dt)

    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, seeds_infected, replace=False)] = I

    daily_deaths = np.zeros(days)
    daily_incidence = np.zeros(days)
    prevalence = np.zeros(days)
    S_frac = np.zeros(days)

    for t in range(days):
        day_new_e = 0
        day_new_d = 0
        for _ in range(n_substeps):
            n_h = np.count_nonzero(state == H)
            delta_now = death_delay_rate * n_h
            q = 1.0 - (1.0 + (delta_now / delta_c) ** k) ** (-0.5)
            out = rng.random(N) > q

            infectious_mask = (state == I)
            n_infectious_out = np.count_nonzero(infectious_mask & out)
            force_of_infection = transmission_rate * n_infectious_out / N
            p_s_to_e = 1 - np.exp(-force_of_infection * dt)

            new_e = (state == S) & out & (rng.random(N) < p_s_to_e)
            new_i = (state == E) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < f_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H) & (rng.random(N) < p_h_to_d)

            state[new_d] = D
            state[to_h] = H
            state[to_r] = R
            state[new_i] = I
            state[new_e] = E

            day_new_e += np.count_nonzero(new_e)
            day_new_d += np.count_nonzero(new_d)

        daily_incidence[t] = day_new_e
        daily_deaths[t] = day_new_d
        prevalence[t] = np.count_nonzero(state == I)
        S_frac[t] = np.count_nonzero(state == S) / N

        if (prevalence[t] == 0 and np.count_nonzero(state == E) == 0
                and np.count_nonzero(state == H) == 0):
            daily_deaths[t + 1:] = 0
            daily_incidence[t + 1:] = 0
            prevalence[t + 1:] = 0
            S_frac[t + 1:] = S_frac[t]
            break

    return dict(
        S=S_frac, prevalence=prevalence, incidence=daily_incidence,
        deaths=daily_deaths, N=N,
        total_infected=N - np.count_nonzero(state == S),
    )
