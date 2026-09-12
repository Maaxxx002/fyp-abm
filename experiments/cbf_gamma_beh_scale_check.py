"""
Check: does arm 1's actual sourced trigger constant (CBF's gamma_beh, NOT Weitz's
delta_c) land in the "safe" (tens-hundreds) or "broken" (single-digit) count
regime at N=3,000 -- the project's actual settled operating population,
not the N=100,000 used for Test 1/2 validation. Follow-up to the
delta_c sweep (Decision_Register.md C12).

Part 1 -- source verification (not run here, done via direct fetch of
github.com/ngozzi/covid-behavior-models):
  models/compartment_model_age_deaths.py implements CBF's global mechanism as

      prob_S_to_SB = beta_B * (1 - exp(-gamma * deaths_yesterday))

  where `gamma` is passed as an exponent, i.e. gamma_beh = 10**gamma. The
  ONLY concrete numeric values anywhere in the repo (constants.py has none;
  no calibrated per-city posterior is published as a single canonical value
  -- Decision_Register.md E8) are the authors' own demo defaults in
  example.ipynb, cell 10, run against Madrid data (N=6,779,888):

      beta_B=0.5, mu_B=0.01, r=0.5, gamma=0 (i.e. gamma_beh=10^0=1)

  swept illustratively over gamma_beh in {1, 0.1, 0.01, 0.001} (gamma in
  {0,-1,-2,-3}). This is Gozzi's own code default, same evidentiary status
  as the daily_steps=12 default used for A20/C9 -- NOT a fitted/canonical
  value (per-city ABC posteriors differ and are not published as one number).

Part 2 -- translation ambiguity, reported not resolved:
  Weitz's delta_c is already a literal raw-count threshold (units:
  deaths/day), directly comparable across models. gamma_beh is the rate
  constant of an EXPONENTIAL saturating function acting on
  `deaths_yesterday` (a raw one-day death COUNT, a flow) -- structurally
  different from Weitz's power-law (delta/delta_c)^k acting on a
  continuous H-compartment STOCK. Two independent translation choices are
  needed and neither is settled:
    (a) which percentile of saturation defines "the" threshold count
        (this script reports both the half-saturation count ln(2)/gamma_beh
        and the e-folding count 1/gamma_beh -- they differ by <1.5x, so the
        choice does not change the qualitative conclusion below);
    (b) this project's actual arm-1 design drives CBF from a SMOOTHED
        rolling-mean death signal (Design_Spec_Perception_and_Population.md
        Sec 3: `deaths_7day_mean`; Decision_Register.md A8/C7 settled on a
        28-day mean project-wide), not Gozzi's literal same-day/previous-day
        raw count that gamma_beh was demonstrated against. Reusing gamma_beh
        unchanged against a differently-scaled smoothed input is not a
        well-defined operation without a re-derivation this script does NOT
        attempt.

Part 3 -- what CAN be computed/simulated cleanly, independent of (a)/(b):
  the actual raw-count SCALE that a N=3,000 epidemic produces, with
  behaviour OFF (the upper bound -- any working behavioural throttle only
  shrinks these further). This bypasses the translation ambiguity entirely:
  regardless of which specific rule or parameterisation drives it, if the
  raw counts an N=3,000 run produces are already single-digit, no
  count-based trigger can escape the small-count regime C12 showed is
  biased.
"""
import numpy as np

S_, E_, I_, H_, R_, D_ = 0, 1, 2, 3, 4, 5

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N_SUBSTEPS = 48
SEEDS_INFECTED = 10
DAYS = 600
N_PROJECT = 3_000
N_SEEDS = 30

# Gozzi's own demo default (example.ipynb cell 10, Madrid, N=6,779,888)
GAMMA_BEH_DEMO = 1.0      # = 10**0
N_MADRID_DEMO = 6_779_888


