"""
Follow-up to C13: repeats the disease-only (behaviour OFF) ceiling
simulation at N=10,000 and N=30,000, alongside N=3,000 for comparison, to
see the real peak-H / peak-daily-deaths scaling relationship instead of
assuming linearity from the single N=3,000 data point.

Same setup throughout: 30 seeds, 600 days, 48 sub-steps/day, behaviour OFF
(the ceiling -- any working behavioural throttle only shrinks these
further). Disease parameters as in Decision_Register.md/CLAUDE.md settled
numbers (R0=3.0, latent=2d, infectious=6d, f_D=0.01 flat, T_H=14d).
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
N_SEEDS = 30
N_VALUES = [3_000, 10_000, 30_000]


def run_peak_counts(N, seed, days=DAYS, n_substeps=N_SUBSTEPS):
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
    print(f"Disease-only (behaviour OFF) ceiling, {N_SEEDS} seeds, {DAYS} days, "
          f"{N_SUBSTEPS} substeps/day:\n")
    rows = []
    for N in N_VALUES:
        peakH, peakD = [], []
        for seed in range(N_SEEDS):
            ph, pd_ = run_peak_counts(N, seed)
            peakH.append(ph)
            peakD.append(pd_)
        peakH = np.array(peakH)
        peakD = np.array(peakD)
        rows.append((N, peakH, peakD))
        print(f"N={N:>7,}: peak H mean={peakH.mean():7.2f} std={peakH.std():6.2f} "
              f"min={peakH.min():4d} max={peakH.max():4d}  |  "
              f"peak daily deaths mean={peakD.mean():5.2f} std={peakD.std():5.2f} "
              f"min={peakD.min():3d} max={peakD.max():3d}  [{N_SEEDS}/{N_SEEDS} seeds]")

    print("\nScaling ratios (relative to N=3,000):")
    base_N, base_H, base_D = rows[0][0], rows[0][1].mean(), rows[0][2].mean()
    for N, peakH, peakD in rows:
        print(f"  N={N:>7,}: N-ratio={N/base_N:6.2f}x  "
              f"peak-H-ratio={peakH.mean()/base_H:6.2f}x  "
              f"peak-deaths-ratio={peakD.mean()/base_D:6.2f}x")


if __name__ == "__main__":
    main()
