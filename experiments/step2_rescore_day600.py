"""
Register C28: (1) re-score pass mark (b) under the revised rule A31, and (2) the day-600 check
at N=3,000 behind A32 (production run length 600 days).

(1) Existing 30-/90-seed results are reused (results/*.json). The only config the revised rule
    needs a new 90-seed run for is C23's config 2T (literal per-age-band truncation, >6% at 30
    seeds, no 90-seed result yet): seeds 30-89 are run here with step1_gozzi_baseline's own
    worker, and seeds 0-29 are checked bit-identical to C23.
(2) Re-runs (same seeds 0-29, days=900) every distinct N=3,000 config of C26 (control +
    gamma_beh 0.25..4) and C27 (S1/S2/S3 with behaviour + control; S1 = C26's gamma_beh=1
    point and S1's control = C26's control, so they are not run twice). Final S and peak I are
    checked bit-identical to the stored C26/C27 runs. Reports runs with E+I > 0 at day 600 and
    the latest day E+I > 0.

Usage:  python experiments/step2_rescore_day600.py [--timing]
"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step2_common as c  # noqa: E402
import step1_gozzi_baseline as s1  # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
SEEDS = list(range(30))
N = 3_000
DAY600_CONFIGS = {
    "ctrl": dict(c.FOUNDATION, N=N, behaviour=False),
    **{f"g{g}": dict(c.FOUNDATION, N=N, gamma_beh=g) for g in (0.25, 0.5, 1.0, 2.0, 4.0)},
    "S2": dict(c.FOUNDATION, N=N, R0=2.0, T_H=14.0),
    "S2_ctrl": dict(c.FOUNDATION, N=N, R0=2.0, T_H=14.0, behaviour=False),
    "S3": dict(c.FOUNDATION, N=N, R0=3.0, T_H=28.0),
    "S3_ctrl": dict(c.FOUNDATION, N=N, R0=3.0, T_H=28.0, behaviour=False),
}
STORED_NAME = {"ctrl": ("grad", "N3000_ctrl"), "S2": ("scen", "N3000_S2"),
               "S2_ctrl": ("scen", "N3000_S2_ctrl"), "S3": ("scen", "N3000_S3"),
               "S3_ctrl": ("scen", "N3000_S3_ctrl"),
               **{f"g{g}": ("grad", f"N3000_g{g}") for g in (0.25, 0.5, 1.0, 2.0, 4.0)}}
LABEL = {"ctrl": "C26 control = C27 S1 control", "g1.0": "C26 gamma 1 = C27 S1"}


def _worker_2t(seed):
    return s1._worker(("config2T", seed))


def main():
    if "--timing" in sys.argv:
        res, times, _ = c.run_pool([(k, v, 0) for k, v in DAY600_CONFIGS.items()])
        for k, v in times.items():
            print(f"  {k:8s} seed 0: {v[0]:.1f}s")
        return

    # ---------------- (1) config 2T at 90 seeds
    c23 = json.load(open(os.path.join(RESULTS, "step1_gozzi_baseline.json")))
    ref2t = c23["dde"]["config2T"]["continuous"]
    with mp.Pool(16) as pool:
        out = pool.map(_worker_2t, range(90))
    s2t = np.array([rec["final_S"] for _, _, rec, _ in out])
    same = sum(s2t[k] == c23["configs"]["config2T"]["per_seed"][k]["final_S"] for k in range(30))
    pb30 = c.pass_b(s2t[:30], ref2t)
    pb90 = c.pass_b(s2t, ref2t)
    print("=== (1) C23 config 2T, seeds 0-89 (seeds 0-29 bit-identical to C23: "
          f"{same}/30) ===")
    c.print_pass_b("2T n=30", pb30)
    c.print_pass_b("2T n=90", pb90)

    # ---------------- (2) day-600 check
    grad = json.load(open(os.path.join(RESULTS, "step2_gradation.json")))["per_seed"]
    scen = json.load(open(os.path.join(RESULTS, "step2_scenarios.json")))["per_seed"]
    stored = {"grad": grad, "scen": scen}
    res, _, wall = c.run_pool([(k, v, s) for k, v in DAY600_CONFIGS.items() for s in SEEDS])
    print(f"\n=== (2) Day-600 check, N=3,000, seeds 0-29, days=900 [{wall/60:.1f} min] ===")
    day600 = {}
    for k in DAY600_CONFIGS:
        src, name = STORED_NAME[k]
        ident = sum(res[k][s]["final_S"] == stored[src][name][str(s)]["final_S"]
                    and res[k][s]["peak_I"] == stored[src][name][str(s)]["peak_I"]
                    for s in SEEDS)
        n600 = sum(res[k][s]["active_at_day600"] for s in SEEDS)
        last = [res[k][s]["last_active_day"] for s in SEEDS]
        day600[k] = dict(n_active_at_day600=n600, n=len(SEEDS), latest_active_day=max(last),
                         median_last_active_day=float(np.median(last)),
                         bit_identical_to_stored=ident)
        print(f"  {k:8s} {LABEL.get(k, ''):32s} E+I>0 at day 600: {n600}/{len(SEEDS)}; latest "
              f"day E+I>0: {max(last)} (median {np.median(last):.0f}); bit-identical to "
              f"stored C26/C27: {ident}/{len(SEEDS)}")

    json.dump(dict(config2T=dict(pass_b_30=pb30, pass_b_90=pb90, bit_identical_0_29=int(same),
                                 per_seed_final_S=s2t.tolist()),
                   day600=day600, per_seed=res),
              open(os.path.join(RESULTS, "step2_rescore_day600.json"), "w"), indent=2,
              default=str)
    print("\nWrote results/step2_rescore_day600.json")


if __name__ == "__main__":
    mp.freeze_support()
    main()
