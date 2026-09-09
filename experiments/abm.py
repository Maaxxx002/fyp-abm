"""
Stochastic ABM pilot: does Weitz's awareness signature survive at small N?
Single well-mixed location. Binary act (home/out) -- the N question does not
depend on the number of action levels, so this is the cleanest test.

Weitz Eqs 9-14 (model B, with H compartment for the infection->fatality lag).
Per-agent rule:  P(stay home) = q(d) = (d/dc)^k / (1 + (d/dc)^k)
In the mean-field one-sided limit this reproduces beta*S*I / (1+(d/dc)^k).
"""
import numpy as np

BETA, MU, GAMMA, FD, K = 0.5, 0.5, 1/6, 0.01, 2
GAMMA_H = 1/14.0          # T_H = 14 d, Weitz Fig 6 default
R0 = BETA/GAMMA

S,E,I,H,R,D = 0,1,2,3,4,5

def run(N, dc, seed, days=600, seeds_infected=None, behaviour=True,
        signal="instant", window=7, sides=2, T_H=14.0, R0=3.0):
    """dc in per-capita deaths/day. Returns daily series."""
    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    n0 = seeds_infected if seeds_infected is not None else max(1, int(round(0.01*N)))
    state[rng.choice(N, n0, replace=False)] = I

    # Daily transition prob must be the RATE, not 1-exp(-rate). A geometric
    # dwell time with per-day prob p has mean 1/p; using 1-exp(-gamma) gives a
    # mean infectious period of 6.51 d instead of 6, inflating R0 to 3.26.
    p_ei, p_ir, p_hd = MU, GAMMA, 1.0/T_H
    beta_s = R0*GAMMA
    daily_deaths = np.zeros(days); prev = np.zeros(days); Sfrac = np.zeros(days); inc = np.zeros(days)
    out_frac = np.zeros(days)
    recent = []

    for t in range(days):
        # --- perceived death signal (per capita per day) ---
        if not behaviour:
            q = 0.0
        else:
            if signal == "instant":
                d = (daily_deaths[t-1]/N) if t > 0 else 0.0
            elif signal == "cum":                    # cumulative deaths per capita
                d = daily_deaths[:t].sum()/N
            elif signal == "both":                   # Weitz model C: short + long term
                d = None
                r_s = ((np.mean(recent[-window:])/N)/dc)**K if recent else 0.0
                r_l = ((daily_deaths[:t].sum()/N)/(dc*100.0))**K
            else:                                    # rolling mean
                d = (np.mean(recent[-window:])/N) if recent else 0.0
            r = (r_s + r_l) if d is None else (d/dc)**K
            # both parties must be out for a contact, so the population-level
            # multiplier is (1-q)^2. Invert to recover Weitz's 1/(1+r).
            q = 1.0 - (1.0+r)**(-1.0/sides)

        # --- action ---
        out = rng.random(N) > q                      # True = out today
        out_frac[t] = out.mean()

        inf_mask = (state == I)
        n_inf_out = np.count_nonzero(inf_mask & out)
        # force of infection on an agent who goes out
        lam = beta_s * n_inf_out / N                   # only out-out pairs mix

        new_e = (state == S) & out & (rng.random(N) < (1-np.exp(-lam)))
        new_i = (state == E) & (rng.random(N) < p_ei)
        leave_i = inf_mask & (rng.random(N) < p_ir)
        to_h = leave_i & (rng.random(N) < FD)
        to_r = leave_i & ~to_h
        new_d = (state == H) & (rng.random(N) < p_hd)

        state[new_d] = D; state[to_h] = H; state[to_r] = R
        state[new_i] = I; state[new_e] = E

        inc[t] = np.count_nonzero(new_e)
        nd = int(np.count_nonzero(new_d))
        daily_deaths[t] = nd; recent.append(nd)
        prev[t] = np.count_nonzero(state == I)
        Sfrac[t] = np.count_nonzero(state == S)/N
        if prev[t] == 0 and np.count_nonzero(state == E) == 0 and np.count_nonzero(state==H)==0:
            daily_deaths[t+1:] = 0; prev[t+1:] = 0; inc[t+1:] = 0; Sfrac[t+1:] = Sfrac[t]; break
    return dict(deaths=daily_deaths, prev=prev, inc=inc, S=Sfrac, out=out_frac,
                total_inf=N-np.count_nonzero(state==S), N=N)
