"""
CLAUDE.md Test 1 — ODE convergence.

Behaviour off, well-mixed, large N: final susceptible fraction must match the
Weitz ODE reference (Decision_Register.md A2: R0=3.0, 2 d latent, 6 d
infectious, f_D=0.01 -> S_inf = 0.05952 exactly; CLAUDE.md states this to
three decimals as 0.0594).

Repointed at src/model.py (register G2): this now guards the actual model,
not the experiments/abm.py pilot -- experiments/abm.py is untouched and no
longer imported here. Register C9 measured 48 sub-steps/day at 0.05% relative
error (N=100,000, 30 seeds), an order of magnitude inside the 1% tolerance
now used (register G1: tightened from 2%, which was loosened only to
accommodate the since-superseded 12-sub-step scheme).
"""
import numpy as np
from scipy.integrate import solve_ivp

from model import run

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N = 100_000
N_SEEDS = 30
DAYS = 900
TARGET_S = 0.0594          # CLAUDE.md's stated target (three decimals); register A2/C9
TOLERANCE = 0.01            # relative; register G1 -- tightened now the model lives in src/


def _ode_final_S(R0=R0, T_H=T_H, days=DAYS):
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate

    def rhs(t, y):
        Sf, Ef, If, Hf, Rf, Df = y
        foi = transmission_rate * Sf * If
        return [-foi, foi - latent_rate * Ef, latent_rate * Ef - infectious_rate * If,
                F_D * infectious_rate * If - death_delay_rate * Hf,
                (1 - F_D) * infectious_rate * If, death_delay_rate * Hf]

    I0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1 - I0, 0, I0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    return sol.sol(days)[0]


def test_ode_reference_matches_claude_md_target():
    """Sanity check on the reference itself, not the model."""
    ode_S = _ode_final_S()
    assert abs(ode_S - TARGET_S) < 5e-4, (
        f"ODE final S={ode_S:.5f} drifted from CLAUDE.md's stated 0.0594 "
        f"-- check R0/latent/infectious/f_D haven't diverged from register A2."
    )


def test_no_behaviour_matches_ode_final_size():
    ode_S = _ode_final_S()
    finals = np.array([
        run(N=N, seed=s, days=DAYS,
            R0=R0, latent_period_days=LATENT_PERIOD_DAYS,
            infectious_period_days=INFECTIOUS_PERIOD_DAYS, f_D=F_D, T_H=T_H)["S"][-1]
        for s in range(N_SEEDS)
    ])
    mean_S = finals.mean()
    rel_err = abs(mean_S - ode_S) / ode_S
    # Denominator (CLAUDE.md's "report the denominator" convention): all
    # N_SEEDS runs used, none excluded -- the epidemic reliably burns out
    # well before `days` at this N, so none are truncated mid-run.
    assert rel_err < TOLERANCE, (
        f"mean final S over {N_SEEDS} seeds = {mean_S:.5f} vs ODE {ode_S:.5f} "
        f"({rel_err*100:.2f}% relative error, tolerance {TOLERANCE*100:.0f}%)"
    )
