"""
Checks requested for register E11/E12/G3: does switching experiments/abm.py's
disease dynamics from a single daily step (`run`) to Gozzi's 12-sub-steps-per-day
scheme (`run_gozzi12`, register A20/D1) (a) still pass Test 1 (ODE convergence),
and (b) change the direction of the T_H -> wave-count relationship (register D6)?

This script only reports numbers with denominators. It does not modify docs/ and
draws no conclusion about closing D6 -- see CLAUDE.md's verification-before-claim
and report-the-denominator conventions.
"""
import numpy as np
from scipy.signal import find_peaks

from abm import run, run_gozzi12
from metrics import sm, ode

# ---------------------------------------------------------------------------
# Part 2 -- Test 1 (ODE convergence) under the 12-sub-step scheme
# ---------------------------------------------------------------------------

def implied_R0(S_inf):
    """Final-size relation ln(S_inf/S0) = -R0*(1-S_inf/S0), S0~1 (E/H add no
    extra transmission so this SIR relation still holds for the SEIR+H model)."""
    return -np.log(S_inf) / (1 - S_inf)


def part2():
    print("=" * 78)
    print("PART 2 -- Test 1 (ODE convergence) under run_gozzi12 (12 sub-steps/day)")
    print("=" * 78)
    N = 100_000
    N_SEEDS = 10
    DAYS = 900
    TARGET_S = 0.0594

    finals = np.array([
        run_gozzi12(N=N, dc=1.0, seed=s, days=DAYS, behaviour=False)["S"][-1]
        for s in range(N_SEEDS)
    ])
    mean_S = finals.mean()
    rel_err = abs(mean_S - TARGET_S) / TARGET_S
    r0_each = implied_R0(finals)

    print(f"N={N}, {N_SEEDS} seeds (0..{N_SEEDS-1}), behaviour off, days={DAYS}")
    print(f"per-seed final S: {np.array2string(finals, precision=5)}")
    print(f"denominator: {N_SEEDS}/{N_SEEDS} seeds (none excluded, none truncated mid-run)")
    print(f"mean final S      = {mean_S:.5f}  (ODE target {TARGET_S})")
    print(f"relative error    = {rel_err*100:.2f}%")
    print(f"implied R0 (mean S)         = {implied_R0(mean_S):.4f}  (target 3.000)")
    print(f"implied R0 (mean of per-seed R0) = {r0_each.mean():.4f} +/- {r0_each.std():.4f}")
    print()


# ---------------------------------------------------------------------------
# Part 3 -- T_H in {7,14,21,28} wave-count comparison, old vs new scheme
# ---------------------------------------------------------------------------

T_H_VALUES = [7, 14, 21, 28]
DC = 5e-6   # Weitz's dc, consistent with metrics.py's ode() default and the
K = 2       # "Weitz dc=5e-6" / k=2 case already used in this repo (metrics.py)
N_ABM = 3000        # register A7
N_SEEDS_WAVE = 20
DAYS_WAVE = 600     # register settled run length
FADEOUT_MIN_INF = 50  # below this, treat the run as a fadeout (not a real epidemic)

# Two "reasonable" prominence definitions -- register D6 says two such
# definitions disagree on identical runs. A wave train decays in amplitude, so
# these differ in a way that matters: "global" measures each peak's topographic
# prominence against the run's single tallest peak (kills later, smaller-but-real
# waves); "local" measures it against that peak's own height (an ODE sanity check,
# below, shows only "local" recovers a rising count with T_H at all -- "global"
# is ~flat). Both are reported; neither is silently preferred.
MIN_PEAK_DISTANCE_DAYS = 14
PROMINENCE_FRAC = 0.10


def _peaks_and_prominence(incidence, smooth_window=7, min_distance=MIN_PEAK_DISTANCE_DAYS):
    ys = sm(incidence, smooth_window)
    if ys.max() <= 0:
        return ys, np.array([], dtype=int), np.array([])
    peaks, props = find_peaks(ys, distance=min_distance, prominence=0)
    return ys, peaks, props["prominences"]


def count_waves_global(incidence, prominence_frac=PROMINENCE_FRAC, **kw):
    ys, peaks, prom = _peaks_and_prominence(incidence, **kw)
    if len(peaks) == 0:
        return 0
    return int(np.count_nonzero(prom >= prominence_frac*ys.max()))


