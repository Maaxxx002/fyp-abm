"""
Design_Spec_Perception_and_Population.md Sec 5's state-count measurement --
"the measurement that decides whether caching is worth building" -- run at
N=10,000 and N=30,000 (this session's ceiling-scaling N values), using a
SIMPLE STAND-IN decision rule, NOT the real CBF (which does not exist in
src/ yet -- no arm-1/arm-2 building this round).

Fields used, and why these and not the full 8-factor combinatorial table
from the design spec (10 age x 3 occ x 3 eff x 3 health x 8 death-level x
6 cumulative x 10 norm x 4 local-death, ~4.6-5.2e5):

  INCLUDED (computable from what already exists / is already a settled
  default, without inventing anything or building arm 1):
    - age_band (10)      -- quota-drawn per Design_Spec Sec 6's sourced
                             New York shares, generalised to arbitrary N.
    - occupation_flex (3) -- Design_Spec Sec 3: fixed 0.5 for school-age,
                             fixed 1.0 for retired, Beta(2,2) draw for
                             working-age -- an already-decided provisional
                             default, not invented here. Binned into 3
                             equal-width bins over [0,1].
    - response_efficacy (3) -- Design_Spec Sec 4: Beta(2,2) for everyone,
                             same default. Binned the same way.
    - own_health (3)      -- fully specified observation model (Sec 2a):
                             S,E -> never_ill; I -> currently_ill; R ->
                             recovered; H,D -> agent no longer decides
                             (excluded from that day's decision count).
    - deaths_28day_mean_percap (8 bins) -- A8/C7's settled 28-day window,
                             per-capita so it's comparable across N.
    - cumulative_deaths_percap (6 bins)
    - social_norm = (S+R)/N (10 bins) -- CBF's relaxation term, already
                             sourced (Design_Spec Sec 3 table).

  EXCLUDED, and why (not silently -- reported):
    - local_deaths_7d (CBF's *local*, contact-weighted mechanism) --
      requires an age-contact matrix / network structure that does not
      exist in src/model.py's well-mixed disease model (A5). In a
      literally well-mixed population "local" reduces to "global" and
      would add zero extra states here, not a meaningful 4x factor as in
      the design spec's ceiling table. Omitting it UNDERSTATES the true
      combinatorial ceiling (by the factor of 4 in that table) and likely
      UNDERSTATES the realised state count too -- flagged, not fixed.

  Bin edges for the three dynamic (population-wide) fields are FIXED and
  chosen by hand for this diagnostic -- Design_Spec Sec 8 item 2 states
  bin count/edges are explicitly "provisional; settle with the Sec 5
  state-count run," i.e. this run. They are NOT sourced and should not be
  read as a proposal, only as one reasonable placeholder:
    deaths_28day_mean_percap: 8 equal-width bins over [0, 0.001]
    cumulative_deaths_percap: 6 equal-width bins over [0, 0.01]
    social_norm:              10 equal-width bins over [0.5, 1.0]

  Decision cadence: every decision-eligible agent (not in H or D) is
  logged EVERY day (p=1, daily) -- the design spec's own re-decision
  cadence p is a separate, still-open item (item 4). p=1 is the upper
  bound on total decisions (the denominator); a lower cadence only
  reduces total decisions, it cannot increase the distinct-state count
  (the numerator), so the ratio reported here is the most conservative
  (worst-case-for-caching) one for whatever p is eventually chosen.
"""
import numpy as np

S_, E_, I_, H_, R_, D_ = 0, 1, 2, 3, 4, 5
NEVER_ILL, CURRENTLY_ILL, RECOVERED = 0, 1, 2

R0 = 3.0
LATENT_PERIOD_DAYS = 2.0
INFECTIOUS_PERIOD_DAYS = 6.0
F_D = 0.01
T_H = 14.0
N_SUBSTEPS = 48
SEEDS_INFECTED = 10
DAYS = 600
DEATHS_WINDOW = 28

# Design_Spec_Perception_and_Population.md Sec 6, New York age shares (sum ~100%)
AGE_SHARES = [0.1102, 0.1123, 0.0625, 0.0800, 0.1572,
              0.1259, 0.1252, 0.1111, 0.0734, 0.0423]
N_AGE_BANDS = 10
# approximation for this diagnostic only: bands 0-9,10-19 = school-age (fixed 0.5);
# 20-24..50-59 = working-age (free Beta(2,2)); 60-69,70-79,80+ = retired (fixed 1.0).
# The real age-band edges don't align cleanly with the 65 cutoff (60-69 straddles
# it); this is a stand-in approximation, not a sourced rule.
SCHOOL_AGE_BANDS = {0, 1}
RETIRED_AGE_BANDS = {7, 8, 9}

N_OCC_BINS = 3
N_EFF_BINS = 3
N_DEATH_BINS = 8
N_CUM_BINS = 6
N_NORM_BINS = 10