def run_peak_counts(N, seed, days=DAYS, n_substeps=N_SUBSTEPS):
    """Disease-only (behaviour OFF) -- the largest H/death-count scale
    possible; any working behavioural throttle only shrinks these."""
    dt = 1.0 / n_substeps
    latent_rate = 1.0 / LATENT_PERIOD_DAYS
    infectious_rate = 1.0 / INFECTIOUS_PERIOD_DAYS
    death_delay_rate = 1.0 / T_H
    transmission_rate = R0 * infectious_rate
    p_e_to_i = 1 - np.exp(-latent_rate * dt)
    p_i_to_leave = 1 - np.exp(-infectious_rate * dt)
    p_h_to_d = 1 - np.exp(-death_delay_rate * dt)

    rng = np.random.default_rng(seed)
    state = np.zeros(N, dtype=np.int8)
    state[rng.choice(N, SEEDS_INFECTED, replace=False)] = I_
    peak_H = 0
    peak_daily_deaths = 0
    for t in range(days):
        day_new_d = 0
        for _ in range(n_substeps):
            infectious_mask = (state == I_)
            n_infectious = np.count_nonzero(infectious_mask)
            foi = transmission_rate * n_infectious / N
            p_s_to_e = 1 - np.exp(-foi * dt)
            new_e = (state == S_) & (rng.random(N) < p_s_to_e)
            new_i = (state == E_) & (rng.random(N) < p_e_to_i)
            leaving_i = infectious_mask & (rng.random(N) < p_i_to_leave)
            to_h = leaving_i & (rng.random(N) < F_D)
            to_r = leaving_i & ~to_h
            new_d = (state == H_) & (rng.random(N) < p_h_to_d)
            state[new_d] = D_; state[to_h] = H_; state[to_r] = R_; state[new_i] = I_; state[new_e] = E_
            n_H = np.count_nonzero(state == H_)
            if n_H > peak_H:
                peak_H = n_H
            day_new_d += np.count_nonzero(new_d)
        if day_new_d > peak_daily_deaths:
            peak_daily_deaths = day_new_d
        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            break
    return peak_H, peak_daily_deaths


def main():
    print("Part 2 -- translation calculation (both flagged as a choice, not a fact):")
    half_sat_madrid = np.log(2) / GAMMA_BEH_DEMO
    efold_madrid = 1.0 / GAMMA_BEH_DEMO
    print(f"  At Gozzi's own demo scale (Madrid, N={N_MADRID_DEMO:,}, gamma_beh={GAMMA_BEH_DEMO}):")
    print(f"    half-saturation count ln(2)/gamma_beh = {half_sat_madrid:.3f} deaths/day")
    print(f"    e-folding count 1/gamma_beh           = {efold_madrid:.3f} deaths/day")
    print(f"    -> already sub-single-digit at the AUTHORS' OWN reference population,")
    print(f"       before any rescaling for our N={N_PROJECT:,}.")

    gamma_beh_rescaled = GAMMA_BEH_DEMO * (N_MADRID_DEMO / N_PROJECT)
    half_sat_rescaled = np.log(2) / gamma_beh_rescaled
    print(f"\n  IF rescaled the same way delta_c was (proportional to N, i.e."
          f" gamma_beh_project = gamma_beh_demo * N_demo/N_project):")
    print(f"    gamma_beh at N={N_PROJECT:,} = {gamma_beh_rescaled:.1f}")
    print(f"    implied half-saturation count = {half_sat_rescaled:.5f} deaths/day")
    print(f"    -> even more extreme: saturates on the very first death.")

    print("\nPart 3 -- direct simulation, translation-independent "
          f"(N={N_PROJECT:,}, {N_SEEDS} seeds, days={DAYS}, behaviour OFF):")
    peakH, peakD = [], []
    for seed in range(N_SEEDS):
        ph, pd_ = run_peak_counts(N_PROJECT, seed)
        peakH.append(ph)
        peakD.append(pd_)
    peakH = np.array(peakH)
    peakD = np.array(peakD)
    print(f"  peak H (stock, agents):        mean={peakH.mean():.2f} std={peakH.std():.2f} "
          f"min={peakH.min()} max={peakH.max()}  [{N_SEEDS}/{N_SEEDS} seeds]")
    print(f"  peak daily deaths (flow, raw): mean={peakD.mean():.2f} std={peakD.std():.2f} "
          f"min={peakD.min()} max={peakD.max()}  [{N_SEEDS}/{N_SEEDS} seeds]")
    print("\n  For reference (C12, N=100,000): 'broken' regime was peak H~23 (4.56% error);")
    print("  'safe' regime was peak H>=66.5 (<=0.14% error, except a 0.80%/2.23-SEM point at 172.5).")
    print(f"  At N={N_PROJECT:,} with behaviour OFF (the upper bound), peak H and peak daily")
    print("  deaths are already at or below the 'broken' scale -- with behaviour ON (which")
    print("  only suppresses transmission further), the true operating scale is <= these numbers.")


if __name__ == "__main__":
    main()
