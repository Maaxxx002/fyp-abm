"""
Arm 3 side tests (register C41), S1 only, rules 1-5, seeds 0-29. No API calls.

  T1  re-decide rate p = 0.1 and p = 1.0 (C39 used p = 0.3; E2)
  T2  variant A-physical (E21): currently-ill agents keep deciding with the same rule;
      staying home stops an ill agent spreading (run_shared_world(ill_decide=True))
  T3  no stay-home option: P(stay_home) added to P(precautions) (Arm3Rule merge_stay_home)

Everything else as C39 (A55 stop, Perception, sampling). Control: C39's S1 AlwaysNormal runs
(no decisions, so identical for every test; read from results/step5/arm3_runs.npz). Baseline:
C39 S1 (p = 0.3) from the same file.

Usage:  python experiments/step5_arm3_side.py --timing | --sim | --score
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
import step5_arm3_runs as base  # noqa: E402

N, DAYS, SEEDS, RULES = base.N, base.DAYS, base.SEEDS, base.RULES
OUT = base.OUT
CACHE = os.path.join(OUT, "arm3_side_runs.npz")
TESTS = {"T1_p0.1": dict(p=0.1), "T1_p1.0": dict(p=1.0),
         "T2_ill": dict(p=0.3, ill=True), "T3_nohome": dict(p=0.3, merge=True)}
KEEP = base.KEEP
_POP = {}


def run_one(task):
    test, k, seed = task
    from population import build_population
    from shared_world import run_shared_world, PRECAUTIONS, STAY_HOME
    from arm3 import Arm3Rule
    if "pop" not in _POP:
        _POP["pop"] = build_population(N=N, seed=0)
    pop, cfg = _POP["pop"], TESTS[test]
    t0 = time.time()
    o = run_shared_world(N=N, seed=seed, days=DAYS, f_D=pop.vulnerability, window=28,
                         detection_rate=0.7, **base.SCEN["S1"],
                         decision=Arm3Rule(k, pop, merge_stay_home=cfg.get("merge", False)),
                         redecide_prob=cfg["p"], stop_deciding_when_no_infection=True,
                         ill_decide=cfg.get("ill", False))
    rec = {key: np.asarray(o[key], float) for key in KEEP}
    deciders = o["S"] * N + o["exposed"]                  # E24: never-ill and alive (S or E)
    cautious = (o["S_by_action"][:, PRECAUTIONS] + o["S_by_action"][:, STAY_HOME]
                + o["E_by_action"][:, PRECAUTIONS] + o["E_by_action"][:, STAY_HOME])
    with np.errstate(invalid="ignore", divide="ignore"):
        rec["caution"] = np.where(deciders > 0, cautious / deciders, np.nan)
    return f"{test}_rule{k}|S1", seed, rec, time.time() - t0


def timing():
    tasks = [(t, k, s) for t in TESTS for k in RULES for s in (0, 1)]
    t0 = time.time()
    with mp.Pool(16) as pool:
        out = pool.map(run_one, tasks)
    wall = time.time() - t0
    per = {}
    for (t, k, s), (_, _, _, dt) in zip(tasks, out):
        per.setdefault(t, []).append(dt)
    print(f"{len(tasks)} timing runs: wall {wall:.1f}s = {wall / len(tasks):.2f}s/run effective")
    for t, v in per.items():
        print(f"  {t:10s} per run {min(v):.1f}-{max(v):.1f}s, mean {np.mean(v):.1f}s")


def simulate():
    tasks = [(t, k, s) for t in TESTS for k in RULES for s in SEEDS]
    t0 = time.time()
    res, times = {}, []
    with mp.Pool(16) as pool:
        for name, seed, rec, dt in pool.imap_unordered(run_one, tasks, chunksize=2):
            res[(name, seed)] = rec
            times.append(dt)
    t_sim = time.time() - t0
    print(f"{len(tasks)} simulations in {t_sim / 60:.1f} min (per run {min(times):.1f}-"
          f"{max(times):.1f}s)", flush=True)
    names = sorted({n for n, _ in res})
    t0 = time.time()
    keys = [(n, s) for n in names for s in SEEDS]
    with mp.Pool(16) as pool:
        m1 = pool.map(base.waves, [res[x]["incidence"] for x in keys], chunksize=2)
    t_kabu = time.time() - t0
    print(f"{len(keys)} wave counts in {t_kabu / 60:.1f} min; total {(t_sim + t_kabu) / 60:.1f} min")
    arrays = {}
    m1d = dict(zip(keys, m1))
    for n in names:
        for key in KEEP + ("caution",):
            arrays[f"{n}#{key}"] = np.array([res[(n, s)][key] for s in SEEDS])
        arrays[f"{n}#m1"] = np.array([m1d[(n, s)] for s in SEEDS])
    c39 = dict(np.load(base.CACHE))                      # control and C39 baseline, S1
    for key in list(c39):
        if key.startswith("ctrl|S1#") or any(key.startswith(f"rule{k}|S1#") for k in RULES):
            arrays[key] = c39[key]
    np.savez_compressed(CACHE, **arrays)


def stats(a, n, boot_idx):
    import step3_shape_metrics as sm
    inc, prev, exp_ = a[f"{n}#incidence"], a[f"{n}#prevalence"], a[f"{n}#exposed"]
    incc, prevc, Sc = a["ctrl|S1#incidence"], a["ctrl|S1#prevalence"], a["ctrl|S1#S"]
    m3 = np.array([sm.duration(y) for y in inc])
    m3c = np.array([sm.duration(y) for y in incc])
    ok = np.isfinite(m3) & np.isfinite(m3c)
    ratio = m3 / m3c
    bt = [m3[idx[ok[idx]]].mean() / m3c[idx[ok[idx]]].mean() if ok[idx].any() else np.nan
          for idx in boot_idx]
    pI, pIc = prev.max(1), prevc.max(1)
    fS = a[f"{n}#S"][:, -1]
    dI, dS = base.mean_sem(pI - pIc), base.mean_sem(fS - Sc[:, -1])
    dr = base.death_resp(a[f"{n}#awareness_signal"], a[f"{n}#caution"], exp_ + prev)
    am, nu = base.aligned_m3(inc)
    amc, _ = base.aligned_m3(incc)
    w, wc = a[f"{n}#m1"], a["ctrl|S1#m1"]
    return dict(
        stretch=float(m3[ok].mean() / m3c[ok].mean()), stretch_ci=tuple(np.nanpercentile(bt, [2.5, 97.5])),
        median=float(np.median(ratio[ok])), gt15=f"{int((ratio[ok] > 1.5).sum())}/{int(ok.sum())}",
        aligned_stretch=float(am / amc), aligned_n=nu,
        peak_red=float(-dI[0] / pIc.mean() * 100), peak_sems=dI[0] / dI[1],
        final_S=float(fS.mean()), final_S_paired=dS, attack=float(1 - fS.mean()),
        m1=float(w.mean()), m1_multi=f"{int((w > 1).sum())}/30", m1_ctrl=float(wc.mean()),
        dr_mean=float(np.nanmean(dr)) if np.isfinite(dr).any() else np.nan,
        dr_median=float(np.nanmedian(dr)) if np.isfinite(dr).any() else np.nan,
        dr_n=int(np.isfinite(dr).sum()),
        finished=int(sum((exp_ + prev)[:, DAYS - 1] == 0)))


def score():
    a = dict(np.load(CACHE))
    rng = np.random.default_rng(base.BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(base.N_BOOT, len(SEEDS)))
    R = {}
    print("test | rule | stretch [95% CI] | median | >x1.5 | aligned stretch (n) | peak red % (SEM) | "
          "final S (paired) | attack | M1; >1 wave | DR mean / median (n) | fin600")
    for k in RULES:
        rows = [("C39 p=0.3", f"rule{k}|S1")] + [(t, f"{t}_rule{k}|S1") for t in TESTS]
        for label, n in rows:
            r = stats(a, n, boot_idx)
            R[f"{label}|rule{k}"] = r
            print(f"  {label:10s} | {k} | x{r['stretch']:.3f} [{r['stretch_ci'][0]:.3f}, "
                  f"{r['stretch_ci'][1]:.3f}] | x{r['median']:.3f} | {r['gt15']} | x{r['aligned_stretch']:.3f}"
                  f" ({r['aligned_n']}) | {r['peak_red']:.1f} ({r['peak_sems']:+.1f}) | {r['final_S']:.4f} "
                  f"({r['final_S_paired'][0]:+.4f}) | {r['attack']:.4f} | {r['m1']:.2f}; {r['m1_multi']} | "
                  f"{r['dr_mean']:+.3f} / {r['dr_median']:+.3f} ({r['dr_n']}) | {r['finished']}/30")
        print()
    print(f"control M1 {R['C39 p=0.3|rule1']['m1_ctrl']:.2f}")
    json.dump(R, open(os.path.join(OUT, "arm3_side_scores.json"), "w"), indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


if __name__ == "__main__":
    mp.freeze_support()
    if "--timing" in sys.argv:
        timing()
    if "--sim" in sys.argv:
        simulate()
    if "--score" in sys.argv:
        score()
