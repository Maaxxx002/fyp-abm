"""
CLAUDE.md Test 2 — mean-field recovery (Sourcing_Pack_v3.md's "Test 3").

Implements Weitz's OWN behaviour rule (Decision_Register.md A4/A19 — simulator
validation, NOT arm 1's CBF, which does not exist yet and is out of scope
here): g(delta) = 1/(1+(delta/delta_c)^k), Weitz Table 1.

Decision (supplied this session, resolving Sourcing_Pack_v3.md's explicit
"decide explicitly whether staying home removes contacts (two-sided) or
reduces per-contact risk (one-sided)" open point): two-sided. Every agent
independently draws "out" for the day with probability (1-q); a contact
between a susceptible and an infectious agent only happens if BOTH are out,
so the population-level multiplier is (1-q)^2, and

    q(t) = 1 - (1 + (delta(t)/delta_c)^k)^(-1/2)

recovers Weitz's own g(delta) at the mean-field level (CLAUDE.md Test 2).

delta(t) = gamma_H * H(t) — Weitz's OWN definition of the death-rate signal
(Decision_Register.md D10): a continuous instantaneous rate from the CURRENT
H-compartment stock, not a tally of realized D-transitions. Originally
mis-specified in this project as "raw death count from the running
simulation" (a discrete tally, tried both lagged and same-day), which failed
Test 2 by ~26-48% against the ODE (D10). Recomputing delta from the running
H count fixes the diagnosis (D10; deterministic direct-g variant drops to
~1.6%). This is Weitz's own validation rule, distinct from the project's
actual future Perception design (register A8: 28-day rolling mean of
per-capita deaths).

Cadence: q(t) is redrawn every sub-step from the current H-based delta, zero
lag (register E16's "continuous-q" variant — the finest cadence measured,
and the one `run_weitz_behaviour` implements). An alternative once-per-day
cadence ("daily-q") was also measured and is closer to the register's
original once-per-day framing, but showed a larger residual gap against the
ODE (E16); see `experiments/verify_meanfield_delta_bug.py` for both variants
compared side by side. Which cadence to adopt as final is not yet decided —
see the register for the outstanding comparison.

delta_c: Weitz Table 1 states N*delta_c = 50 deaths/day (Figs 3, 6, 7) at
N=10,000,000 (Sourcing_Pack_v3.md); deaths/day is a raw count, not
per-capita, and does not transfer across population sizes without rescaling
(Sourcing_Pack_v3.md, mean-field-recovery section) — so at N=100,000,
delta_c = 50 * (100,000 / 10,000,000) = 0.5 deaths/day. k=2, Weitz's stated
"typical" value (Sourcing_Pack_v3.md: k in 1-4, 2 typical).
"""
import numpy as np
from scipy.integrate import solve_ivp

from model import run_weitz_behaviour

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N = 100_000
N_SEEDS = 30
DAYS = 900
DELTA_C = 0.5     # deaths/day, raw count; rescaled from Weitz's N*delta_c=50 at N=1e7
K = 2             # Weitz's stated "typical" value (Sourcing_Pack_v3.md)
TOLERANCE = 0.02  # relative; looser than Test 1's 1% -- extra layer of mean-field approximation


def _ode_final_S(days=DAYS):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    def rhs(t, y):
        Sf, Ef, If, Hf, Rf, Df = y
        delta = death_delay_rate * Hf * N           # raw expected deaths/day at this instant
        g = 1.0 / (1.0 + (delta / DELTA_C) ** K)     # Weitz's own behaviour multiplier
        foi = transmission_rate * g * Sf * If
        return [-foi, foi - latent_rate * Ef, latent_rate * Ef - infectious_rate * If,
                F_D * infectious_rate * If - death_delay_rate * Hf,
                (1 - F_D) * infectious_rate * If, death_delay_rate * Hf]

    I0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1 - I0, 0, I0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    return sol.sol(days)[0]


def test_meanfield_recovers_weitz_ode():
    ode_S = _ode_final_S()
    finals = np.array([
        run_weitz_behaviour(N=N, seed=s, days=DAYS,
                             R0=R0, latent_period_days=LATENT_PERIOD_DAYS,
                             infectious_period_days=INFECTIOUS_PERIOD_DAYS,
                             f_D=F_D, T_H=T_H, delta_c=DELTA_C, k=K)["S"][-1]
        for s in range(N_SEEDS)
    ])
    mean_S = finals.mean()
    rel_err = abs(mean_S - ode_S) / ode_S
    # Denominator (CLAUDE.md convention): all N_SEEDS runs used, none excluded.
    assert rel_err < TOLERANCE, (
        f"mean final S over {N_SEEDS} seeds = {mean_S:.5f} vs ODE {ode_S:.5f} "
        f"({rel_err*100:.2f}% relative error, tolerance {TOLERANCE*100:.0f}%)"
    )
