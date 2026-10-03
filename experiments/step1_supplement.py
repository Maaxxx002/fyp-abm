"""
SUPPLEMENTARY diagnostic for register C23 -- not part of the pre-registered step-1 run.

step1_gozzi_baseline.py's 30-seed config2 missed pass mark (b) at 13.1% relative error but
only +1.93 SEM, and one SEM there is ~6.8% of the reference -- larger than the 6% band
itself. This script (1) extends config1/config2/config3 to 90 seeds (seeds 0-29 identical to
the main run) and (2) splits config2's two changes from config3 (detection 0.7, age-based
f_D) into one-at-a-time configs, each against its own DDE reference.
"""
import json
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step1_gozzi_baseline as base  # noqa: E402
from cbf_real_mechanism_test import ode_final_S  # noqa: E402

N_SEEDS = 90
base.CONFIGS.update({
    "det07_flat": dict(window=28, detection_rate=0.7, f_D="flat", behaviour=True),
    "det10_age":  dict(window=28, detection_rate=1.0, f_D="age", behaviour=True),
})
RUN = ["config1", "config2", "config3", "det07_flat", "det10_age"]


def main():
    mean_ifr = float(base._pop().vulnerability.mean())
    tasks = [(name, s) for name in RUN for s in range(N_SEEDS)]
    res = {name: {} for name in RUN}
    with mp.Pool(min(os.cpu_count() or 1, 16)) as pool:
        for name, seed, rec, _ in pool.imap_unordered(base._worker, tasks):
            res[name][seed] = rec
    out = {}
    print(f"=== SUPPLEMENT: N={base.N}, flat r=0.5, days={base.DAYS} ===")
    for name in RUN:
        cfg = base.CONFIGS[name]
        f_D = mean_ifr if cfg["f_D"] == "age" else base.FLAT_F_D
        ref = ode_final_S(N=base.N, r_factor=base.R_FLAT, window=cfg["window"],
                          days=base.DAYS, f_D=f_D, detection_rate=cfg["detection_rate"])[0]
        out[name] = {"dde": ref}
        for n in (30, 90):
            s = np.array([res[name][k]["final_S"] for k in range(n)])
            m, se = s.mean(), s.std(ddof=1) / np.sqrt(n)
            rel, gap = abs(m - ref) / ref, (m - ref) / se
            out[name][n] = dict(mean=m, sem=se, relative_error=rel, gap_sems=gap)
            print(f"{name:10s} {str(cfg):80s} n={n}: mean final S {m:.5f} +/- {se:.5f}, "
                  f"DDE {ref:.5f}, rel err {rel*100:5.2f}%, gap {gap:+.2f} SEM")
    with open(os.path.join(HERE, "..", "results", "step1_supplement.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)


if __name__ == "__main__":
    mp.freeze_support()
    main()
