"""
Step 2, modification B (register C25): Gozzi disease parameters vs Weitz, on the foundation.

Gozzi disease set (constants.py: mu = 1/2.5 -> infectious_period_days=2.5; eps = 1/4 ->
latent_period_days=4; example.ipynb R0=2.5). Transmission rate R0/infectious = 1.0/day.
T_H, IFR, detection and behaviour parameters unchanged from the foundation.

3a  Convergence check FIRST: behaviour off, N=100,000, 30 seeds, Gozzi disease set.
    Target = analytical final size s = exp(-2.5(1-s)) = 0.10736; DDE with beta_B=0 must
    reproduce it too. Pass = ABM relative error < 1%. On failure the script STOPS before 3b.
3b  N=3,000, seeds 0-29 (= step2_personal_r.py's first 30):
      G   foundation with Gozzi disease set;    CG  no-behaviour control, Gozzi disease set
      F   foundation (Weitz);                    A   its no-behaviour control
    Pass (a) G vs CG; pass (b) G vs the Gozzi-parameterised DDE under the A27 rule, with an
    automatic 90-seed re-run of G if INCONCLUSIVE.

Usage:  python experiments/step2_gozzi_disease.py --timing | (no flag for the full run)
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

FINAL_SIZE_TARGET = 0.10736
CONV_TOL = 0.01
CONV = dict(c.FOUNDATION, N=100_000, behaviour=False, disease="gozzi")
CONFIGS = {
    "G":  dict(c.FOUNDATION, disease="gozzi"),
    "CG": dict(c.FOUNDATION, disease="gozzi", behaviour=False),
    "F":  dict(c.FOUNDATION),
    "A":  dict(c.FOUNDATION, behaviour=False),
}


def dde(cfg, beta_B=c.BETA_B):
    N = cfg["N"]
    return ode_final_S(N=N, beta_B=beta_B, r_factor=c.R_FLAT, window=c.WINDOW, days=cfg["days"],
                       f_D=float(c.population(N).vulnerability.mean()),
                       detection_rate=c.DETECTION, **c.disease_params(cfg["disease"]))[0]


def main():
    if "--timing" in sys.argv:
        tasks = [("CONV", CONV, 0)] + [(k, v, 0) for k, v in CONFIGS.items()]
        res, times, wall = c.run_pool(tasks)
        for k, v in times.items():
            print(f"  {k:4s} seed 0: {v[0]:.1f}s")
        print(f"  3a serial {times['CONV'][0] * 30 / 60:.1f} min; 3b serial "
              f"{sum(times[k][0] for k in CONFIGS) * 30 / 60:.1f} min (+ G x60 if inconclusive)")
        return

    out = {}
    # ---------------- 3a
    print("=== 3a: convergence check, Gozzi disease set, behaviour off, N=100,000 ===")
    dde_conv = dde(CONV, beta_B=0.0)
    dde_rel = abs(dde_conv - FINAL_SIZE_TARGET) / FINAL_SIZE_TARGET
    print(f"  DDE (beta_B=0): {dde_conv:.5f} vs target {FINAL_SIZE_TARGET:.5f} "
          f"(rel err {dde_rel*100:.4f}%)")
    seeds30 = list(range(30))
    res_conv, _, wall = c.run_pool([("CONV", CONV, s) for s in seeds30])
    m, se, n = c.mean_sem(c.values(res_conv, "CONV", "final_S", seeds30))
    rel = abs(m - FINAL_SIZE_TARGET) / FINAL_SIZE_TARGET
    ok = rel < CONV_TOL and dde_rel < CONV_TOL
    print(f"  ABM mean final S {m:.5f} +/- {se:.5f} (n={n}) vs {FINAL_SIZE_TARGET}: rel err "
          f"{rel*100:.3f}%, gap {(m-FINAL_SIZE_TARGET)/se:+.2f} SEM -> {'PASS' if ok else 'FAIL'}"
          f"  [{wall/60:.1f} min]")
    out["3a"] = dict(dde=dde_conv, dde_relative_error=dde_rel, mean=m, sem=se, n=n,
                     relative_error=rel, passes=bool(ok),
                     per_seed=[res_conv["CONV"][s]["final_S"] for s in seeds30])
    path = os.path.join(HERE, "..", "results", "step2_gozzi_disease.json")
    if not ok:
        print("STOP: 3a failed -- 3b not run.")
        json.dump(out, open(path, "w"), indent=2)
        return

    # ---------------- 3b
    print("\n=== 3b: N=3,000, seeds 0-29 ===")
    res, _, wall = c.run_pool([(k, v, s) for k, v in CONFIGS.items() for s in seeds30])
    for name in CONFIGS:
        c.print_stats(res, name, seeds30, behaviour=CONFIGS[name]["behaviour"])

    pa = {"G": c.pass_a(res, "G", "CG", seeds30), "F": c.pass_a(res, "F", "A", seeds30)}
    print()
    c.print_pass_a("G vs CG", pa["G"])
    c.print_pass_a("F vs A (foundation, for comparison)", pa["F"])

    refs = {"G": dde(CONFIGS["G"]), "F": dde(CONFIGS["F"])}
    pb = {"G_30": c.pass_b(c.values(res, "G", "final_S", seeds30), refs["G"])}
    c.print_pass_b("G, n=30", pb["G_30"])
    if pb["G_30"]["verdict"] == "INCONCLUSIVE":
        seeds90 = list(range(90))
        extra, _, _ = c.run_pool([("G", CONFIGS["G"], s) for s in range(30, 90)])
        res["G"].update(extra["G"])
        pb["G_90"] = c.pass_b(c.values(res, "G", "final_S", seeds90), refs["G"])
        c.print_pass_b("G, n=90 (re-run per A27)", pb["G_90"])
    pb["F_30"] = c.pass_b(c.values(res, "F", "final_S", seeds30), refs["F"])
    c.print_pass_b("F, n=30 (foundation, for comparison)", pb["F_30"])

    print("\n--- Side by side (seeds 0-29, n=30)")
    side = {}
    print(f"  {'':22s} {'Weitz F':>22s} {'Weitz ctrl A':>22s} {'Gozzi G':>22s} {'Gozzi ctrl CG':>22s}")
    for key in ("final_S", "peak_I", "peak_SB", "peak_daily_deaths"):
        row = []
        for name in ("F", "A", "G", "CG"):
            if key == "peak_SB" and not CONFIGS[name]["behaviour"]:
                row.append("—")
                continue
            mm, ss, _ = c.mean_sem(c.values(res, name, key, seeds30))
            side[f"{name}_{key}"] = dict(mean=mm, sem=ss, n=30)
            row.append(f"{mm:.4f} +/- {ss:.4f}")
        print(f"  {key:22s} " + " ".join(f"{x:>22s}" for x in row))
    for key in ("final_S", "peak_I"):
        print(f"  effect on {key:9s} (paired vs own control): Weitz {c.fmt_paired(pa['F'][key])};"
              f" Gozzi {c.fmt_paired(pa['G'][key])}")

    out.update(dict(per_seed=res, pass_a=pa, pass_b=pb, dde=refs, side_by_side=side))
    json.dump(out, open(path, "w"), indent=2, default=str)
    print(f"\nWrote {path}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
