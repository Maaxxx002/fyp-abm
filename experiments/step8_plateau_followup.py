"""
Step 8 (register C47-C50). Capability tests and measure revisions, NOT arms. No API calls.

  8a  Step C (agents' own mean of 70%-reported deaths, daily decisions, p = 1, A55 stop) at
      N = 15,000 / 20,000 / 30,000, normal per-agent f_D, C43's per-capita delta_c (0.5e-5/day),
      seeds 0-9; at N = 30,000 also with a 7-DAY mean (a test of reverting A24 at large N).
  8b  Route B retry at N = 3,000, f_D in {0.05, 0.10}: N*delta_c = HALF the C45 edge value.
      Equations first, then step B and step C, seeds 0-9.
  8c  E24 rounding fix (cautious and deciding agents counted as whole agents). Old caches are
      converted exactly (cautious = rint(caution * (S*N + E)), deciders = rint(S*N) + E); the
      conversion is checked against fresh reruns with the fixed code.
  8d  E26 criterion (i) REVISED after the C46 failure: max over lags L = -42..+42 days of the
      Spearman correlation between deaths_28day_mean on day t and the cautious share on day t+L
      (L < 0: caution leads), over days t with t and t+L both active (end-of-day E + I > 0);
      undefined at a lag with < 3 pairs or a constant series. (ii), (iii), thresholds unchanged.

Usage:  python experiments/step8_plateau_followup.py --ode | --timing | --sim | --score | --e24 | --e26
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
import step7_real_plateau_check as rp  # noqa: E402

SEEDS = list(range(10))
SIZES_8A = [15_000, 20_000, 30_000]
F_D_8B = [0.05, 0.10]
LAGS = range(-42, 43)
OUT = cp.OUT
CACHE = os.path.join(OUT, "step8_runs.npz")
C39_CACHE = rp.C39_CACHE


def ndc_8b():
    edge = cp.chosen_ndc()
    return {f: edge[f] / 2 for f in F_D_8B}


def step_ode():
    rows = {}
    for f, ndc in ndc_8b().items():
        _, _, r = cp._ode_row((ndc, f))
        rows[str(f)] = dict(ndc=ndc, **r)
        print(f"f_D {f}: N*delta_c {ndc:.4f} (half of {2 * ndc:.4f}): T10-90 {r['m3']:.0f} d, stretch "
              f"x{r['stretch']:.2f}, peak red {r['peak_red']:.1f}%, final S {r['final_S']:.4f}, "
              f"E+I at day 600 {r['active_600_EI']:.2f} persons, plateau criterion {r['plateau']}, "
              f"ODE mean H (E+I>=1) {r['H_main_mean']:.2f}")
    json.dump(rows, open(os.path.join(OUT, "step8_ode.json"), "w"), indent=1)


def tasks():
    t = []
    for n in SIZES_8A:
        for s in SEEDS:
            t += [("C", n, None, cp.DCRIT * n, s, 28), ("ctrl", n, None, None, s, 28)]
    t += [("C", 30_000, None, cp.DCRIT * 30_000, s, 7) for s in SEEDS]
    for f, ndc in ndc_8b().items():
        for s in SEEDS:
            t += [("B", cp.N3K, f, ndc, s, 28), ("C", cp.N3K, f, ndc, s, 28), ("ctrl", cp.N3K, f, None, s, 28)]
    return t


def key(task):
    kind, n, f, _, s, w = task
    return f"{kind}|{n}|{f}|{w}|{s}"


def timing():
    tt = [x for x in tasks() if x[4] == 0]
    t0 = time.time()
    with mp.Pool(16) as pool:
        out = pool.map(cp.run_one, tt)
    for task, rec, dt in out:
        act = rec["exposed"] + rec["prevalence"]
        last = int(np.nonzero(act > 0)[0].max()) + 1 if (act > 0).any() else 0
        print(f"  {key(task):32s} {dt:6.1f}s (last active day {last})")
    print(f"  wall {time.time() - t0:.1f}s for {len(tt)} runs (16 workers)")


def simulate():
    tt = sorted(tasks(), key=lambda x: -x[1])
    arr, times, t0 = {}, [], time.time()
    with mp.Pool(16) as pool:
        for task, rec, dt in pool.imap_unordered(cp.run_one, tt):
            for k, v in rec.items():
                arr[f"{key(task)}#{k}"] = v
            times.append(dt)
    print(f"{len(tt)} simulations {(time.time() - t0) / 60:.1f} min (per run {min(times):.1f}-{max(times):.1f}s)")
    np.savez_compressed(CACHE, **arr)


# ------------------------------------------------------------------ C45-style summary

def summarise(a, kind, n, f, w):
    import step3_shape_metrics as sm
    from step5_arm3_runs import mean_sem
    g = lambda k_, ww, kk: np.array([a[f"{k_}|{n}|{f}|{ww}|{s}#{kk}"] for s in SEEDS])  # noqa: E731
    inc, prev, exp_, S = (g(kind, w, k) for k in ("incidence", "prevalence", "exposed", "S"))
    incc, prevc, Sc = (g("ctrl", 28, k) for k in ("incidence", "prevalence", "S"))
    m3 = np.array([sm.duration(y) for y in inc])
    m3c = np.array([sm.duration(y) for y in incc])
    ratio = m3 / m3c
    rng = np.random.default_rng(pc.BOOT_SEED)
    boot = rng.integers(0, len(SEEDS), size=(pc.N_BOOT, len(SEEDS)))
    bt = [m3[i].mean() / m3c[i].mean() for i in boot]
    dI = mean_sem(prev.max(1) - prevc.max(1))
    active = (exp_ + prev) > 0
    H = g(kind, w, "H_sub" if kind == "B" else "H_eod")
    h_main = [float(h[ac].mean()) if ac.any() else 0.0 for h, ac in zip(H, active)]
    r = dict(stretch=float(m3.mean() / m3c.mean()), stretch_ci=[float(x) for x in np.percentile(bt, [2.5, 97.5])],
             median=float(np.median(ratio)), ge10=int((ratio >= 10).sum()), gt15=int((ratio > 1.5).sum()),
             m3=float(m3.mean()), m3_ctrl=float(m3c.mean()),
             peak_red=float(-dI[0] / prevc.max(1).mean() * 100), peak_sems=float(dI[0] / dI[1]),
             final_S=float(S[:, -1].mean()), final_S_sd=float(S[:, -1].std(ddof=1)),
             final_S_ctrl=float(Sc[:, -1].mean()), attack=float(1 - S[:, -1].mean()),
             active_600=int(active[:, -1].sum()),
             last_active=sorted(int(np.nonzero(ac)[0].max()) + 1 if ac.any() else 0 for ac in active),
             H_main_mean=float(np.mean(h_main)), H_main_range=[float(min(h_main)), float(max(h_main))],
             H_measure="sub-step mean" if kind == "B" else "end-of-day")
    r["c42_pass"] = bool(r["stretch"] >= 10 or (r["active_600"] > len(SEEDS) / 2 and r["peak_red"] >= 80))
    return r


def cases_8():
    nd = ndc_8b()
    c = [(f"8a step C 28-day, N = {n:,}", "C", n, None, 28, cp.DCRIT * n) for n in SIZES_8A]
    c.append(("8a step C 7-DAY (A24 revert test), N = 30,000", "C", 30_000, None, 7, cp.DCRIT * 30_000))
    for f in F_D_8B:
        c.append((f"8b step B, f_D {f}", "B", cp.N3K, f, 28, nd[f]))
        c.append((f"8b step C, f_D {f}", "C", cp.N3K, f, 28, nd[f]))
    return c


def score():
    a = dict(np.load(CACHE))
    out = {}
    for label, kind, n, f, w, ndc in cases_8():
        r = summarise(a, kind, n, f, w)
        r["ndc"] = ndc
        out[label] = r
        print(f"\n{label} (N*delta_c {ndc:.4g})")
        print(f"  stretch x{r['stretch']:.2f} [{r['stretch_ci'][0]:.2f}, {r['stretch_ci'][1]:.2f}]"
              f"{' (TRUNCATED)' if r['active_600'] else ''}; median x{r['median']:.2f}; >=x10 {r['ge10']}/10; "
              f">x1.5 {r['gt15']}/10; T10-90 {r['m3']:.1f} vs control {r['m3_ctrl']:.1f} d")
        print(f"  peak I reduction {r['peak_red']:.1f}% ({r['peak_sems']:+.1f} SEM); final S {r['final_S']:.4f} "
              f"(SD {r['final_S_sd']:.4f}; control {r['final_S_ctrl']:.4f}); attack {r['attack']:.4f}")
        print(f"  active at day 600 {r['active_600']}/10; last active {r['last_active']}; mean people in H "
              f"(main phase, {r['H_measure']}) {r['H_main_mean']:.2f} ({r['H_main_range'][0]:.2f}-"
              f"{r['H_main_range'][1]:.2f}); C42 pass mark {'MET' if r['c42_pass'] else 'NOT MET'}")
    json.dump(out, open(os.path.join(OUT, "step8_scores.json"), "w"), indent=1)


# ------------------------------------------------------------------ 8c: E24 rounding fix

def convert(caution, S, exposed, n):
    """Old float caution -> whole-agent caution (exact: cautious and deciders are integers)."""
    dec_f = S * n + exposed
    with np.errstate(invalid="ignore"):
        cautious = np.rint(np.nan_to_num(caution) * dec_f)
        dec = np.rint(S * n) + exposed
        resid = np.nanmax(np.abs(np.nan_to_num(caution) * dec_f - cautious))
        return np.where(dec > 0, cautious / np.where(dec > 0, dec, 1), np.nan), float(resid)


def e24():
    from step5_arm3_runs import death_resp, run_one as run39, configs
    c39 = dict(np.load(C39_CACHE))
    names = sorted({k.split("#")[0] for k in c39 if k.endswith("#caution")})
    # check the conversion against fresh reruns with the fixed code
    cf = configs()
    checks = [("arm1|S1", 0), ("rule1|S1", 0), ("rule2|S2", 3), ("rule4|S3", 7), ("supp_rule3|S1", 5)]
    for nm, s in checks:
        _, _, rec, _ = run39((nm, cf[nm], s))
        conv, _ = convert(c39[f"{nm}#caution"][s], c39[f"{nm}#S"][s], c39[f"{nm}#exposed"][s], 3000)
        same_inc = np.array_equal(rec["incidence"], c39[f"{nm}#incidence"][s])
        print(f"  rerun {nm} seed {s}: incidence identical {same_inc}; converted caution == fixed-code "
              f"caution {np.array_equal(np.nan_to_num(conv, nan=-1), np.nan_to_num(rec['caution'], nan=-1))}")
    worst, nchg, rows = 0.0, 0, {}
    print("config | DR mean old -> new | n defined old -> new | max |DR change| per run")
    for nm in names:
        conv, resid = [], 0.0
        for s in range(30):
            c, r_ = convert(c39[f"{nm}#caution"][s], c39[f"{nm}#S"][s], c39[f"{nm}#exposed"][s], 3000)
            conv.append(c); resid = max(resid, r_)
        conv = np.array(conv)
        act = c39[f"{nm}#exposed"] + c39[f"{nm}#prevalence"]
        old = death_resp(c39[f"{nm}#awareness_signal"], c39[f"{nm}#caution"], act)
        new = death_resp(c39[f"{nm}#awareness_signal"], conv, act)
        both = np.isfinite(old) & np.isfinite(new)
        d = float(np.max(np.abs(old[both] - new[both]))) if both.any() else 0.0
        worst = max(worst, d)
        nchg += int((np.isfinite(old) != np.isfinite(new)).sum())
        rows[nm] = dict(old_mean=float(np.nanmean(old)) if np.isfinite(old).any() else None,
                        new_mean=float(np.nanmean(new)) if np.isfinite(new).any() else None,
                        old_n=int(np.isfinite(old).sum()), new_n=int(np.isfinite(new).sum()),
                        max_change=d, max_count_residual=resid)
        f = lambda x: "undef" if x is None else f"{x:+.6f}"  # noqa: E731
        print(f"  {nm} | {f(rows[nm]['old_mean'])} -> {f(rows[nm]['new_mean'])} | {rows[nm]['old_n']} -> "
              f"{rows[nm]['new_n']} | {d:.2e} (count residual {resid:.1e})")
    print(f"C39: largest per-run DR change {worst:.2e}; runs changing defined/undefined {nchg}")
    json.dump(dict(rows=rows, worst=worst, n_def_changes=nchg), open(os.path.join(OUT, "step8_e24.json"), "w"),
              indent=1)


# ------------------------------------------------------------------ 8d: revised E26 (i)

def signal28(deaths, detection=0.7, window=28):
    rep = detection * np.asarray(deaths, float)
    c = np.concatenate([[0.0], np.cumsum(rep)])
    t = np.arange(len(rep))
    lo = np.maximum(0, t - window)
    out = np.where(t > 0, (c[t] - c[lo]) / np.maximum(t - lo, 1), 0.0)
    return out


def lag_dr(sig, caution, active):
    from scipy.stats import spearmanr
    best, best_l, n_def = np.nan, None, 0
    T = len(sig)
    for L in LAGS:
        t = np.arange(max(0, -L), min(T, T - L))
        m = active[t] & active[t + L] & np.isfinite(caution[t + L])
        x, y = sig[t][m], caution[t + L][m]
        if m.sum() < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
            continue
        n_def += 1
        rho = float(spearmanr(x, y)[0])
        if not np.isfinite(best) or rho > best:
            best, best_l = rho, L
    return best, best_l


def per_run_rev(sig, caution, prev, exp_, S):
    from step5_arm3_runs import death_resp
    active = (exp_ + prev) > 0
    dr0 = death_resp(sig, caution, exp_ + prev)
    res = [lag_dr(s_, c_, a_) for s_, c_, a_ in zip(sig, caution, active)]
    drL = np.array([r[0] for r in res])
    lagL = [r[1] for r in res]
    sd = []
    for c, ac in zip(caution, active):
        m = ac & np.isfinite(c)
        sd.append(float(np.std(c[m], ddof=1)) if m.sum() >= 2 else np.nan)
    sd = np.array(sd)
    attack = 1 - S[:, -1]
    ok = lambda v, th: np.isfinite(v) & (np.nan_to_num(v, nan=-9) >= th)  # noqa: E731
    i0, iL, ii, iii = ok(dr0, rp.DR_MIN), ok(drL, rp.DR_MIN), ok(sd, rp.SD_MIN), attack >= rp.ATTACK_MIN
    n = len(S)
    lags_def = [l_ for l_ in lagL if l_ is not None]
    return dict(n=n, drL_mean=float(np.nanmean(drL)) if np.isfinite(drL).any() else None,
                drL_median=float(np.nanmedian(drL)) if np.isfinite(drL).any() else None,
                drL_defined=int(np.isfinite(drL).sum()),
                lag_median=float(np.median(lags_def)) if lags_def else None,
                lag_range=[min(lags_def), max(lags_def)] if lags_def else None,
                dr0_mean=float(np.nanmean(dr0)) if np.isfinite(dr0).any() else None,
                dr0_defined=int(np.isfinite(dr0).sum()),
                sd_mean=float(np.nanmean(sd)) if np.isfinite(sd).any() else None,
                attack_mean=float(attack.mean()),
                pass_iL=int(iL.sum()), pass_i0=int(i0.sum()), pass_ii=int(ii.sum()), pass_iii=int(iii.sum()),
                all_rev=int((iL & ii & iii).sum()), all_orig=int((i0 & ii & iii).sum()),
                verdict_rev="PASS" if (iL & ii & iii).sum() > n / 2 else "FAIL",
                verdict_orig="PASS" if (i0 & ii & iii).sum() > n / 2 else "FAIL")


def e26():
    cases = []
    rpc = dict(np.load(rp.CACHE))

    def old(prefix, seeds, n):
        g = lambda k: np.array([rpc[f"{prefix}{s}#{k}"] for s in seeds])  # noqa: E731
        S, E, I = g("S"), g("exposed"), g("prevalence")
        c = np.array([convert(cc, ss, ee, n)[0] for cc, ss, ee in zip(g("caution"), S, E)])
        return g("awareness_signal"), c, I, E, S
    cases.append(("SHOULD PASS: Weitz rule N = 30,000 (C43 step B)", old("c43|", range(10), 30_000)))
    cases.append(("SHOULD FAIL: C31 ceiling (a) S1", old("ceil|S1|", range(30), 3000)))
    cases.append(("SHOULD FAIL: C31 ceiling (c) S2", old("ceil|S2|", range(30), 3000)))
    c39 = dict(np.load(C39_CACHE))

    def g39(nm):
        S, E, I = c39[f"{nm}#S"], c39[f"{nm}#exposed"], c39[f"{nm}#prevalence"]
        c = np.array([convert(cc, ss, ee, 3000)[0] for cc, ss, ee in zip(c39[f"{nm}#caution"], S, E)])
        return c39[f"{nm}#awareness_signal"], c, I, E, S
    for sc in rp.SCEN:
        cases.append((f"SHOULD FAIL: C39 rule 2, {sc}", g39(f"rule2|{sc}")))
    for sc in rp.SCEN:
        cases.append((f"info: arm 1, {sc}", g39(f"arm1|{sc}")))
    for k in (1, 3, 4, 5):
        for sc in rp.SCEN:
            cases.append((f"info: rule {k}, {sc}", g39(f"rule{k}|{sc}")))
    b = dict(np.load(cp.CACHE))

    def g45(kind, n, f):
        g = lambda k: np.array([b[f"{kind}|{n}|{f}|{s}#{k}"] for s in cp.SEEDS])  # noqa: E731
        S, E, I = g("S"), g("exposed"), g("prevalence")
        c = np.array([convert(cc, ss, ee, n)[0] for cc, ss, ee in zip(g("caution"), S, E)])
        return g("awareness_signal"), c, I, E, S
    for f in cp.F_D_LIST:
        cases.append((f"info: C45 1a step B, f_D {f}", g45("B", cp.N3K, f)))
    cases.append(("info: C45 1a step C, f_D 0.1", g45("C", cp.N3K, 0.1)))
    for n in cp.SIZES_1B:
        cases.append((f"info: C45 1b step B, N = {n:,}", g45("B", n, None)))
    a = dict(np.load(CACHE))
    chk = []
    for label, kind, n, f, w, _ in cases_8():
        g = lambda k: np.array([a[f"{kind}|{n}|{f}|{w}|{s}#{k}"] for s in SEEDS])  # noqa: E731
        # Recomputed signal: rounded to 12 decimals so summation-order noise (~1e-15) cannot split
        # rank ties. 28-day runs use the world's own signal; the recomputation is only checked
        # there, on active days (the world stops updating its signal after a run ends).
        sig = np.round(np.array([signal28(d) for d in g("deaths")]), 12)
        act = (g("exposed") + g("prevalence")) > 0
        if w == 28:
            chk.append(bool(np.allclose(sig[act], g("awareness_signal")[act], rtol=0, atol=1e-12)))
            sig = g("awareness_signal")
        cases.append((f"info: {label}", (sig, g("caution"), g("prevalence"), g("exposed"), g("S"))))
    print(f"signal28 recomputed from deaths == world awareness_signal on active days (28-day runs): "
          f"{sum(chk)}/{len(chk)} cases")
    print("case | n | max-lag DR mean / median (n def) | best lag median [range] | lag-0 DR mean (n def) | "
          "caution SD | attack | runs meeting (i-rev) / (i-orig) / (ii) / (iii) | all rev / orig | verdict rev (orig)")
    out = {}
    fm = lambda x: "undef" if x is None else f"{x:+.3f}"  # noqa: E731
    for label, data in cases:
        r = per_run_rev(*data)
        out[label] = r
        print(f"{label} | {r['n']} | {fm(r['drL_mean'])} / {fm(r['drL_median'])} ({r['drL_defined']}) | "
              f"{r['lag_median']} {r['lag_range']} | {fm(r['dr0_mean'])} ({r['dr0_defined']}) | "
              f"{'undef' if r['sd_mean'] is None else format(r['sd_mean'], '.3f')} | {r['attack_mean']:.3f} | "
              f"{r['pass_iL']} / {r['pass_i0']} / {r['pass_ii']} / {r['pass_iii']} | {r['all_rev']} / {r['all_orig']} | "
              f"{r['verdict_rev']} ({r['verdict_orig']})")
    json.dump(out, open(os.path.join(OUT, "step8_e26.json"), "w"), indent=1)


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--ode", step_ode), ("--timing", timing), ("--sim", simulate), ("--score", score),
                     ("--e24", e24), ("--e26", e26)):
        if flag in sys.argv:
            fn()