def count_waves_local(incidence, prominence_frac=PROMINENCE_FRAC, **kw):
    ys, peaks, prom = _peaks_and_prominence(incidence, **kw)
    if len(peaks) == 0:
        return 0
    heights = ys[peaks]
    return int(np.count_nonzero(prom >= prominence_frac*heights))


WAVE_DEFS = {"global (prominence >= 10% of run's tallest peak)": count_waves_global,
             "local (prominence >= 10% of that peak's own height)": count_waves_local}


def part3():
    print("=" * 78)
    print("PART 3 -- T_H sweep wave counts, old (run) vs new (run_gozzi12) scheme")
    print(f"dc={DC}, k={K}, N={N_ABM}, seeds=0..{N_SEEDS_WAVE-1}, days={DAYS_WAVE}")
    print("=" * 78)

    # ODE reference, same dc/k, same wave-counting methods -- sanity check
    # against the register's cited 2,2,3,3 rising-wave-count claim.
    print("\n-- ODE reference (ground truth Weitz model, no ABM stochasticity) --")
    print("   (register D6 cites 2,2,3,3 at T_H=7,14,21,28; check below is against")
    print("    this repo's own ode()/find_peaks pipeline, not a re-derivation of D6's number)")
    ode_counts = {}
    for T_H in T_H_VALUES:
        inc, _ = ode(DC, K, T_H, R0=3.0, days=900)
        row = {name: fn(inc) for name, fn in WAVE_DEFS.items()}
        ode_counts[T_H] = row
        print(f"  T_H={T_H:>3}: " + ", ".join(f"{k}={v}" for k, v in row.items()))

    schemes = {"old (single daily step, raw rate)": run,
               "new (12 sub-steps/day, 1-exp(-rate*dt))": run_gozzi12}

    results = {}
    for scheme_name, run_fn in schemes.items():
        print(f"\n-- ABM, {scheme_name} --")
        results[scheme_name] = {}
        for T_H in T_H_VALUES:
            wave_counts = {name: [] for name in WAVE_DEFS}
            n_valid = 0
            for seed in range(N_SEEDS_WAVE):
                out = run_fn(N=N_ABM, dc=DC, seed=seed, days=DAYS_WAVE,
                             behaviour=True, signal="rolling", window=28,
                             sides=2, T_H=T_H, R0=3.0)
                if out["total_inf"] < FADEOUT_MIN_INF:
                    continue  # fadeout, not a real epidemic -- excluded, counted in denominator below
                n_valid += 1
                for name, fn in WAVE_DEFS.items():
                    wave_counts[name].append(fn(out["inc"]))
            row = {name: np.array(wave_counts[name]) for name in WAVE_DEFS}
            results[scheme_name][T_H] = (row, n_valid)
            means = ", ".join(
                f"{name}: mean={row[name].mean():.2f} (n={n_valid}/{N_SEEDS_WAVE})"
                if n_valid else f"{name}: undefined (n=0/{N_SEEDS_WAVE})"
                for name in WAVE_DEFS
            )
            print(f"  T_H={T_H:>3}: {means}")

    print("\n-- Direction check (does mean wave count rise with T_H, as in the ODE?) --")
    for scheme_name in schemes:
        for name in WAVE_DEFS:
            means = []
            for T_H in T_H_VALUES:
                row, n_valid = results[scheme_name][T_H]
                means.append(row[name].mean() if n_valid else float("nan"))
            nondecreasing = all(b >= a - 1e-9 for a, b in zip(means, means[1:]))
            print(f"  [{scheme_name}] {name}: means at T_H={T_H_VALUES} = "
                  f"{[round(m,2) for m in means]}  "
                  f"non-decreasing={nondecreasing}")

    print("\nRaw per-seed wave counts (for inspection):")
    for scheme_name in schemes:
        print(f"\n  {scheme_name}:")
        for T_H in T_H_VALUES:
            row, n_valid = results[scheme_name][T_H]
            for name in WAVE_DEFS:
                print(f"    T_H={T_H:>3} {name}: {row[name].tolist()}  (n={n_valid}/{N_SEEDS_WAVE})")


if __name__ == "__main__":
    part2()
    part3()