DEATH_BIN_MAX = 0.001    # per-capita, deaths_28day_mean -- hand-picked, provisional
CUM_BIN_MAX = 0.01       # per-capita, cumulative deaths -- hand-picked, provisional
NORM_RANGE = (0.5, 1.0)  # social_norm=(S+R)/N -- hand-picked, provisional


def quota_age_bands(N, seed):
    rng = np.random.default_rng(seed + 10_000_000)
    counts = [int(round(s * N)) for s in AGE_SHARES]
    counts[-1] += N - sum(counts)  # largest-remainder-style correction on last band
    bands = np.repeat(np.arange(N_AGE_BANDS), counts)
    rng.shuffle(bands)
    return bands.astype(np.int16)


def build_population(N, seed):
    rng = np.random.default_rng(seed + 20_000_000)
    age_band = quota_age_bands(N, seed)
    occ_flex = np.empty(N)
    is_school = np.isin(age_band, list(SCHOOL_AGE_BANDS))
    is_retired = np.isin(age_band, list(RETIRED_AGE_BANDS))
    is_working = ~is_school & ~is_retired
    occ_flex[is_school] = 0.5
    occ_flex[is_retired] = 1.0
    occ_flex[is_working] = rng.beta(2, 2, size=is_working.sum())
    resp_eff = rng.beta(2, 2, size=N)

    occ_bin = np.clip((occ_flex * N_OCC_BINS).astype(int), 0, N_OCC_BINS - 1)
    eff_bin = np.clip((resp_eff * N_EFF_BINS).astype(int), 0, N_EFF_BINS - 1)
    static_id = (age_band * N_OCC_BINS + occ_bin) * N_EFF_BINS + eff_bin
    return static_id.astype(np.int32)  # one int per agent, range [0, 10*3*3)


def bin_value(x, lo, hi, n_bins):
    frac = (x - lo) / (hi - lo)
    return int(np.clip(frac * n_bins, 0, n_bins - 1))


def run_state_count(N, seed):
    static_id = build_population(N, seed)

    dt = 1.0 / N_SUBSTEPS
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

    daily_deaths = np.zeros(DAYS)
    seen_states = set()
    total_decisions = 0
    cumulative_deaths = 0

    for t in range(DAYS):
        day_new_d = 0
        for _ in range(N_SUBSTEPS):
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
            day_new_d += np.count_nonzero(new_d)

        daily_deaths[t] = day_new_d
        cumulative_deaths += day_new_d

        window_start = max(0, t - DEATHS_WINDOW + 1)
        death_mean_percap = daily_deaths[window_start:t + 1].mean() / N
        cum_percap = cumulative_deaths / N
        n_S = np.count_nonzero(state == S_)
        n_R = np.count_nonzero(state == R_)
        social_norm = (n_S + n_R) / N

        death_bin = bin_value(death_mean_percap, 0, DEATH_BIN_MAX, N_DEATH_BINS)
        cum_bin = bin_value(cum_percap, 0, CUM_BIN_MAX, N_CUM_BINS)
        norm_bin = bin_value(social_norm, NORM_RANGE[0], NORM_RANGE[1], N_NORM_BINS)
        day_suffix = (death_bin, cum_bin, norm_bin)

        eligible = (state != H_) & (state != D_)
        total_decisions += int(np.count_nonzero(eligible))

        for health, mask in ((NEVER_ILL, (state == S_) | (state == E_)),
                              (CURRENTLY_ILL, state == I_),
                              (RECOVERED, state == R_)):
            if mask.any():
                for sid in np.unique(static_id[mask]):
                    seen_states.add((int(sid), health) + day_suffix)

        if (np.count_nonzero(state == I_) == 0 and np.count_nonzero(state == E_) == 0
                and np.count_nonzero(state == H_) == 0):
            # epidemic over; remaining days would repeat the same (recovered-only,
            # settled dynamic bins) state -- no new distinct states, decisions
            # for the remaining days still counted at the settled rate
            remaining_days = DAYS - t - 1
            if remaining_days > 0:
                total_decisions += remaining_days * int(np.count_nonzero(eligible))
            break

    return len(seen_states), total_decisions


def main():
    combinatorial_ceiling = N_AGE_BANDS * N_OCC_BINS * N_EFF_BINS * 3 * N_DEATH_BINS * N_CUM_BINS * N_NORM_BINS
    print(f"Combinatorial ceiling under this stand-in's bins: {combinatorial_ceiling:,} "
          f"(design spec's own full 8-factor table: ~4.6-5.2e5; this stand-in omits "
          f"local_deaths_7d, a factor of 4, by construction -- see docstring)\n")

    for N in [10_000, 30_000]:
        n_states, n_decisions = run_state_count(N, seed=0)
        ratio = n_states / n_decisions
        print(f"N={N:>7,}: distinct states = {n_states:,} / total decisions = {n_decisions:,} "
              f"-> ratio = {ratio:.6f} ({1/ratio:,.0f}x compression if perfectly cached)")


if __name__ == "__main__":
    main()
