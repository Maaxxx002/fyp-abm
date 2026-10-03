"""
Step 1 of the supervisor's "run the original model as-is, then add modifications one at a
time" plan (Decision_Register.md C23): arm 1 as Gozzi's CBF with flat r=0.5, Gozzi's 70%
death reporting and age-based IFR, and ONE measured modification -- the project's 28-day
mean death signal vs Gozzi's literal yesterday's-deaths signal.

Configs (N=3,000 frozen quota population, population seed 0 as in C21/C22; same 30
disease seeds for every config; 48 sub-steps; R0=3, latent 2 d, infectious 6 d, T_H=14;
10 initial infected; days=900 to match C18):

  config1   window=1  (yesterday's deaths), detection 0.7, age-based f_D
  config2   window=28,                      detection 0.7, age-based f_D
  config3   window=28,                      detection 1.0, flat f_D 0.01  (= C18's setup)
  config2T  window=28, detection 0.7 with Gozzi's literal per-age-band integer cast
            (compartment_model_age_deaths.py line 152), age-based f_D -- extra config
            agreed with Max after the cast was found in source
  controlA  no behaviour, age-based f_D  (control for 1, 2, 2T)
  controlB  no behaviour, flat f_D 0.01  (control for 3)

Controls are run_cbf_behaviour with beta_B=0 (S^B never filled -> exactly the
no-behaviour model in distribution) so they consume random numbers in the same pattern as
the behavioural configs: same seed -> same initial infected and common random numbers,
which is what the paired-difference pass mark (a) relies on.

Gozzi's 14-day death delay (Delta) is NOT added: the H compartment (T_H=14) already
provides the infection-to-death delay.

Usage:  python experiments/step1_gozzi_baseline.py --timing   (one seed per config)
        python experiments/step1_gozzi_baseline.py            (full batch)
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from model import run_cbf_behaviour  # noqa: E402
from population import build_population  # noqa: E402
from cbf_real_mechanism_test import ode_final_S, sanity_check_against_test1  # noqa: E402

N = 3_000
POPULATION_SEED = 0
N_SEEDS = 30
DAYS = 900
CHECK_DAYS = (600, 900)
R_FLAT = 0.5          # planning-chat decision: flat r for all agents (response_efficacy = 0.5)
BETA_B, MU_B, GAMMA_BEH = 0.5, 0.01, 1.0
DETECTION = 0.7
FLAT_F_D = 0.01

CONFIGS = {
    "config1":  dict(window=1,  detection_rate=DETECTION, f_D="age", behaviour=True),
    "config2":  dict(window=28, detection_rate=DETECTION, f_D="age", behaviour=True),
    "config3":  dict(window=28, detection_rate=1.0,       f_D="flat", behaviour=True),
    "config2T": dict(window=28, detection_rate=DETECTION, f_D="age", behaviour=True,
                     truncate=True),
    "controlA": dict(window=28, detection_rate=1.0, f_D="age", behaviour=False),
    "controlB": dict(window=28, detection_rate=1.0, f_D="flat", behaviour=False),
}
CONTROL_OF = {"config1": "controlA", "config2": "controlA", "config2T": "controlA",
              "config3": "controlB"}

_POP = None


def _pop():
    global _POP
    if _POP is None:
        _POP = build_population(N=N, seed=POPULATION_SEED)
    return _POP


def _worker(args):
    name, seed = args
    cfg = CONFIGS[name]
    pop = _pop()
    t0 = time.time()
    out = run_cbf_behaviour(
        N=N, seed=seed, response_efficacy=np.full(N, 1.0 - R_FLAT), days=DAYS,
        seeds_infected=10, R0=3.0, latent_period_days=2.0, infectious_period_days=6.0,
        f_D=pop.vulnerability if cfg["f_D"] == "age" else FLAT_F_D, T_H=14.0,
        n_substeps=48, beta_B=BETA_B if cfg["behaviour"] else 0.0, mu_B=MU_B,
        gamma_beh=GAMMA_BEH, window=cfg["window"], detection_rate=cfg["detection_rate"],
        truncate_by_age_band=pop.age_band if cfg.get("truncate") else None,
    )
    active = out["exposed"] + out["prevalence"]
    rec = dict(
        final_S=float(out["S"][-1]),
        peak_I=float(out["prevalence"].max()),
        peak_SB=float(out["SB"].max()),
        peak_daily_deaths=float(out["deaths"].max()),
        total_deaths=float(out["deaths"].sum()),
        total_reported=float(out["reported_deaths"].sum()),
        **{f"infected_at_day{d}": bool(active[d - 1] > 0) for d in CHECK_DAYS},
    )
    return name, seed, rec, time.time() - t0


def mean_sem(x):
    x = np.asarray(x, dtype=float)
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def dde_references(mean_ifr):
    refs = {}
    for name, cfg in CONFIGS.items():
        if not cfg["behaviour"]:
            continue
        f_D = mean_ifr if cfg["f_D"] == "age" else FLAT_F_D
        kw = dict(N=N, beta_B=BETA_B, mu_B=MU_B, r_factor=R_FLAT, gamma_beh=GAMMA_BEH,
                  window=cfg["window"], days=DAYS, f_D=f_D,
                  detection_rate=cfg["detection_rate"])
        refs[name] = dict(continuous=ode_final_S(**kw)[0],
                          daily_held=ode_final_S(signal_update="daily", **kw)[0])
    for ctrl, f_D in (("controlA", mean_ifr), ("controlB", FLAT_F_D)):
        refs[ctrl] = dict(continuous=ode_final_S(N=N, beta_B=0.0, days=DAYS, f_D=f_D)[0])
    return refs


def run_batch(seeds, n_workers):
    tasks = [(name, s) for name in CONFIGS for s in seeds]
    res = {name: {} for name in CONFIGS}
    times = {name: [] for name in CONFIGS}
    t_start = time.time()
    with mp.Pool(n_workers) as pool:
        for i, (name, seed, rec, dt) in enumerate(pool.imap_unordered(_worker, tasks), 1):
            res[name][seed] = rec
            times[name].append(dt)
            print(f"[{i}/{len(tasks)}] {name} seed={seed} final_S={rec['final_S']:.5f} "
                  f"peak_I={rec['peak_I']:.0f} ({dt:.1f}s, elapsed {time.time()-t_start:.0f}s)",
                  flush=True)
    return res, times, time.time() - t_start


def main():
    timing_only = "--timing" in sys.argv
    n_workers = min(os.cpu_count() or 1, 16)

    sanity_check_against_test1()
    pop = _pop()
    mean_ifr = float(pop.vulnerability.mean())
    print(f"Population N={N} seed={POPULATION_SEED}: mean per-agent f_D = {mean_ifr:.6f}")

    if timing_only:
        res, times, wall = run_batch([0], n_workers)
        per_run = {k: v[0] for k, v in times.items()}
        serial = sum(per_run.values()) * N_SEEDS
        print("\nPer-run time (seed 0):")
        for k, v in per_run.items():
            print(f"  {k:9s} {v:6.1f}s")
        print(f"Workers: {n_workers}. Serial total for {N_SEEDS} seeds x {len(CONFIGS)} "
              f"configs: {serial/60:.1f} min; projected wall-clock ~{serial/n_workers/60:.1f} min "
              f"(ignores parallel slowdown; this timing run's own wall time {wall:.0f}s for "
              f"{len(CONFIGS)} parallel runs)")
        return

    refs = dde_references(mean_ifr)
    print("DDE references (final S):")
    for k, v in refs.items():
        print(f"  {k:9s} " + ", ".join(f"{m}={x:.5f}" for m, x in v.items()))

    seeds = list(range(N_SEEDS))
    res, times, wall = run_batch(seeds, n_workers)
    print(f"\nBatch wall time: {wall/60:.1f} min")

    # C18's per-seed final S at N=3,000 (flat r=0.5, seeds 0-29) from C19's stored output.
    c19 = json.load(open(os.path.join(HERE, "..", "results",
                                      "cbf_real_mechanism_seed_check.json")))
    c18_S = np.array(c19["results"]["3000"]["finals_S"][:N_SEEDS])

    summary = {"N": N, "days": DAYS, "n_seeds": N_SEEDS, "population_seed": POPULATION_SEED,
               "mean_ifr": mean_ifr, "dde": refs, "configs": {}}
    print("\n=== SUMMARY (n = seeds the statistic is defined on) ===")
    for name in CONFIGS:
        recs = [res[name][s] for s in seeds]
        block = {"per_seed": recs}
        print(f"\n--- {name}: {CONFIGS[name]}")
        for key in ("final_S", "peak_I", "peak_SB", "peak_daily_deaths", "total_deaths"):
            if key == "peak_SB" and not CONFIGS[name]["behaviour"]:
                continue
            m, se, n = mean_sem([r[key] for r in recs])
            block[key] = dict(mean=m, sem=se, n=n)
            print(f"  {key:18s} {m:10.5f} +/- {se:.5f}  (n={n})")
        for d in CHECK_DAYS:
            k = sum(r[f"infected_at_day{d}"] for r in recs)
            block[f"n_infected_at_day{d}"] = k
            print(f"  runs with E or I agents at day {d}: {k}/{len(recs)}")
        if CONFIGS[name]["detection_rate"] != 1.0:
            tot_d = sum(r["total_deaths"] for r in recs)
            tot_r = sum(r["total_reported"] for r in recs)
            block["reported_over_realised"] = tot_r / tot_d
            print(f"  total reported / total realised deaths (pooled over {len(recs)} runs): "
                  f"{tot_r/tot_d:.4f}")

        if name in CONTROL_OF:
            ctrl = CONTROL_OF[name]
            crecs = [res[ctrl][s] for s in seeds]
            pa = {}
            for key, want in (("peak_I", -1), ("final_S", +1)):
                diff = np.array([r[key] for r in recs]) - np.array([c[key] for c in crecs])
                m, se, n = mean_sem(diff)
                z = m / se if se > 0 else float("inf") * np.sign(m)
                ok = (np.sign(m) == want) and abs(z) > 2
                pa[key] = dict(mean_diff=m, sem_diff=se, n=n, sems=z, passes=bool(ok))
                print(f"  (a) {key} - {ctrl}: {m:+.5f} +/- {se:.5f} = {z:+.2f} SEM (n={n}) "
                      f"-> {'PASS' if ok else 'FAIL'}")
            pa["passes"] = all(v["passes"] for v in pa.values())
            block["pass_a"] = pa

            ref = refs[name]["continuous"]
            m, se, n = block["final_S"]["mean"], block["final_S"]["sem"], block["final_S"]["n"]
            rel = abs(m - ref) / ref
            gap = (m - ref) / se
            ok = rel <= 0.06
            block["pass_b"] = dict(dde=ref, relative_error=rel, gap_sems=gap, n=n,
                                   passes=bool(ok),
                                   like_for_like=not CONFIGS[name].get("truncate", False))
            note = ("" if not CONFIGS[name].get("truncate") else
                    "  [NOT like-for-like: DDE uses plain 0.7x, ABM uses per-band floor]")
            print(f"  (b) final S vs DDE {ref:.5f}: rel err {rel*100:.2f}%, gap {gap:+.2f} SEM "
                  f"(n={n}) -> {'PASS' if ok else 'FAIL'}{note}")
            dh = refs[name]["daily_held"]
            print(f"      diagnostic: daily-held-signal DDE {dh:.5f}: rel err "
                  f"{abs(m-dh)/dh*100:.2f}%, gap {(m-dh)/se:+.2f} SEM")
            block["diag_daily_held"] = dict(dde=dh, relative_error=abs(m - dh) / dh,
                                            gap_sems=(m - dh) / se)
        else:
            ref = refs[name]["continuous"]
            m, se = block["final_S"]["mean"], block["final_S"]["sem"]
            print(f"  no-behaviour ODE final S {ref:.5f}: rel err {abs(m-ref)/ref*100:.2f}%, "
                  f"gap {(m-ref)/se:+.2f} SEM")

        if name == "config3":
            s3 = np.array([r["final_S"] for r in recs])
            n_same = int(np.sum(s3 == c18_S))
            d_m, d_se, n = mean_sem(s3 - c18_S)
            block["vs_c18"] = dict(c18_mean=float(c18_S.mean()), n_bit_identical=n_same,
                                   mean_diff=d_m, sem_diff=d_se, n=n)
            print(f"  vs C18 (same seeds): C18 mean {c18_S.mean():.5f}, this {s3.mean():.5f}; "
                  f"bit-identical on {n_same}/{n} seeds; paired diff {d_m:+.6f} +/- {d_se:.6f}")
        summary["configs"][name] = block

    print("\n--- config2 vs config3 (effect of 70% reporting + age-based f_D, same seeds)")
    summary["config2_minus_config3"] = {}
    for key in ("final_S", "peak_I"):
        diff = (np.array([res["config2"][s][key] for s in seeds])
                - np.array([res["config3"][s][key] for s in seeds]))
        m, se, n = mean_sem(diff)
        summary["config2_minus_config3"][key] = dict(mean_diff=m, sem_diff=se, n=n)
        print(f"  {key}: {m:+.5f} +/- {se:.5f} = {m/se:+.2f} SEM (n={n})")

    out = os.path.join(HERE, "..", "results", "step1_gozzi_baseline.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
