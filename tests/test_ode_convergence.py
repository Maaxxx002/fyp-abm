"""
CLAUDE.md Test 1 — ODE convergence.

Behaviour off, well-mixed, large N: final susceptible fraction must match the
Weitz ODE reference (register D1: R0=3.000 -> S_inf ~ 0.0594).

Context this test resolves: docs/Decision_Register.md A20/D1 name Gozzi's
12-sub-steps-per-day scheme as the settled fix for the R0-inflation bug
(naive 1-exp(-rate) at a 1-day step -> R0=3.257). experiments/abm.py does not
implement 12 sub-steps -- it uses a single step per day with the raw daily
rate as the transition probability for the E->I/I->R/H->D dwell-time
transitions (see its own comment), and 1-exp(-rate) only for the S->E force
of infection. That's a different technique from the one named in the
register. Empirically (checked here, and manually with 20 seeds during
setup: mean final S 0.05900 vs ODE 0.05952, well within stochastic noise of
std ~0.0014), it converges to the correct R0 anyway. This test exists so
that fact is checked by CI rather than re-argued from memory every session.

If this test ever starts failing after a code change, don't just widen the
tolerance -- that's the exact failure mode D1 describes ("invisible in any
single run").
"""
import numpy as np
from scipy.integrate import solve_ivp

from abm import run
from metrics import BETA, MU, GAMMA, FD

R0 = 3.0
N = 100_000
N_SEEDS = 10
DAYS = 900
TARGET_S = 0.0594          # CLAUDE.md's stated target, register D1
TOLERANCE = 0.02            # relative; see docstring for why not "3 decimals" on raw output


def _ode_final_S(R0=R0, T_H=14.0, days=DAYS):
    beta = R0 * GAMMA
    gH = 1 / T_H

    def rhs(t, y):
        S, E, I, H, R, D = y
        foi = beta * S * I
        return [-foi, foi - MU * E, MU * E - GAMMA * I,
                FD * GAMMA * I - gH * H, (1 - FD) * GAMMA * I, gH * H]

    S0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1 - S0, 0, S0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    return sol.sol(days)[0]


def test_ode_reference_matches_claude_md_target():
    """Sanity check on the reference itself, not the ABM."""
    ode_S = _ode_final_S()
    assert abs(ode_S - TARGET_S) < 5e-4, (
        f"ODE final S={ode_S:.5f} drifted from CLAUDE.md's stated 0.0594 "
        f"-- check R0/GAMMA/MU/FD/T_H haven't diverged from register A2/A20."
    )


def test_no_behaviour_matches_ode_final_size():
    ode_S = _ode_final_S()
    finals = np.array([
        run(N=N, dc=1.0, seed=s, days=DAYS, behaviour=False)["S"][-1]
        for s in range(N_SEEDS)
    ])
    mean_S = finals.mean()
    rel_err = abs(mean_S - ode_S) / ode_S
    # Denominator (CLAUDE.md's "report the denominator" convention): all
    # N_SEEDS runs used, none excluded -- the epidemic reliably burns out
    # well before `days` at this N (confirmed: days=600 vs 900 give
    # identical results), so none are truncated mid-run.
    assert rel_err < TOLERANCE, (
        f"mean final S over {N_SEEDS} seeds = {mean_S:.5f} vs ODE {ode_S:.5f} "
        f"({rel_err*100:.2f}% relative error, tolerance {TOLERANCE*100:.0f}%)"
    )
