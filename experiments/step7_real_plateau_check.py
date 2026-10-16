"""
"Real plateau" check (register E26, proposed; results C46). Supervisor point 6. No API calls.

A flattened result counts as behaviour-driven only if ALL hold (thresholds UNSOURCED, proposed):
  (i)   death responsiveness (E24, as implemented in C39) >= 0.3;
  (ii)  the cautious share among deciding agents varies over time: SD over the days with
        end-of-day E + I > 0 >= 0.05;
  (iii) the disease really spread: attack size (1 - S at day 600) >= 0.10.
Per run: an undefined death responsiveness (a series constant on the active days, E24) or an
undefined SD (< 2 active days) fails that criterion. Config verdict: PASS if a majority of runs
(> half) meet all three; config means are reported alongside.

Known cases: should PASS -- Weitz's rule at N = 30,000 (C43 step B, seeds 0-9, rerun with the
caution series logged; incidence checked bit-identical to the stored runs). Should FAIL -- C31
ceiling (everyone never-ill in precautions from day 0; (a) S1 and (c) S2, seeds 0-29, rerun;
final S checked against C31) and C39 rule 2 (S1/S2/S3, from the C39 cache). Information only:
arm 1 (C30, via C39's shared-world rerun) and C39 rules 1, 3, 4, 5; C45's cases if present.

Usage:  python experiments/step7_real_plateau_check.py --sim | --score
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
import step7_cheaper_plateau as cp  # noqa: E402

DR_MIN, SD_MIN, ATTACK_MIN = 0.3, 0.05, 0.10
OUT = cp.OUT
CACHE = os.path.join(OUT, "real_plateau_runs.npz")
C39_CACHE = os.path.join(ROOT, "results", "step5", "arm3_runs.npz")
C43_CACHE = os.path.join(ROOT, "results", "step6", "plateau_size_runs.npz")
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
_POP = {}


def run_ceiling(task):
    sc, seed = task
    from population import build_population
    from shared_world import run_shared_world, ForcedPrecautions, STAY_HOME, PRECAUTIONS
    if "pop" not in _POP:
        _POP["pop"] = build_population(N=3000, seed=0)
    pop = _POP["pop"]
    o = run_shared_world(N=3000, seed=seed, decision=ForcedPrecautions(), days=600,
                         f_D=pop.vulnerability, window=28, detection_rate=0.7, **SCEN[sc])
    rec = {k: np.asarray(o[k], float) for k in ("prevalence", "exposed", "S", "awareness_signal")}
    deciders = o["S"] * 3000 + o["exposed"]
    cautious = (o["S_by_action"][:, STAY_HOME] + o["S_by_action"][:, PRECAUTIONS]
                + o["E_by_action"][:, STAY_HOME] + o["E_by_action"][:, PRECAUTIONS])
    with np.errstate(invalid="ignore", divide="ignore"):
        rec["caution"] = np.where(deciders > 0, cautious / deciders, np.nan)
    return ("ceil", sc, seed), rec


def _c43(task):
    return cp.run_one(task)


def simulate():
    os.makedirs(OUT, exist_ok=True)
    arr = {}
    t0 = time.time()
    with mp.Pool(16) as pool:
        c43 = pool.map_async(_c43, [("B", 30_000, None, cp.DCRIT * 30_000, s) for s in range(10)])
        ceil = pool.map(run_ceiling, [(sc, s) for sc in ("S1", "S2") for s in range(30)])
        c43 = c43.get()
    for (k, sc, s), rec in ceil:
        for key, v in rec.items():
            arr[f"ceil|{sc}|{s}#{key}"] = v
    for task, rec, _ in c43:
        for key, v in rec.items():
            arr[f"c43|{task[4]}#{key}"] = v
    np.savez_compressed(CACHE, **arr)
    print(f"{len(ceil) + len(c43)} simulations {(time.time() - t0) / 60:.1f} min")


def per_run(sig, caution, prev, exp_, S):
    from step5_arm3_runs import death_resp
    active = exp_ + prev
    dr = death_resp(sig, caution, active)
    sd = []
    for c, ac in zip(caution, active):
        m = (ac > 0) & np.isfinite(c)
        sd.append(float(np.std(c[m], ddof=1)) if m.sum() >= 2 else np.nan)
    sd = np.array(sd)
    attack = 1 - S[:, -1]
    ok_i = np.isfinite(dr) & (np.nan_to_num(dr, nan=-9) >= DR_MIN)
    ok_ii = np.isfinite(sd) & (np.nan_to_num(sd, nan=-9) >= SD_MIN)
    ok_iii = attack >= ATTACK_MIN
    allok = ok_i & ok_ii & ok_iii
    n = len(S)
    return dict(n=n, dr_mean=float(np.nanmean(dr)) if np.isfinite(dr).any() else None,
                dr_median=float(np.nanmedian(dr)) if np.isfinite(dr).any() else None,
                dr_defined=int(np.isfinite(dr).sum()),
                sd_mean=float(np.nanmean(sd)) if np.isfinite(sd).any() else None,
                sd_defined=int(np.isfinite(sd).sum()), attack_mean=float(attack.mean()),
                pass_i=int(ok_i.sum()), pass_ii=int(ok_ii.sum()), pass_iii=int(ok_iii.sum()),
                pass_all=int(allok.sum()), verdict="PASS" if allok.sum() > n / 2 else "FAIL")


def score():
    out = {}
    a = dict(np.load(CACHE))
    # --- reproduction checks
    c43 = dict(np.load(C43_CACHE))
    same = [np.array_equal(a[f"c43|{s}#incidence"], c43[f"B|30000|{s}#incidence"]) for s in range(10)]
    print(f"C43 N = 30,000 rerun: incidence bit-identical to stored runs on {sum(same)}/10 seeds")
    for sc, ref in (("S1", 0.40774), ("S2", 0.95254)):
        fs = np.mean([a[f"ceil|{sc}|{s}#S"][-1] for s in range(30)])
        print(f"C31 ceiling {sc}: mean final S {fs:.5f} (C31: {ref})")
    out["checks"] = dict(c43_identical=int(sum(same)))

    def get_new(prefix, seeds):
        g = lambda k: np.array([a[f"{prefix}{s}#{k}"] for s in seeds])  # noqa: E731
        return g("awareness_signal"), g("caution"), g("prevalence"), g("exposed"), g("S")

    cases = [("SHOULD PASS: Weitz rule, N = 30,000 (C43 step B)", get_new("c43|", range(10))),
             ("SHOULD FAIL: C31 ceiling (a) S1, all precautions", get_new("ceil|S1|", range(30))),
             ("SHOULD FAIL: C31 ceiling (c) S2, all precautions", get_new("ceil|S2|", range(30)))]
    c39 = dict(np.load(C39_CACHE))
    g39 = lambda n: tuple(c39[f"{n}#{k}"] for k in ("awareness_signal", "caution", "prevalence",  # noqa: E731
                                                    "exposed", "S"))
    for sc in SCEN:
        cases.append((f"SHOULD FAIL: C39 rule 2, {sc}", g39(f"rule2|{sc}")))
    for sc in SCEN:
        cases.append((f"info: arm 1 (CBF), {sc}", g39(f"arm1|{sc}")))
    for k in (1, 3, 4, 5):
        for sc in SCEN:
            cases.append((f"info: C39 rule {k}, {sc}", g39(f"rule{k}|{sc}")))
    if os.path.exists(cp.CACHE):
        b = dict(np.load(cp.CACHE))
        sc_ = json.load(open(os.path.join(cp.OUT, "cheaper_plateau_scores.json")))

        def g7(kind, n, f):
            gg = lambda k: np.array([b[f"{kind}|{n}|{f}|{s}#{k}"] for s in cp.SEEDS])  # noqa: E731
            return gg("awareness_signal"), gg("caution"), gg("prevalence"), gg("exposed"), gg("S")
        for f in cp.F_D_LIST:
            cases.append((f"info: C45 1a step B, f_D {f}", g7("B", cp.N3K, f)))
        best = sc_["best_f_D"]
        if f"C|{cp.N3K}|{best}|0#incidence" in b:
            cases.append((f"info: C45 1a step C, f_D {best}", g7("C", cp.N3K, best)))
        for n in cp.SIZES_1B:
            cases.append((f"info: C45 1b step B, N = {n:,}", g7("B", n, None)))
    print(f"\nthresholds: (i) DR >= {DR_MIN}; (ii) SD of caution over active days >= {SD_MIN}; "
          f"(iii) attack >= {ATTACK_MIN}. Verdict: PASS if > half of runs meet all three.")
    print("case | n | DR mean / median (n defined) | SD mean (n def) | attack mean | runs passing "
          "(i) / (ii) / (iii) / all | verdict")
    for label, data in cases:
        r = per_run(*data)
        out[label] = r
        f = lambda x: "undef" if x is None else f"{x:+.3f}"  # noqa: E731
        print(f"{label} | {r['n']} | {f(r['dr_mean'])} / {f(r['dr_median'])} ({r['dr_defined']}) | "
              f"{'undef' if r['sd_mean'] is None else format(r['sd_mean'], '.3f')} ({r['sd_defined']}) | "
              f"{r['attack_mean']:.3f} | {r['pass_i']} / {r['pass_ii']} / {r['pass_iii']} / "
              f"{r['pass_all']} | {r['verdict']}")
    json.dump(out, open(os.path.join(OUT, "real_plateau_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    mp.freeze_support()
    if "--sim" in sys.argv:
        simulate()
    if "--score" in sys.argv:
        score()
