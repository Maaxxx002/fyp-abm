"""
Step 2, modification A (register C24): per-agent r vs flat r, on the C23-config-2 foundation.

  F   foundation, flat r = 0.5
  PR  foundation, per-agent r_i = cbf_r_from_response_efficacy(response_efficacy_i) (C21/C22),
      response_efficacy from the same frozen population
  A   no-behaviour control (C23's Control A: beta_B=0, per-agent f_D). Seeds 0-29 are checked
      against C23's stored values for bit-identity.

90 seeds (0-89), the same for every config. Pass mark (b) is NOT applied to PR: the DDE
assumes one shared r (C22). F's (b) is reported for continuity only.

Usage:  python experiments/step2_personal_r.py --timing | (no flag for the full run)
"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step2_common as c  # noqa: E402
from cbf_real_mechanism_test import ode_final_S  # noqa: E402

N_SEEDS = 90
CONFIGS = {
    "F":  dict(c.FOUNDATION),
    "PR": dict(c.FOUNDATION, r="personal"),
    "A":  dict(c.FOUNDATION, behaviour=False),
}


def main():
    if "--timing" in sys.argv:
        res, times, wall = c.run_pool([(k, v, 0) for k, v in CONFIGS.items()])
        for k, v in times.items():
            print(f"  {k:3s} seed 0: {v[0]:.1f}s")
        print(f"  serial total {sum(t[0] for t in times.values()) * N_SEEDS / 60:.1f} min")
        return

    seeds = list(range(N_SEEDS))
    res, _, wall = c.run_pool([(k, v, s) for k, v in CONFIGS.items() for s in seeds])
    print(f"Wall time {wall/60:.1f} min. N={c.FOUNDATION['N']}, seeds 0-{N_SEEDS-1}.")
    re = c.population(c.FOUNDATION["N"]).response_efficacy
    print(f"Population response_efficacy mean {re.mean():.4f} -> mean r_i {1-re.mean():.4f}")

    # Control A reuse check vs C23 (seeds 0-29)
    c23 = json.load(open(os.path.join(HERE, "..", "results", "step1_gozzi_baseline.json")))
    c23A = c23["configs"]["controlA"]["per_seed"]
    c23F = c23["configs"]["config2"]["per_seed"]
    same_A = sum(res["A"][s]["final_S"] == c23A[s]["final_S"]
                 and res["A"][s]["peak_I"] == c23A[s]["peak_I"] for s in range(30))
    same_F = sum(res["F"][s]["final_S"] == c23F[s]["final_S"]
                 and res["F"][s]["peak_I"] == c23F[s]["peak_I"] for s in range(30))
    print(f"Bit-identical to C23 on seeds 0-29: control A {same_A}/30, F (=config 2) {same_F}/30")

    print("\n--- Per-config statistics")
    for name in CONFIGS:
        c.print_stats(res, name, seeds, behaviour=CONFIGS[name]["behaviour"])

    print("\n--- PRIMARY: paired difference PR - F (same seed)")
    primary = {}
    for key in ("final_S", "peak_I", "peak_SB", "peak_daily_deaths"):
        primary[key] = c.paired(res, "PR", "F", key, seeds)
        print(f"  {key:18s} {c.fmt_paired(primary[key])}")
    detectable = any(abs(primary[k]["sems"]) > 2 for k in ("final_S", "peak_I"))
    print(f"  detectable change (|diff| > 2 SEM in final S or peak I): {detectable}")

    print("\n--- Pass mark (a)")
    pa = {k: c.pass_a(res, k, "A", seeds) for k in ("PR", "F")}
    for k in pa:
        c.print_pass_a(f"{k} vs A", pa[k])

    print("\n--- Pass mark (b): F only, for continuity (not applied to PR)")
    ref = ode_final_S(N=c.FOUNDATION["N"], r_factor=c.R_FLAT, window=c.WINDOW, days=900,
                      f_D=float(c.population(c.FOUNDATION["N"]).vulnerability.mean()),
                      detection_rate=c.DETECTION)[0]
    pb = {n: c.pass_b(c.values(res, "F", "final_S", seeds[:n]), ref) for n in (30, 90)}
    for n in pb:
        c.print_pass_b(f"F, first {n} seeds", pb[n])

    out = dict(seeds=seeds, per_seed=res, primary_PR_minus_F=primary, detectable=detectable,
               pass_a=pa, pass_b_F=pb, bit_identical_to_c23=dict(A=same_A, F=same_F))
    path = os.path.join(HERE, "..", "results", "step2_personal_r.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
