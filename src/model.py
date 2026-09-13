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

S, E, I, H, R, D, SB = 0, 1, 2, 3, 4, 5, 6


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


def cbf_r_from_response_efficacy(response_efficacy):
    """CBF's per-agent protection factor `r_i`, from Perception's `response_efficacy`.

    r_i = 1 - response_efficacy_i: higher response_efficacy (an agent's belief that
    precautions work) gives a LOWER residual transmission rate while that agent is in
    S^B. This mapping is a stated MODELLING CHOICE, not a sourced formula -- no paper
    specifies how response_efficacy maps onto CBF's `r`, only that response_efficacy is
    the PMT construct that maps to it (Sourcing_Pack_v3.md Sec 3a: beta=+0.251;
    Design_Spec_Perception_and_Population.md Sec 2's field table). Same evidentiary
    status as occupation_flex's values (register A13, this entry): sourced construct,
    unsourced mapping. See Decision_Register.md for the entry recording this choice.
    """
    response_efficacy = np.asarray(response_efficacy, dtype=np.float64)
    return 1.0 - response_efficacy


def run_cbf_behaviour(N, seed, response_efficacy, days=600, seeds_infected=10,
                       R0=3.0, latent_period_days=2.0, infectious_period_days=6.0,
                       f_D=0.01, T_H=14.0, n_substeps=48,
                       beta_B=0.5, mu_B=0.01, gamma_beh=1.0, window=28):
    """Arm 1's REAL CBF mechanism (Decision_Register.md D12/E17) -- not the
    `direct-g` simplification, which D12 confirmed is NOT a valid stand-in
    for CBF (CBF has a genuine two-compartment, memory-laden structure that a
    memoryless multiplier cannot reproduce).

    S and S^B are separate tracked compartments. Each sub-step runs the same
    sub-step competing-hazards transitions Gozzi's own
    `compartment_model_age_deaths.py` implements (verified directly against
    source, lines ~114-126): from S, agents race between "-> E" (force of
    infection, full rate) and "-> S^B" (adoption); from S^B, agents race
    between "-> S" (relaxation) and "-> E" (force of infection at the
    PER-AGENT reduced rate `r_i * foi`, r_i = cbf_r_from_response_efficacy(...)).
    Gozzi draws one joint binomial for "did this age-group leave the
    compartment" and then splits it by relative hazard; here, with
    individual agents rather than age-group counts, the equivalent is two
    sequential per-agent Bernoulli draws (leave, then destination) --
    distributionally identical for i.i.d. agents (standard
    binomial/multinomial thinning), not an approximation of Gozzi's version:

        prob_S_to_SB(t)  = beta_B * (1 - exp(-gamma_beh * D(t)))   -- adoption RATE
        prob_SB_to_S(t)  = mu_B * (S(t) + R(t)) / N                -- relaxation RATE

    D(t) is NOT Gozzi's own literal single-day-lagged raw count -- it is the
    project's actual settled awareness signal (Decision_Register.md A8/C7,
    confirmed to resolve the small-flow-count bias for CBF's own mechanism in
    C17): a 28-day rolling mean of daily deaths, raw count units (not
    per-capita -- gamma_beh was sourced against raw counts, C13), using only
    days strictly before today (shrinking window for the first `window`
    days).

    `response_efficacy` is REQUIRED, length N, index-aligned with agents --
    normally `Population.response_efficacy` from src/population.py's
    quota-drawn population (Design_Spec Sec 6 Step 4). This replaces the
    earlier flat `r_factor=0.5` used for every agent (register C18/C19/C20's
    validation round): r is now per-agent, `1 - response_efficacy_i`, not a
    single population-wide constant.

    beta_B/mu_B/gamma_beh default to Gozzi's own sourced demo values
    (Sourcing_Pack_v3.md Sec 2b, Decision_Register.md C13).
    """
    if len(response_efficacy) != N:
        raise ValueError(
            f"response_efficacy has length {len(response_efficacy)}, expected N={N} "
            "(one value per agent, index-aligned with the population)."
        )
    r = cbf_r_from_response_efficacy(response_efficacy)

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
        window_start = max(0, t - window)
        D_mean = daily_deaths[window_start:t].mean() if t > 0 else 0.0
        adoption_rate = beta_B * (1.0 - np.exp(-gamma_beh * D_mean))

        day_new_e = 0
        day_new_d = 0
        for _ in range(n_substeps):
            n_infectious = np.count_nonzero(state == I)
            foi = transmission_rate * n_infectious / N
            foi_reduced = r * foi

            n_s = np.count_nonzero(state == S)
            n_r = np.count_nonzero(state == R)
            relax_rate = mu_B * (n_s + n_r) / N

            rate_total_s = adoption_rate + foi
            if rate_total_s > 0:
                p_leave_s = 1 - np.exp(-rate_total_s * dt)
                frac_e_from_s = foi / rate_total_s
            else:
                p_leave_s = 0.0
                frac_e_from_s = 0.0

            # foi_reduced (and hence rate_total_sb) is now per-agent (r_i varies), so this
            # is an elementwise version of the scalar r_factor branch used previously.
            rate_total_sb = relax_rate + foi_reduced
            p_leave_sb = 1 - np.exp(-rate_total_sb * dt)
            safe_rate_total_sb = np.where(rate_total_sb > 0, rate_total_sb, 1.0)
            frac_e_from_sb = np.where(rate_total_sb > 0, foi_reduced / safe_rate_total_sb, 0.0)

            s_mask = (state == S)
            sb_mask = (state == SB)

            leaving_s = s_mask & (rng.random(N) < p_leave_s)
            to_e_from_s = leaving_s & (rng.random(N) < frac_e_from_s)
            to_sb = leaving_s & ~to_e_from_s

            leaving_sb = sb_mask & (rng.random(N) < p_leave_sb)
            to_e_from_sb = leaving_sb & (rng.random(N) < frac_e_from_sb)
            to_s = leaving_sb & ~to_e_from_sb

            new_i = (state == E) & (rng.random(N) < p_e_to_i)
            leaving_i = (state == I) & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < f_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H) & (rng.random(N) < p_h_to_d)

            state[new_d] = D
            state[to_h] = H
            state[to_r] = R
            state[new_i] = I
            state[to_e_from_s] = E
            state[to_e_from_sb] = E
            state[to_sb] = SB
            state[to_s] = S

            day_new_e += np.count_nonzero(to_e_from_s) + np.count_nonzero(to_e_from_sb)
            day_new_d += np.count_nonzero(new_d)

        daily_incidence[t] = day_new_e
        daily_deaths[t] = day_new_d
        prevalence[t] = np.count_nonzero(state == I)
        S_frac[t] = (np.count_nonzero(state == S) + np.count_nonzero(state == SB)) / N

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
        total_infected=N - np.count_nonzero(state == S) - np.count_nonzero(state == SB),
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
