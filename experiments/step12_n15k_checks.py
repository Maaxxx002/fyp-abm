"""
Step 12 (register C54-C57). PROVISIONAL setting under test: N = 15,000 with a 7-day signal
(proposed, not adopted; A24 stands). No API calls (no Anthropic, no Qwen).

  Part 1 (C54)  C51 9a repeated with re-decide rate p = 0.3: Weitz test rule, step C, 7-day signal,
                S1, N = 15,000, N*delta_c 0.075, seeds 0-9, own AlwaysNormal control.
  Part 2 (C55)  Arm 1 (CBF, unchanged rule and parameters, CBFArm1) in the shared world, N = 15,000,
                7-day signal, S1/S2/S3, seeds 0-9, own AlwaysNormal controls.
  Part 3 (C56)  E26 criterion (i) rescored with lag windows +/-21, 28, 42, 63 d on every case of
                C50, C51, C52 10c and Parts 1-2.
  Part 4 (C57)  prompts for the offline Qwen token count: the 42 C37 pilot prompts and a uniform
                random sample of 1,000 frozen-v1 prompts from C53's dry run (counted in a separate
                tokenizer environment, experiments/step12_qwen_tokens.py).

Usage:  python experiments/step12_n15k_checks.py --timing | --sim | --score | --lags | --sample
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
import step6_plateau_check as pc  # noqa: E402
import step7_cheaper_plateau as cp  # noqa: E402
import step8_plateau_followup as s8  # noqa: E402
import step11_prompt_reuse as s11  # noqa: E402

N = 15_000
SEEDS = list(range(10))
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
NDC = cp.DCRIT * N                          # 0.075
WINDOWS = [21, 28, 42, 63]
OUT = cp.OUT
CACHE = os.path.join(OUT, "step12_runs.npz")
PROMPTS = os.path.join(OUT, "step12_prompts.json")
SAMPLE_SEED = 20261031
_POP = {}

# C30 / C27 / C39 / C50 (N = 3,000, 28-day signal, 30 seeds), copied from the register for the table
C30 = {"S1": dict(stretch="×1.079 [1.018, 1.158]", median="×1.000", peak_red=12.8, final_S=0.1444, attack=0.856,
                  active="0/30", m1="1.00", dr="+0.792", e26="PASS"),
       "S2": dict(stretch="×1.239 [0.962, 1.704]", median="×0.964", peak_red=23.6, final_S=0.4075, attack=0.593,
                  active="0/30", m1="1.20", dr="+0.647", e26="PASS"),
       "S3": dict(stretch="×1.020 [0.987, 1.057]", median="×0.980", peak_red=7.0, final_S=0.1094, attack=0.891,
                  active="0/30", m1="1.00", dr="+0.864", e26="PASS")}


def run_arm1(task):
    kind, sc, seed = task
    from population import build_population
    from shared_world import run_shared_world, AlwaysNormal, CBFArm1, PRECAUTIONS
    if N not in _POP:
        _POP[N] = build_population(N=N, seed=0)
    t0 = time.time()
    o = run_shared_world(N=N, seed=seed, decision=CBFArm1() if kind == "arm1" else AlwaysNormal(), days=600,
                         f_D=_POP[N].vulnerability, window=7, detection_rate=0.7, **SCEN[sc])
    rec = {k: np.asarray(o[k], float) for k in ("incidence", "prevalence", "exposed", "S", "awareness_signal",
                                                "recovered", "deaths")}
    dec = o["S_by_action"].sum(1) + o["E_by_action"].sum(1)        # whole agents (C49)
    with np.errstate(invalid="ignore", divide="ignore"):
        rec["caution"] = np.where(dec > 0, o["S_by_action"][:, PRECAUTIONS] / np.where(dec > 0, dec, 1), np.nan)
    rec["H_eod"] = (N - np.rint(o["S"] * N) - o["exposed"] - o["prevalence"] - o["recovered"]
                    - np.cumsum(o["deaths"]))
    return ("arm1", task), rec, time.time() - t0


def run_p1(task):
    t, rec, dt = cp.run_one(task)
    return ("p1", t), rec, dt


def p1_tasks():
    return ([("C", N, None, NDC, s, 7, 0.3) for s in SEEDS] + [("ctrl", N, None, None, s, 28) for s in SEEDS])


def arm1_tasks():
    return [(k, sc, s) for sc in SCEN for k in ("arm1", "ctrl") for s in SEEDS]


def key(part, t):
    return f"{part}|" + "|".join(str(x) for x in t)


def _dispatch(x):
    part, t = x
    return run_p1(t) if part == "p1" else run_arm1(t)


def timing():
    tt = ([("p1", t) for t in p1_tasks() if t[4] == 0]
          + [("arm1", t) for t in arm1_tasks() if t[2] == 0])
    t0 = time.time()
    with mp.Pool(16) as pool:
        out = pool.map(_dispatch, tt)
    for (part, t), rec, dt in out:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  {key(part, t):40s} {dt:6.1f}s (last active day {last})")
    print(f"  wall {time.time() - t0:.1f}s for {len(tt)} runs (16 workers)")


def simulate():
    from step5_arm3_runs import waves
    tt = [("p1", t) for t in p1_tasks()] + [("arm1", t) for t in arm1_tasks()]
    arr, t0, times = {}, time.time(), []
    with mp.Pool(16) as pool:
        for (part, t), rec, dt in pool.imap_unordered(_dispatch, tt):
            for k, v in rec.items():
                arr[f"{key(part, t)}#{k}"] = v
            times.append(dt)
    t_sim = time.time() - t0
    wk = [f"{key('arm1', t)}" for t in arm1_tasks()]
    t0 = time.time()
    with mp.Pool(16) as pool:
        m1 = pool.map(waves, [arr[f"{k}#incidence"] for k in wk])
    for k, w in zip(wk, m1):
        arr[f"{k}#m1"] = np.array(w)
    np.savez_compressed(CACHE, **arr)
    print(f"{len(tt)} simulations {t_sim / 60:.1f} min (per run {min(times):.1f}-{max(times):.1f}s); "
          f"{len(wk)} wave counts {(time.time() - t0) / 60:.1f} min")


# ------------------------------------------------------------------ summaries

def summ(inc, prev, exp_, S, incc, prevc, Sc, H):
    import step3_shape_metrics as sm
    from step5_arm3_runs import mean_sem
    m3 = np.array([sm.duration(y) for y in inc])
    m3c = np.array([sm.duration(y) for y in incc])
    ratio = m3 / m3c
    rng = np.random.default_rng(pc.BOOT_SEED)
    boot = rng.integers(0, len(inc), size=(pc.N_BOOT, len(inc)))
    bt = [m3[i].mean() / m3c[i].mean() for i in boot]
    dI = mean_sem(prev.max(1) - prevc.max(1))
    active = (exp_ + prev) > 0
    h_main = [float(h[ac].mean()) if ac.any() else 0.0 for h, ac in zip(H, active)]
    r = dict(stretch=float(m3.mean() / m3c.mean()), stretch_ci=[float(x) for x in np.percentile(bt, [2.5, 97.5])],
             median=float(np.median(ratio)), ge10=int((ratio >= 10).sum()), gt15=int((ratio > 1.5).sum()),
             m3=float(m3.mean()), m3_ctrl=float(m3c.mean()),
             peak_red=float(-dI[0] / prevc.max(1).mean() * 100), peak_sems=float(dI[0] / dI[1]),
             final_S=float(S[:, -1].mean()), final_S_sd=float(S[:, -1].std(ddof=1)),
             final_S_ctrl=float(Sc[:, -1].mean()), attack=float(1 - S[:, -1].mean()),
             active_600=int(active[:, -1].sum()),
             last_active=sorted(int(np.nonzero(ac)[0].max()) + 1 if ac.any() else 0 for ac in active),
             H_main_mean=float(np.mean(h_main)), H_main_range=[float(min(h_main)), float(max(h_main))])
    r["c42_pass"] = bool(r["stretch"] >= 10 or (r["active_600"] > len(inc) / 2 and r["peak_red"] >= 80))
    return r


def sig28(deaths):
    return np.round(np.array([s8.signal28(d) for d in deaths]), 12)


def _print_case(label, r, e):
    fm = lambda x: "undef" if x is None else f"{x:+.3f}"  # noqa: E731
    print(f"\n{label}")
    print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
          f"{' (TRUNCATED)' if r['active_600'] else ''}; median x{r['median']:.2f}; >=x10 {r['ge10']}/10; "
          f">x1.5 {r['gt15']}/10; T10-90 {r['m3']:.1f} vs control {r['m3_ctrl']:.1f} d")
    print(f"  peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
          f"(SD {r['final_S_sd']:.4f}; control {r['final_S_ctrl']:.4f}); attack {r['attack']:.4f}")
    print(f"  active at day 600 {r['active_600']}/10; last active {r['last_active']}; mean end-of-day people in H "
          f"(main phase) {r['H_main_mean']:.2f} ({r['H_main_range'][0]:.2f}-{r['H_main_range'][1]:.2f}); "
          f"C42 pass mark {'MET' if r['c42_pass'] else 'NOT MET'}")
    print(f"  E26 (C50): max-lag DR {fm(e['drL_mean'])} / {fm(e['drL_median'])} ({e['drL_defined']}), best lag "
          f"{e['lag_median']} {e['lag_range']}; lag-0 DR (E24) {fm(e['dr0_mean'])} ({e['dr0_defined']}); caution SD "
          f"{'undef' if e['sd_mean'] is None else format(e['sd_mean'], '.3f')}; runs meeting (i)/(ii)/(iii)/all "
          f"{e['pass_iL']}/{e['pass_ii']}/{e['pass_iii']}/{e['all_rev']} -> {e['verdict_rev']}")


def score():
    from step5_arm3_runs import death_resp, mean_sem
    a = dict(np.load(CACHE))
    out = {}
    # ---- Part 1, next to C51 9a (p = 1)
    g = lambda kind, kk: np.array([a[f"{key('p1', t)}#{kk}"] for t in p1_tasks() if t[0] == kind])  # noqa: E731
    r = summ(*(g("C", k) for k in ("incidence", "prevalence", "exposed", "S")),
             *(g("ctrl", k) for k in ("incidence", "prevalence", "S")), g("C", "H_eod"))
    e = s8.per_run_rev(sig28(g("C", "deaths")), g("C", "caution"), g("C", "prevalence"), g("C", "exposed"), g("C", "S"))
    out["part1_p0.3"] = dict(r, e26=e)
    _print_case("PART 1 (C54): Weitz test rule, step C, 7-day, S1, N = 15,000, N*delta_c 0.075, p = 0.3", r, e)
    c51 = json.load(open(os.path.join(OUT, "step9_scores.json")))["9a step C 7-day, N = 15,000"]
    out["part1_C51_p1"] = c51
    _print_case("  ... beside C51 9a (p = 1.0), from step9_scores.json", c51, c51["e26"])
    # ---- Part 2
    print("\nPART 2 (C55): arm 1 (CBF unchanged), shared world, N = 15,000, 7-day signal, 10 seeds; C30 beside")
    eff = {}
    for sc in SCEN:
        ga = lambda kind, kk: np.array([a[f"{key('arm1', (kind, sc, s))}#{kk}"] for s in SEEDS])  # noqa: E731
        r = summ(*(ga("arm1", k) for k in ("incidence", "prevalence", "exposed", "S")),
                 *(ga("ctrl", k) for k in ("incidence", "prevalence", "S")), ga("arm1", "H_eod"))
        cau, prev, exp_, S = ga("arm1", "caution"), ga("arm1", "prevalence"), ga("arm1", "exposed"), ga("arm1", "S")
        e = s8.per_run_rev(sig28(ga("arm1", "deaths")), cau, prev, exp_, S)
        dr7 = death_resp(ga("arm1", "awareness_signal"), cau, exp_ + prev)
        w, wc = ga("arm1", "m1"), ga("ctrl", "m1")
        r.update(e26=e, m1=float(w.mean()), m1_multi=int((w > 1).sum()), m1_ctrl=float(wc.mean()),
                 dr_7day_mean=float(np.nanmean(dr7)), dr_7day_defined=int(np.isfinite(dr7).sum()))
        out[f"part2_{sc}"] = r
        _print_case(f"arm 1 {sc}", r, e)
        print(f"  waves {r['m1']:.2f} (> 1 wave {r['m1_multi']}/10; control {r['m1_ctrl']:.2f}); DR vs the world's own "
              f"7-day signal (info) {r['dr_7day_mean']:+.3f} ({r['dr_7day_defined']})")
        c = C30[sc]
        print(f"  C30 (N 3,000, 28-day, n 30): stretch {c['stretch']}, median {c['median']}, peak red {c['peak_red']}%, "
              f"final S {c['final_S']}, attack {c['attack']}, active {c['active']}, waves {c['m1']}, DR {c['dr']}, "
              f"E26 {c['e26']}")
        eff[sc] = dict(S=ga("arm1", "S")[:, -1] - ga("ctrl", "S")[:, -1],
                       I=ga("arm1", "prevalence").max(1) - ga("ctrl", "prevalence").max(1))
    print("\n  scenario separation (C27 method: per-seed difference of behaviour effects vs S1, n = 10):")
    sep = {}
    for sc in ("S2", "S3"):
        dS, dI = mean_sem(eff[sc]["S"] - eff["S1"]["S"]), mean_sem(eff[sc]["I"] - eff["S1"]["I"])
        sep[sc] = dict(final_S=dS, peak_I=dI)
        print(f"  {sc} vs S1: final S {dS[0]:+.4f} +/- {dS[1]:.4f} ({dS[0] / dS[1]:+.2f} SEM); peak I {dI[0]:+.1f} "
              f"+/- {dI[1]:.1f} ({dI[0] / dI[1]:+.2f} SEM)")
    print("  C27 (N 3,000, n 30): S2 final S +0.1171 (+9.09 SEM), peak I +3.6 (+0.37); S3 final S -0.0350 "
          "(-5.82 SEM), peak I +39.3 (+3.96)")
    out["part2_separation"] = sep
    json.dump(out, open(os.path.join(OUT, "step12_scores.json"), "w"), indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


# ------------------------------------------------------------------ Part 3: lag windows

def lag_rhos(sig, caution, active, wmax=max(WINDOWS)):
    from scipy.stats import spearmanr
    T, out = len(sig), {}
    for L in range(-wmax, wmax + 1):
        t = np.arange(max(0, -L), min(T, T - L))
        m = active[t] & active[t + L] & np.isfinite(caution[t + L])
        x, y = sig[t][m], caution[t + L][m]
        if m.sum() >= 3 and np.ptp(x) > 0 and np.ptp(y) > 0:
            out[L] = float(spearmanr(x, y)[0])
    return out


def _lag_case(args):
    label, (sig, cau, prev, exp_, S) = args
    active = (exp_ + prev) > 0
    rhos = [lag_rhos(s_, c_, a_) for s_, c_, a_ in zip(sig, cau, active)]
    sd = np.array([float(np.std(c[ac & np.isfinite(c)], ddof=1)) if (ac & np.isfinite(c)).sum() >= 2 else np.nan
                   for c, ac in zip(cau, active)])
    ok_ii = np.isfinite(sd) & (np.nan_to_num(sd, nan=-9) >= 0.05)
    ok_iii = (1 - S[:, -1]) >= 0.10
    res = {}
    for W in WINDOWS:
        best = np.array([max([v for L, v in r.items() if abs(L) <= W], default=np.nan) for r in rhos])
        ok_i = np.isfinite(best) & (np.nan_to_num(best, nan=-9) >= 0.3)
        allok = ok_i & ok_ii & ok_iii
        res[W] = dict(pass_i=int(ok_i.sum()), pass_all=int(allok.sum()), n=len(S),
                      verdict="PASS" if allok.sum() > len(S) / 2 else "FAIL",
                      dr_mean=float(np.nanmean(best)) if np.isfinite(best).any() else None)
    return label, res


def lag_cases():
    cases, _ = s8.e26_cases()
    cases = [(f"C50 {lab}", d) for lab, d in cases]
    b = dict(np.load(os.path.join(OUT, "step9_runs.npz")))
    import step9_7day_signal as s9
    for lab, kind, n, f, w, _ in s9.cases():
        gg = lambda k: np.array([b[f"{kind}|{n}|{f}|{w}|{s}#{k}"] for s in s9.SEEDS])  # noqa: E731
        cases.append((f"C51 {lab}", (sig28(gg("deaths")), gg("caution"), gg("prevalence"), gg("exposed"), gg("S"))))
    c = dict(np.load(os.path.join(OUT, "step10_runs.npz")))
    gg = lambda k: np.array([c[f"C|10000|None|7|{s}#{k}"] for s in SEEDS])  # noqa: E731
    cases.append(("C52 10c step C 7-day, N = 10,000", (sig28(gg("deaths")), gg("caution"), gg("prevalence"),
                                                       gg("exposed"), gg("S"))))
    a = dict(np.load(CACHE))
    g = lambda kk: np.array([a[f"{key('p1', t)}#{kk}"] for t in p1_tasks() if t[0] == "C"])  # noqa: E731
    cases.append(("C54 Part 1 step C 7-day p 0.3, N = 15,000", (sig28(g("deaths")), g("caution"), g("prevalence"),
                                                                g("exposed"), g("S"))))
    for sc in SCEN:
        ga = lambda kk: np.array([a[f"{key('arm1', ('arm1', sc, s))}#{kk}"] for s in SEEDS])  # noqa: E731
        cases.append((f"C55 Part 2 arm 1 7-day N = 15,000 {sc}", (sig28(ga("deaths")), ga("caution"),
                                                                  ga("prevalence"), ga("exposed"), ga("S"))))
    return cases


def lags():
    cases = lag_cases()
    t0 = time.time()
    with mp.Pool(16) as pool:
        res = pool.map(_lag_case, cases)
    out, changed = {}, []
    print(f"E26 verdict per lag window (criterion (i) = max Spearman over |L| <= W; (ii), (iii), thresholds unchanged); "
          f"{len(cases)} cases, {time.time() - t0:.0f}s")
    print("case | n | " + " | ".join(f"+/-{W}: (i) runs, all runs, verdict" for W in WINDOWS) + " | changes vs +/-42")
    for label, r in res:
        v42 = r[42]["verdict"]
        ch = [W for W in WINDOWS if r[W]["verdict"] != v42]
        if ch:
            changed.append((label, ch))
        out[label] = {str(W): v for W, v in r.items()}
        print(f"{label} | {r[42]['n']} | " + " | ".join(f"{r[W]['pass_i']}, {r[W]['pass_all']}, {r[W]['verdict']}"
                                                         for W in WINDOWS) + f" | {ch or 'none'}")
    print(f"\ncases whose verdict differs from the +/-42 verdict in any window: {len(changed)} {changed}")
    json.dump(dict(cases=out, changed=changed), open(os.path.join(OUT, "step12_lags.json"), "w"), indent=1)


# ------------------------------------------------------------------ Part 4: prompt sample

class SamplingStub(s11.CountingStub):
    """C53's stub; additionally renders (with the real v1 renderer) the decisions whose running index
    within the run is in `pick`. Draws exactly as C53 (the parent's decide does the drawing)."""

    def __init__(self, probs, pop, pick):
        super().__init__(probs, pop)
        self.pick, self.k, self.rendered = set(pick), 0, []

    def decide(self, day, agents, view, rng):
        from perception import Perception
        hit = [j for j in range(len(agents)) if self.k + j in self.pick]
        if hit:
            _, (m28, m28_7) = s11.dyn_fields(day, view["reported_deaths"], view["social_norm"], view["N"])
            rep, pop = view["reported_deaths"], self.pop
            for j in hit:
                i = agents[j]
                self.rendered.append((self.k + j, s11.rt.render(Perception(
                    deaths_28day_mean=m28, deaths_cumulative=float(rep.sum()), deaths_28day_mean_7d_ago=m28_7,
                    current_action=s11.ACT_NAME[int(view["action"][i])], social_norm=float(view["social_norm"]),
                    age_band=int(pop.age_band[i]), vulnerability=float(pop.vulnerability[i]),
                    occupation_flex=float(pop.occupation_flex[i]), response_efficacy=float(pop.response_efficacy[i]),
                    population=int(view["N"]), day=int(day)))))
        self.k += len(agents)
        return super().decide(day, agents, view, rng)


def _sample_run(args):
    (stub, sc, n, seed), pick = args
    from population import build_population
    from shared_world import run_shared_world
    if n not in _POP:
        _POP[n] = build_population(N=n, seed=0)
    d = SamplingStub(s11.STUBS[stub], _POP[n], pick)
    run_shared_world(N=n, seed=seed, decision=d, days=600, f_D=_POP[n].vulnerability, window=7, detection_rate=0.7,
                     redecide_prob=0.3, stop_deciding_when_no_infection=True, **s11.SCEN[sc])
    return (stub, sc, n, seed), d.k, d.rendered


def sample():
    counts = json.load(open(os.path.join(OUT, "step11_counts.json")))
    runs = []
    for k, r in counts.items():
        stub, sc, n = k.split("|")
        for s, c in zip(s11.SEEDS, r["decisions_per_run"]):
            runs.append(((stub, sc, int(n), s), c))
    total = sum(c for _, c in runs)
    idx = np.sort(np.random.default_rng(SAMPLE_SEED).choice(total, 1000, replace=False))
    starts = np.cumsum([0] + [c for _, c in runs])
    jobs = []
    for j, (run, c) in enumerate(runs):
        pick = (idx[(idx >= starts[j]) & (idx < starts[j + 1])] - starts[j]).tolist()
        if pick:
            jobs.append((run, pick))
    t0 = time.time()
    with mp.Pool(16) as pool:
        res = pool.map(_sample_run, jobs)
    cnt = dict(runs)
    mism = [r for r, k, _ in res if k != cnt[r]]
    prompts = [dict(run=list(r), index=i, text=txt) for r, _, rend in res for i, txt in rend]
    sits = json.load(open(os.path.join(ROOT, "results", "step4", "pilot_v4_situations.json")))
    c37 = [dict(id=s["id"], wording=w, text=t) for s in sits for w, t in s["prompts"].items()]
    json.dump(dict(c37=c37, c53_sample=prompts, sample_seed=SAMPLE_SEED, total_decisions=int(total)),
              open(PROMPTS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"C53 decisions {total:,}; sampled {len(idx)}; rendered {len(prompts)} from {len(jobs)} runs; runs whose "
          f"decision count differs from C53: {len(mism)}; C37 prompts {len(c37)}; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--timing", timing), ("--sim", simulate), ("--score", score), ("--lags", lags),
                     ("--sample", sample)):
        if flag in sys.argv:
            fn()
