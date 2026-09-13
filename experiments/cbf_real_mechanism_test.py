"""
CBF's REAL mechanism (Decision_Register.md D12/E17), not the `direct-g`
simplification C16/C17 used (D12 confirmed direct-g is NOT a valid stand-in
for CBF: CBF is a genuine two-compartment, memory-laden model, not an
instantaneous multiplier). This is the test D12/E17 asked for and C16/C17
deliberately withheld: does the REAL S/S^B mechanism recover the mean-field
(ODE-level) reference at N=3,000, 10,000, and 30,000?

Mechanism (src/model.py's `run_cbf_behaviour`, verified directly against
Gozzi's own `compartment_model_age_deaths.py`, lines ~114-126):

    prob_S_to_SB(t) = beta_B * (1 - exp(-gamma_beh * D(t)))   -- adoption rate
    prob_SB_to_S(t) = mu_B * (S(t) + R(t)) / N                -- relaxation rate
    S^B infected at the PER-AGENT reduced rate r_i * (force of infection)

Sub-step competing-hazards transitions exactly as Gozzi's code: one joint
"did this agent leave the compartment" draw, then split by relative hazard.
beta_B=0.5, mu_B=0.01, gamma_beh=1 -- Gozzi's own sourced demo values
(Sourcing_Pack_v3.md Sec 2b, Decision_Register.md C13), unmodified. D(t) =
28-day rolling mean of daily deaths (A8/C7), using days strictly before
today with a shrinking window for the first 28 days -- the project's actual
settled signal, not Gozzi's own literal yesterday-count (confirmed the
right choice for CBF's mechanism in C17, though C17 only tested it against
the `direct-g` simplification).

UPDATE (Decision_Register.md C21/C22): `r` is no longer a flat scalar
(r_factor=0.5, C18/C19's original round) -- it is now per-agent,
`r_i = 1 - response_efficacy_i`, drawn from a real quota-drawn
`src/population.py` Population (Beta(2,2), the design spec's proposed
default). ⚠️ The DDE reference below (`_rhs`/`ode_final_S`) is UNCHANGED and
still assumes a single shared `r_factor` (still defaulting to 0.5) for the
whole S^B compartment -- it does NOT account for the response_efficacy
distribution. That is a deliberate, stated limitation of this comparison
(a bigger, separate task to fix properly), not an oversight: this round
changes only the ABM side, so the ABM-vs-DDE comparison below is not fully
apples-to-apples on the reference side, only on the ABM side relative to
C18/C19.

Reference: a genuine delay-differential-equation system (the 28-day mean is
a trailing integral, not expressible as a plain ODE), 7 states
(S, S^B, E, I, H, R, D), fixed-step (dt=0.25 day) RK4, same "shrinking
window, days strictly before today" convention as the ABM, and the same
integrator structure C17 used for the simpler (no-S^B) case. Sanity-checked
below (`sanity_check_against_test1`) against Test 1's known ODE target
(0.05952 at R0=3, CLAUDE.md/Decision_Register.md C9) with beta_B=0 -- with
no adoption, S^B never receives inflow and the system collapses to exactly
the validated no-behaviour 6-state system, so this checks the integrator
itself before trusting its behavioural-mode output (register C17's stated
methodology, repeated here since this is a genuinely different model, not
just a parameter change).
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from model import run_cbf_behaviour  # noqa: E402
from population import build_population  # noqa: E402

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N_SUBSTEPS = 48
SEEDS_INFECTED = 10
DAYS = 900          # matches C16/C17's convergence-testing convention, not the 600-day production run length
N_SEEDS = 30
BETA_B = 0.5        # Gozzi's own sourced demo default (C13), as-is
MU_B = 0.01         # Gozzi's own sourced demo default (C13), as-is
R_FACTOR = 0.5      # kept ONLY for the DDE reference below, which still assumes a flat r
                    # (see module docstring's C21/C22 update note) -- the ABM no longer uses this
GAMMA_BEH = 1.0     # Gozzi's own sourced demo default (C13), as-is -- not swept
WINDOW = 28         # A8/C7's settled awareness window
N_VALUES = [3_000, 10_000, 30_000]
POPULATION_SEED = 0  # fixed population-construction seed (unrelated to disease-run seeds),
                     # same convention as tests/test_population.py and register C21

_LATENT_RATE = 1.0 / LATENT_PERIOD_DAYS
_INFECTIOUS_RATE = 1.0 / INFECTIOUS_PERIOD_DAYS
_DEATH_DELAY_RATE = 1.0 / T_H
_TRANSMISSION_RATE = R0 * _INFECTIOUS_RATE

# ODE test-1 target, CLAUDE.md / Decision_Register.md C9 (R0=3 exactly)
TEST1_ODE_TARGET = 0.05952
TEST1_TOLERANCE = 0.001  # 3 decimals, per CLAUDE.md Test 1


def _rhs(y, adoption_rate, r_factor):
    """7-state DDE right-hand side: s, sb, e, i, h, r, d (all fractions of N)."""
    s, sb, e, i, h, r, d = y
    foi = _TRANSMISSION_RATE * i
    flow_s_to_e = foi * s
    flow_s_to_sb = adoption_rate * s
    flow_sb_to_s = MU_B * (s + r) * sb
    flow_sb_to_e = r_factor * foi * sb
    return np.array([
        -flow_s_to_e - flow_s_to_sb + flow_sb_to_s,
        flow_s_to_sb - flow_sb_to_s - flow_sb_to_e,
        flow_s_to_e + flow_sb_to_e - _LATENT_RATE * e,
        _LATENT_RATE * e - _INFECTIOUS_RATE * i,
        F_D * _INFECTIOUS_RATE * i - _DEATH_DELAY_RATE * h,
        (1 - F_D) * _INFECTIOUS_RATE * i,
        _DEATH_DELAY_RATE * h,
    ])


def ode_final_S(N, beta_B=BETA_B, mu_B=MU_B, r_factor=R_FACTOR, gamma_beh=GAMMA_BEH,
                 window=WINDOW, days=DAYS, dt=0.25):
    """RK4 integration of the 7-state S/S^B DDE. Returns (final S = s+sb, final H count)."""
    n_steps = int(round(days / dt))
    steps_per_window = int(round(window / dt))
    assert abs(steps_per_window * dt - window) < 1e-9, "dt must evenly divide the window"

    I0 = 1e-6
    y = np.array([1 - I0, 0.0, 0.0, I0, 0.0, 0.0, 0.0])  # s, sb, e, i, h, r, d
    dcum_history = np.zeros(n_steps + 1)
    dcum_history[0] = y[6]

    for step in range(n_steps):
        t_days = step * dt
        if step == 0:
            D_delay = 0.0
        elif step < steps_per_window:
            D_delay = N * dcum_history[step] / t_days
        else:
            D_delay = N * (dcum_history[step] - dcum_history[step - steps_per_window]) / window
        adoption_rate = beta_B * (1.0 - np.exp(-gamma_beh * D_delay))

        k1 = _rhs(y, adoption_rate, r_factor)
        k2 = _rhs(y + 0.5 * dt * k1, adoption_rate, r_factor)
        k3 = _rhs(y + 0.5 * dt * k2, adoption_rate, r_factor)
        k4 = _rhs(y + dt * k3, adoption_rate, r_factor)
        y = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        dcum_history[step + 1] = y[6]

    final_S = y[0] + y[1]  # s + sb: never-infected fraction
    return final_S, y[4] * N  # final H in agent-count units


def sanity_check_against_test1():
    """beta_B=0 -> S^B never receives inflow -> collapses exactly to the
    validated no-behaviour 6-state system. Must reproduce Test 1's known
    target (0.05952, register C9) before this DDE is trusted for anything
    else -- same check C17 ran on its own (simpler) DDE reference."""
    final_S, _ = ode_final_S(N=100_000, beta_B=0.0, days=900)
    rel_err = abs(final_S - TEST1_ODE_TARGET) / TEST1_ODE_TARGET
    print(f"Sanity check (beta_B=0, N=100,000, days=900): "
          f"DDE final S = {final_S:.5f} vs Test 1 target {TEST1_ODE_TARGET:.5f} "
          f"({rel_err*100:.4f}% relative error)")
    assert abs(final_S - TEST1_ODE_TARGET) < 0.001, (
        f"DDE reference does not collapse to Test 1's target with beta_B=0: "
        f"{final_S:.5f} vs {TEST1_ODE_TARGET:.5f}"
    )
    print("Sanity check PASSED -- DDE integrator trusted for behavioural-mode use.\n")


def _worker(args):
    N, seed, response_efficacy = args
    t0 = time.time()
    result = run_cbf_behaviour(
        N=N, seed=seed, response_efficacy=response_efficacy,
        days=DAYS, seeds_infected=SEEDS_INFECTED,
        R0=R0, latent_period_days=LATENT_PERIOD_DAYS,
        infectious_period_days=INFECTIOUS_PERIOD_DAYS,
        f_D=F_D, T_H=T_H, n_substeps=N_SUBSTEPS,
        beta_B=BETA_B, mu_B=MU_B, gamma_beh=GAMMA_BEH, window=WINDOW,
    )
    s_final = float(result["S"][-1])
    peak_d = float(result["deaths"].max())
    return N, seed, s_final, peak_d, time.time() - t0


def main(n_seeds=N_SEEDS):
    sanity_check_against_test1()

    ode_targets = {}
    for N in N_VALUES:
        ode_S, ode_H = ode_final_S(N)
        ode_targets[N] = ode_S
        print(f"N={N:,}: ODE final S = {ode_S:.5f}, ODE final H = {ode_H:.2f}")
    print(flush=True)

    # One frozen Population per N (register C21/CLAUDE.md hard constraint 6: drawn once,
    # reused across every seed). response_efficacy is the only field run_cbf_behaviour needs.
    populations = {N: build_population(N=N, seed=POPULATION_SEED) for N in N_VALUES}
    for N in N_VALUES:
        re = populations[N].response_efficacy
        print(f"N={N:,}: population built (seed={POPULATION_SEED}), "
              f"response_efficacy mean={re.mean():.4f} (r_i mean={1-re.mean():.4f})")
    print(flush=True)

    tasks = [
        (N, seed, populations[N].response_efficacy)
        for N in N_VALUES for seed in range(n_seeds)
    ]
    results = {N: {"S": [None] * n_seeds, "peakD": [None] * n_seeds} for N in N_VALUES}
    t_start = time.time()
    done = 0
    with mp.Pool(min(len(tasks), 16)) as pool:
        for N, seed, s_final, peak_d, dt in pool.imap_unordered(_worker, tasks):
            results[N]["S"][seed] = s_final
            results[N]["peakD"][seed] = peak_d
            done += 1
            print(f"[{done}/{len(tasks)}] N={N} seed={seed} final_S={s_final:.5f} "
                  f"peak_daily_deaths={peak_d:.0f} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)",
                  flush=True)

    print("\n=== SUMMARY (REAL CBF mechanism: S/S^B compartments, competing hazards, "
          "28-day mean signal, beta_B=0.5/mu_B=0.01/gamma_beh=1 as sourced, "
          "PER-AGENT r_i = 1 - response_efficacy_i, C21) ===")
    print("WARNING: DDE reference unchanged: still assumes a single flat r=0.5 for the whole "
          "S^B compartment -- does NOT account for the response_efficacy distribution. "
          "This comparison is apples-to-apples on the ABM side vs C18/C19 only.\n")
    # C18's original 30-seed flat-r=0.5 relative errors, for direct comparison (register).
    C18_RELATIVE_ERROR = {3_000: 0.0454, 10_000: 0.0443, 30_000: 0.0563}

    summary = {
        "beta_B": BETA_B, "mu_B": MU_B, "gamma_beh": GAMMA_BEH,
        "window": WINDOW, "days": DAYS, "n_substeps": N_SUBSTEPS, "n_seeds": n_seeds,
        "population_seed": POPULATION_SEED,
        "note": "r is now per-agent (r_i = 1 - response_efficacy_i); the DDE reference still "
                "assumes a single flat r (see ode_final_S's r_factor default) and was NOT "
                "changed to account for the response_efficacy distribution.",
        "results": {},
    }
    for N in N_VALUES:
        ode_S = ode_targets[N]
        s_arr = np.array([v for v in results[N]["S"] if v is not None])
        d_arr = np.array([v for v in results[N]["peakD"] if v is not None])
        n_used = len(s_arr)
        mean_S = float(s_arr.mean())
        sem_S = float(s_arr.std(ddof=1) / np.sqrt(n_used))
        rel_err = abs(mean_S - ode_S) / ode_S
        gap_sems = (mean_S - ode_S) / sem_S
        c18_rel_err = C18_RELATIVE_ERROR[N]
        summary["results"][str(N)] = {
            "ode_final_S": ode_S, "finals_S": results[N]["S"], "finals_peakD": results[N]["peakD"],
            "n_seeds_used": n_used, "mean_final_S": mean_S, "sem_final_S": sem_S,
            "relative_error": rel_err, "gap_sems": gap_sems,
            "mean_peak_daily_deaths": float(d_arr.mean()),
            "population_response_efficacy_mean": float(populations[N].response_efficacy.mean()),
            "c18_flat_r_relative_error": c18_rel_err,
        }
        # Denominator (CLAUDE.md convention): report how many of n_seeds this statistic is defined on.
        print(f"N={N:>7,}: {n_used}/{n_seeds} seeds, "
              f"mean peak daily deaths = {d_arr.mean():.1f}, "
              f"mean final S = {mean_S:.5f} (ODE {ode_S:.5f}), "
              f"relative error = {rel_err*100:.2f}% ({gap_sems:.2f} SEMs) "
              f"[C18 flat-r=0.5: {c18_rel_err*100:.2f}%]")

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "results"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "results", "cbf_real_mechanism_test.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
