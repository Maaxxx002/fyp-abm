"""
Register E15: does the 2.34% Test-1 gap found under 12 sub-steps/day (C8) shrink
as sub-steps increase (-> discretisation bias, shrinks toward 0 as dt->0) or stay
flat (-> an implementation issue, not fixed by finer sub-stepping)?

Diagnostic only -- does not touch src/ or docs/.
"""
import numpy as np
from scipy.integrate import solve_ivp

from abm import run_gozzi12, run_gozzi24, run_gozzi48
from metrics import MU, GAMMA, FD

N = 100_000
N_SEEDS = 30
DAYS = 900
R0_TARGET = 3.0000
TARGET_S = 0.0594


def ode_final_S(R0=R0_TARGET, T_H=14.0, days=DAYS):
    beta = R0 * GAMMA
    gH = 1 / T_H

    def rhs(t, y):
        S, E, I, H, R, D = y
        foi = beta * S * I
        return [-foi, foi - MU*E, MU*E - GAMMA*I, FD*GAMMA*I - gH*H, (1-FD)*GAMMA*I, gH*H]

    S0 = 1e-6
    sol = solve_ivp(rhs, [0, days], [1-S0, 0, S0, 0, 0, 0],
                     dense_output=True, max_step=0.5, rtol=1e-10, atol=1e-14)
    return sol.sol(days)[0]


def implied_R0(S_inf):
    """Final-size relation ln(S_inf/S0) = -R0*(1-S_inf/S0), S0~1."""
    return -np.log(S_inf) / (1 - S_inf)


def main():
    ode_S = ode_final_S()
    print(f"ODE reference final S = {ode_S:.5f} (CLAUDE.md target {TARGET_S})\n")

    schemes = {12: run_gozzi12, 24: run_gozzi24, 48: run_gozzi48}
    rows = []

    for n_substeps, run_fn in schemes.items():
        finals = np.array([
            run_fn(N=N, dc=1.0, seed=s, days=DAYS, behaviour=False)["S"][-1]
            for s in range(N_SEEDS)
        ])
        r0_each = implied_R0(finals)
        mean_S = finals.mean()
        r0_mean = r0_each.mean()
        r0_std = r0_each.std(ddof=1)
        sem = r0_std / np.sqrt(N_SEEDS)
        gap_sem = (r0_mean - R0_TARGET) / sem
        rows.append((n_substeps, mean_S, r0_mean, r0_std, sem, gap_sem))
        print(f"n_substeps={n_substeps:>2}: per-seed final S = "
              f"{np.array2string(finals, precision=5, max_line_width=120)}")
        print(f"  denominator: {N_SEEDS}/{N_SEEDS} seeds (none excluded, none truncated)")
        print()

    print("=" * 100)
    print(f"{'substeps':>8} | {'mean final S':>13} | {'implied R0':>11} | "
          f"{'R0 std':>8} | {'SEM':>8} | {'gap from 3.0000 (SEM units)':>28}")
    print("-" * 100)
    for n_substeps, mean_S, r0_mean, r0_std, sem, gap_sem in rows:
        print(f"{n_substeps:>8} | {mean_S:>13.5f} | {r0_mean:>11.4f} | "
              f"{r0_std:>8.4f} | {sem:>8.4f} | {gap_sem:>28.2f}")
    print("=" * 100)

    gaps = [abs(r[5]) for r in rows]
    print(f"\n|gap in SEM units| by substep count: "
          f"{dict(zip(schemes.keys(), [round(g,2) for g in gaps]))}")
    shrinking = all(b <= a + 0.5 for a, b in zip(gaps, gaps[1:]))  # allow noise slack
    monotone_shrinking = gaps[0] > gaps[-1] and all(b <= a for a, b in zip(gaps, gaps[1:]))
    print(f"strictly non-increasing as substeps rise: {monotone_shrinking}")
    print(f"roughly non-increasing (0.5 SEM slack for noise): {shrinking}")
    if monotone_shrinking:
        print("-> pattern is CONSISTENT with a discretisation bias shrinking toward 0 as dt->0.")
    elif shrinking:
        print("-> pattern LEANS toward a shrinking discretisation bias, but not cleanly monotone at n=30 seeds.")
    else:
        print("-> pattern looks FLAT / does not shrink with finer sub-stepping -- "
              "consistent with an implementation issue rather than pure discretisation bias.")


if __name__ == "__main__":
    main()
