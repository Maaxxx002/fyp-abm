"""
Arm 3, step 2: epidemic runs of the 5 frozen rules (register C39). No API calls.

  arm 3:  rules 1-5 x S1/S2/S3 x seeds 0-29, shared world, p = 0.3/day (A41), A55 stop
  control: AlwaysNormal, same world mode, S1/S2/S3 x seeds 0-29 (shared by the 5 rules)
  arm 1:  CBFArm1 in the shared world (bit-identical to run_cbf_behaviour, C31), S1/S2/S3 x 30,
          for death responsiveness; final S and peak I checked against the stored C27 runs
  supplementary: S1 x rules 1-5 x 30 with social_norm_def="alive_not_home_not_H"

Metrics as C30 (step3_score_arm1.py); death responsiveness as E24 (filled in C39).

Usage:  python experiments/step5_arm3_runs.py --sim     (simulations + wave counts, cached)
        python experiments/step5_arm3_runs.py --score
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

N, DAYS, SEEDS, P_REASK = 3000, 600, list(range(30)), 0.3
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
RULES = [1, 2, 3, 4, 5]
OUT = os.path.join(ROOT, "results", "step5")
CACHE = os.path.join(OUT, "arm3_runs.npz")
N_BOOT, BOOT_SEED = 1000, 20261005
KEEP = ("incidence", "prevalence", "exposed", "S", "awareness_signal")
_POP = {}


def configs():
    c = {}
    for sc in SCEN:
        c[f"ctrl|{sc}"] = ("ctrl", sc, None, "cbf")
        c[f"arm1|{sc}"] = ("arm1", sc, None, "cbf")
        for k in RULES:
            c[f"rule{k}|{sc}"] = ("rule", sc, k, "cbf")
    for k in RULES:
        c[f"supp_rule{k}|S1"] = ("rule", "S1", k, "alive_not_home_not_H")
    return c


def run_one(task):
    name, (kind, sc, k, norm), seed = task
    from population import build_population
    from shared_world import run_shared_world, AlwaysNormal, CBFArm1, PRECAUTIONS, STAY_HOME
    from arm3 import Arm3Rule
    if "pop" not in _POP:
        _POP["pop"] = build_population(N=N, seed=0)
    pop = _POP["pop"]
    kw = dict(N=N, seed=seed, days=DAYS, f_D=pop.vulnerability, window=28, detection_rate=0.7,
              **SCEN[sc])
    t0 = time.time()
    if kind == "ctrl":
        o = run_shared_world(decision=AlwaysNormal(), **kw)
    elif kind == "arm1":
        o = run_shared_world(decision=CBFArm1(), **kw)
    else:
        o = run_shared_world(decision=Arm3Rule(k, pop), redecide_prob=P_REASK,
                             stop_deciding_when_no_infection=True, social_norm_def=norm, **kw)
    rec = {key: np.asarray(o[key], float) for key in KEEP}
    deciders = o["S"] * N + o["exposed"]                  # never-ill and alive: S or E
    if kind == "arm1":
        cautious = o["SB"]                                # E24: arm 1 = share in S^B
    else:
        cautious = (o["S_by_action"][:, PRECAUTIONS] + o["S_by_action"][:, STAY_HOME]
                    + o["E_by_action"][:, PRECAUTIONS] + o["E_by_action"][:, STAY_HOME])
    with np.errstate(invalid="ignore", divide="ignore"):
        rec["caution"] = np.where(deciders > 0, cautious / deciders, np.nan)
    return name, seed, rec, time.time() - t0


def waves(y):
    import step3_shape_metrics as sm
    return sm.kabu_n_waves(y, kernel=18)


def simulate():
    os.makedirs(OUT, exist_ok=True)
    cfgs = configs()
    tasks = [(n, c, s) for n, c in cfgs.items() for s in SEEDS]
    t0 = time.time()
    res, times = {}, []
    with mp.Pool(16) as pool:
        for name, seed, rec, dt in pool.imap_unordered(run_one, tasks, chunksize=2):
            res[(name, seed)] = rec
            times.append(dt)
    t_sim = time.time() - t0
    print(f"{len(tasks)} simulations in {t_sim / 60:.1f} min (per run {min(times):.1f}-"
          f"{max(times):.1f}s)", flush=True)
    need_m1 = [(n, s) for n in cfgs if not n.startswith("arm1") for s in SEEDS]
    t0 = time.time()
    with mp.Pool(16) as pool:
        m1 = pool.map(waves, [res[x]["incidence"] for x in need_m1], chunksize=2)
    t_kabu = time.time() - t0
    print(f"{len(need_m1)} wave counts in {t_kabu / 60:.1f} min; total "
          f"{(t_sim + t_kabu) / 60:.1f} min", flush=True)
    arrays = {}
    for n in cfgs:
        for key in KEEP + ("caution",):
            arrays[f"{n}#{key}"] = np.array([res[(n, s)][key] for s in SEEDS])
    m1d = dict(zip(need_m1, m1))
    for n in cfgs:
        if not n.startswith("arm1"):
            arrays[f"{n}#m1"] = np.array([m1d[(n, s)] for s in SEEDS])
    np.savez_compressed(CACHE, **arrays)
    json.dump(dict(t_sim_min=t_sim / 60, t_kabu_min=t_kabu / 60, n_sim=len(tasks),
                   n_kabu=len(need_m1)), open(os.path.join(OUT, "arm3_runs_timing.json"), "w"))


def mean_sem(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def death_resp(sig, caution, active):
    from scipy.stats import spearmanr
    out = []
    for s_, c_, a_ in zip(sig, caution, active):
        m = (a_ > 0) & np.isfinite(c_)
        x, y = s_[m], c_[m]
        if m.sum() < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
            out.append(np.nan)
        else:
            out.append(float(spearmanr(x, y)[0]))
    return np.array(out)


def score():
    import step3_shape_metrics as sm
    a = dict(np.load(CACHE))
    cfgs = configs()
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    R = {}

    def get(n, key):
        return a[f"{n}#{key}"]

    for n, (kind, sc, k, norm) in cfgs.items():
        inc, prev, exp_ = get(n, "incidence"), get(n, "prevalence"), get(n, "exposed")
        active = exp_ + prev
        r = dict(finished_600=int(sum(active[:, DAYS - 1] == 0)), n=len(SEEDS),
                 final_S=mean_sem(get(n, "S")[:, -1]), peak_I=mean_sem(prev.max(1)))
        dr = death_resp(get(n, "awareness_signal"), get(n, "caution"), active)
        r["death_resp"] = dict(mean=float(np.nanmean(dr)) if np.isfinite(dr).any() else np.nan,
                               median=float(np.nanmedian(dr)) if np.isfinite(dr).any() else np.nan,
                               n_defined=int(np.isfinite(dr).sum()), per_run=dr.tolist())
        r["mean_caution_active"] = float(np.nanmean([np.nanmean(c[ac > 0]) if (ac > 0).any()
                                                     else np.nan for c, ac in
                                                     zip(get(n, "caution"), active)]))
        if kind != "ctrl":
            ctl = f"ctrl|{sc}"
            m3, m3c = (np.array([sm.duration(y) for y in inc]),
                       np.array([sm.duration(y) for y in get(ctl, "incidence")]))
            ok = np.isfinite(m3) & np.isfinite(m3c)
            ratio = m3 / m3c
            bt = []
            for idx in boot_idx:
                ii = idx[ok[idx]]
                bt.append(m3[ii].mean() / m3c[ii].mean() if len(ii) else np.nan)
            pI, pIc = prev.max(1), get(ctl, "prevalence").max(1)
            fS, fSc = get(n, "S")[:, -1], get(ctl, "S")[:, -1]
            dI, dS = mean_sem(pI - pIc), mean_sem(fS - fSc)
            r.update(
                m3=mean_sem(m3), m3_ctrl=mean_sem(m3c), m3_defined=int(ok.sum()),
                stretch=float(m3[ok].mean() / m3c[ok].mean()),
                stretch_ci=tuple(np.nanpercentile(bt, [2.5, 97.5])),
                stretch_median=float(np.median(ratio[ok])),
                stretch_share_gt_1_5=f"{int((ratio[ok] > 1.5).sum())}/{int(ok.sum())}",
                peak_red_pct=float(-dI[0] / pIc.mean() * 100), peak_I_paired=dI,
                final_S_paired=dS)
            if kind == "rule":
                w, wc = get(n, "m1"), get(ctl, "m1")
                r.update(m1=mean_sem(w), m1_ctrl=mean_sem(wc), m1_paired=mean_sem(w - wc),
                         m1_multi=f"{int((w > 1).sum())}/{len(w)}")
        R[n] = r

    # arm 1 bit-identity against the stored C27 runs
    stored = json.load(open(os.path.join(ROOT, "results", "step2_scenarios.json")))["per_seed"]
    ident = {}
    for sc in SCEN:
        st = stored[f"N3000_{sc}"]
        fS, pI = get(f"arm1|{sc}", "S")[:, -1], get(f"arm1|{sc}", "prevalence").max(1)
        ident[sc] = int(sum(fS[s] == st[str(s)]["final_S"] and pI[s] == st[str(s)]["peak_I"]
                            for s in SEEDS))
    c30 = json.load(open(os.path.join(ROOT, "results", "step3", "arm1_scores.json")))["summary"]

    print("Arm 1 shared-world rerun vs stored C27 (final S and peak I identical): "
          + ", ".join(f"{sc} {v}/30" for sc, v in ident.items()))
    for sc in SCEN:
        print(f"\n===== {sc} {SCEN[sc]} =====")
        c = R[f"ctrl|{sc}"]
        print(f"control: final S {c['final_S'][0]:.4f}, peak I {c['peak_I'][0]:.1f}, finished by 600 "
              f"{c['finished_600']}/30")
        hdr = ("rule | stretch [95% CI] | median | >x1.5 | M3 arm/ctrl (n) | peak red % (SEM) | "
               "final S (paired +) | M1 arm/ctrl; paired; >1 wave | fin600 | DR mean / median (n) "
               "| mean caution")
        print(hdr)
        for k in RULES:
            r = R[f"rule{k}|{sc}"]
            print(f"  {k} | x{r['stretch']:.3f} [{r['stretch_ci'][0]:.3f}, {r['stretch_ci'][1]:.3f}] | "
                  f"x{r['stretch_median']:.3f} | {r['stretch_share_gt_1_5']} | {r['m3'][0]:.1f}/"
                  f"{r['m3_ctrl'][0]:.1f} ({r['m3_defined']}) | {r['peak_red_pct']:.1f} "
                  f"({r['peak_I_paired'][0] / r['peak_I_paired'][1]:+.1f} SEM) | {r['final_S'][0]:.4f} "
                  f"({r['final_S_paired'][0]:+.4f}, {r['final_S_paired'][0] / r['final_S_paired'][1]:+.1f} SEM)"
                  f" | {r['m1'][0]:.2f}/{r['m1_ctrl'][0]:.2f}; {r['m1_paired'][0]:+.2f}; {r['m1_multi']} | "
                  f"{r['finished_600']}/30 | {r['death_resp']['mean']:+.3f} / {r['death_resp']['median']:+.3f} "
                  f"({r['death_resp']['n_defined']}) | {r['mean_caution_active']:.3f}")
        rs = [R[f"rule{k}|{sc}"] for k in RULES]
        def agg(f):
            v = np.array([f(r) for r in rs], float)
            return f"{v.mean():.3f} [{v.min():.3f}, {v.max():.3f}]"
        print(f"  ARM 3 (mean [min, max] over 5 rules): stretch {agg(lambda r: r['stretch'])}; "
              f"median {agg(lambda r: r['stretch_median'])}; peak red % {agg(lambda r: r['peak_red_pct'])}; "
              f"final S {agg(lambda r: r['final_S'][0])}; M1 {agg(lambda r: r['m1'][0])}; "
              f"DR mean {agg(lambda r: r['death_resp']['mean'])}")
        a1, c1 = R[f"arm1|{sc}"], c30[sc]
        print(f"  ARM 1 (C30): stretch x{c1['stretch_ratio_of_means']['value']:.3f} "
              f"[{c1['stretch_ratio_of_means']['ci'][0]:.3f}, {c1['stretch_ratio_of_means']['ci'][1]:.3f}]; "
              f"peak red {c1['peak_I_reduction_pct']:.1f}%; final S increase "
              f"{c1['final_S_paired']['mean']:+.4f}; M1 {c1['m1_arm'][0]:.2f}; shared-world rerun: "
              f"final S {a1['final_S'][0]:.4f}, DR mean {a1['death_resp']['mean']:+.3f} / median "
              f"{a1['death_resp']['median']:+.3f} (n {a1['death_resp']['n_defined']}), mean caution "
              f"{a1['mean_caution_active']:.3f}, finished {a1['finished_600']}/30")

    print("\n===== SUPPLEMENTARY: S1, social_norm = normal / (S,E,I,R not staying home) =====")
    for k in RULES:
        m, s_ = R[f"rule{k}|S1"], R[f"supp_rule{k}|S1"]
        print(f"  {k} | stretch x{s_['stretch']:.3f} [{s_['stretch_ci'][0]:.3f}, {s_['stretch_ci'][1]:.3f}]"
              f" (main x{m['stretch']:.3f}; diff {s_['stretch'] - m['stretch']:+.3f}) | median "
              f"x{s_['stretch_median']:.3f} | >x1.5 {s_['stretch_share_gt_1_5']} | peak red "
              f"{s_['peak_red_pct']:.1f}% (main {m['peak_red_pct']:.1f}; diff "
              f"{s_['peak_red_pct'] - m['peak_red_pct']:+.1f}) | final S {s_['final_S'][0]:.4f} (main "
              f"{m['final_S'][0]:.4f}; diff {s_['final_S'][0] - m['final_S'][0]:+.4f}) | M1 "
              f"{s_['m1'][0]:.2f} (main {m['m1'][0]:.2f}) | fin600 {s_['finished_600']}/30 | DR "
              f"{s_['death_resp']['mean']:+.3f} (main {m['death_resp']['mean']:+.3f}) | caution "
              f"{s_['mean_caution_active']:.3f} (main {m['mean_caution_active']:.3f})")
    json.dump(dict(results=R, arm1_identity=ident), open(os.path.join(OUT, "arm3_scores.json"), "w"),
              indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def aligned_m3(inc, seeds_idx=None, frac=0.01):
    """A33's averaged-curve M3: per-capita curves aligned at the first day cumulative incidence
    >= frac*N, averaged over the common window (step3_shape_metrics.align_average), T10-90 of
    the mean. Runs that never reach frac*N are left out (n used reported). `seeds_idx` selects
    rows (with repeats, for the bootstrap)."""
    import step3_shape_metrics as sm
    rows = range(len(inc)) if seeds_idx is None else seeds_idx
    starts, kept = [], []
    for i in rows:
        hit = np.nonzero(np.cumsum(inc[i]) >= frac * N)[0]
        if len(hit):
            starts.append(int(hit[0])); kept.append(inc[i] / N)
    if not kept:
        return np.nan, 0
    L = DAYS - max(starts)
    return sm.duration(np.mean([y[s:s + L] for y, s in zip(kept, starts)], axis=0)), len(kept)


def aligned(cfg_names=None, cache=CACHE, label="C39"):
    """Averaged-curve M3 per configuration (never across rules), with 1,000 paired bootstrap
    resamples of seeds (seed 20261005), next to the per-run stretch."""
    a = dict(np.load(cache))
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    cfgs = cfg_names or [n for n in configs() if not n.startswith(("arm1", "ctrl"))]
    out = {}
    print(f"{label}: averaged-curve M3 (1% alignment) arm / control [95% CI], n used; "
          f"averaged-curve stretch [95% CI]")
    for n in cfgs:
        sc = n.split("|")[1]
        inc, incc = a[f"{n}#incidence"], a[f"ctrl|{sc}#incidence"]
        m, nu = aligned_m3(inc)
        mc, nuc = aligned_m3(incc)
        bm, bc, br = [], [], []
        for idx in boot_idx:
            x, _ = aligned_m3(inc, idx)
            y, _ = aligned_m3(incc, idx)
            bm.append(x); bc.append(y); br.append(x / y)
        ci = lambda v: tuple(np.nanpercentile(v, [2.5, 97.5]))   # noqa: E731
        out[n] = dict(arm=m, arm_ci=ci(bm), n_used=nu, ctrl=mc, ctrl_ci=ci(bc), n_used_ctrl=nuc,
                      stretch=m / mc, stretch_ci=ci(br),
                      boot_defined=int(np.isfinite(br).sum()))
        r = out[n]
        print(f"  {n:16s} {m:5.0f} [{r['arm_ci'][0]:.0f}, {r['arm_ci'][1]:.0f}] (n {nu}/30) / "
              f"{mc:4.0f} [{r['ctrl_ci'][0]:.0f}, {r['ctrl_ci'][1]:.0f}] (n {nuc}/30); "
              f"x{r['stretch']:.3f} [{r['stretch_ci'][0]:.3f}, {r['stretch_ci'][1]:.3f}]")
    return out


if __name__ == "__main__":
    mp.freeze_support()
    if "--sim" in sys.argv:
        simulate()
    if "--score" in sys.argv:
        score()
    if "--aligned" in sys.argv:
        json.dump(aligned(), open(os.path.join(OUT, "arm3_aligned.json"), "w"), indent=1)
