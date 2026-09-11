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

delta(t): that day's raw (unsmoothed) death COUNT — not per-capita, not
rolling-averaged. This is Weitz's own validation rule, distinct from the
project's actual future Perception design (register A8: 28-day rolling mean
of per-capita deaths).

Implementation note, flagged rather than silently settled: q(t) is decided
once per day, before that day's 48 sub-steps of disease dynamics run, using
the PREVIOUS day's realized death count (delta(t) = deaths(t-1)). This
mirrors the single-pass causal structure already validated for Test 1 and
the pilot's own "instant" signal convention (experiments/abm.py). A same-day
(zero-lag) version would need the day's disease-progression transitions
(E->I, I->H/R, H->D — all independent of "out" status) resolved in a
separate pass BEFORE the day's contact-driven S->E transitions, so that the
day's own realized death count is known before that day's behaviour is
decided. That two-pass split forces I's within-day trajectory used by S->E
to come from a different point (effectively next-day's I) than the
synchronous per-substep I used by Test 1's single-pass model, introducing an
unvalidated splitting-order artifact of its own. A 1-day lag on an aggregate
outcome (final S — not a fine-grained shape metric) is expected to matter far
less than that. The ODE reference below has no such lag (a continuous system
has no "yesterday"); this asymmetry is part of the "extra layer of
approximation" the 2% tolerance (vs Test 1's 1%) is meant to absorb. If the
zero-lag version is wanted instead, say so and it can be built as a second
variant.

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
