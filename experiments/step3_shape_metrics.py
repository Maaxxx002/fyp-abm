"""
Step 3 Phase 1 (register C29): validate candidate shape metrics on KNOWN cases only.
No arm is scored here.

Known cases (600 days, daily INCIDENCE = new infections/day as the primary series):
  K1  Weitz model B ODE (seirdelay_plat in Weitz's own code, jsweitz/covid19-git-plateaus):
      R0=3 (beta 0.5, latent 2 d, infectious 6 d), T_H=14, f_D=0.01, initial E = 1/N, N=1e7.
      (a) no behaviour; (b) g = 1/(1+(delta/delta_c)^k), delta = gamma_H*H, N*delta_c = 50,
      k = 2 (figseir_Hdel_k2.m / figseir_Hlong_k2D.m: pars.awareness = 2, Dcrit = 0.5e-5).
  K2  Weitz-rule ABM, N=100,000, seeds 0-29: run_weitz_behaviour (continuous-q, delta_c=0.5,
      k=2 = C11/Test 2) and its no-behaviour control run() on the same seeds.
  K3  No-behaviour ABM, N=3,000, seeds 0-29: run() with per-agent f_D (A26), 48 sub-steps.

Candidate metrics (plateau direction in brackets):
  M1  EpidemicKabu 0.2.7 number of waves = len(cutDatesW) + 1, library pipeline exactly as
      waves.run() minus its CSV/plot output; kernel 18 (the library's built-in fallback),
      fbi 0 (signature default)  [more waves; direction = operationalisation agreed with Max]
  M2  Hoen et al. 2015 two-peak metric, Multimedia Appendix eq. S1:
      TP(S) = max_{i<j} sqrt((s_i - v_ij)(s_j - v_ij)), v_ij = min_{i<=k<=j} s_k, applied to
      per-capita incidence so N=3,000 / 100,000 / ODE share units; no tunables  [higher]
  M3  T10-90: days between 10% and 90% of the run's final cumulative incidence  [longer]
  M4  max daily incidence / mean daily incidence over the T10-90 window  [lower]
  SA  symmetry coefficient as implemented in experiments/metrics.py (sym_pt: centred 7-day
      moving average, cutoff*peak / value at t_P + dt)  [lower]
  SB  symmetry coefficient per Weitz's own R code (deaths/national_deaths_metric.R): drop zero
      days, loess(log y ~ day) with R defaults span 0.75 / degree 2, predict on a grid,
      D_l / D_r at the 10% cutoff. APPROXIMATION: direct tricube local-quadratic fit, not R's
      default kd-tree "interpolate" surface, and a 0.1-day grid instead of 0.01  [lower]
  M5  averaged curve: align each run at the first day cumulative incidence >= 1% of N,
      average the per-capita aligned curves over the common window, then M3/M4/SA/SB on it,
      with a 1,000-resample bootstrap over runs (95% percentile interval).

Pass criteria P1-P4 (fixed by the planning chat before running) are evaluated in score().

Usage:  python experiments/step3_shape_metrics.py --timing    (one seed per config)
        python experiments/step3_shape_metrics.py --simulate  (runs + caches the series)
        python experiments/step3_shape_metrics.py             (stage 1: P1-P3, default settings)
        python experiments/step3_shape_metrics.py --stage2    (stage 2: P4 variants only for
               metric/kind pairs passing P1-P3; stops if upper-end projection > 10 min unless --go)
"""
import json
import multiprocessing as mp
import os
import sys
import time
import warnings

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from model import run, run_weitz_behaviour  # noqa: E402
from population import build_population  # noqa: E402

OUT = os.path.join(ROOT, "results", "step3")
CACHE = os.path.join(OUT, "sim_series.npz")
STAGE1 = os.path.join(OUT, "stage1.json")
STAGE2 = os.path.join(OUT, "stage2.json")
DAYS = 600
SEEDS = list(range(30))
N_K2, N_K3 = 100_000, 3_000
N_BOOT = 1000
BOOT_SEED = 20261004

# ---------------------------------------------------------------- simulation

def _sim(args):
    case, seed = args
    t0 = time.time()
    if case == "K2_beh":
        out = run_weitz_behaviour(N=N_K2, seed=seed, days=DAYS, delta_c=0.5, k=2)
    elif case == "K2_ctrl":
        out = run(N=N_K2, seed=seed, days=DAYS)
    else:
        out = run(N=N_K3, seed=seed, days=DAYS,
                  f_D=build_population(N=N_K3, seed=0).vulnerability)
    return case, seed, out["incidence"], time.time() - t0


def simulate(seeds):
    tasks = [(c, s) for c in ("K2_beh", "K2_ctrl", "K3") for s in seeds]
    res = {c: [None] * len(seeds) for c in ("K2_beh", "K2_ctrl", "K3")}
    times = {}
    with mp.Pool(min(16, len(tasks))) as pool:
        for case, seed, inc, dt in pool.imap_unordered(_sim, tasks):
            res[case][seeds.index(seed)] = inc
            times.setdefault(case, []).append(dt)
    return {k: np.array(v) for k, v in res.items()}, times


def weitz_ode(behaviour, days=DAYS, N=1e7, k=2, Ndc=50.0, T_H=14.0):
    """Weitz model B (seirdelay_plat.m), per-capita. Returns daily incidence and deaths,
    integrated over each day (S(t)-S(t+1), D(t+1)-D(t))."""
    from scipy.integrate import solve_ivp
    beta, mu, gamma, fD, gH = 0.5, 1 / 2, 1 / 6, 0.01, 1 / T_H
    dc = Ndc / N

    def rhs(t, y):
        S, E, I, R, H, D = y
        g = 1.0 / (1.0 + (gH * H / dc) ** k) if behaviour else 1.0
        foi = beta * S * I * g
        return [-foi, foi - mu * E, mu * E - gamma * I, gamma * I * (1 - fD),
                gamma * I * fD - gH * H, gH * H]

    y0 = [1 - 1 / N, 1 / N, 0, 0, 0, 0]
    sol = solve_ivp(rhs, [0, days], y0, t_eval=np.arange(days + 1), rtol=1e-10, atol=1e-14,
                    method="LSODA")
    S, D = sol.y[0], sol.y[5]
    return S[:-1] - S[1:], D[1:] - D[:-1]

# ---------------------------------------------------------------- metrics

def kabu_n_waves(y, kernel=18):
    import pandas as pd
    from epidemickabu.kabu import curves
    from epidemickabu.kabuWaves import waves
    warnings.filterwarnings("ignore")
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=len(y)).strftime("%Y-%m-%d"),
                       "cases": np.asarray(y, float)})
    w = waves(df, "date", "cases", kernel, "x", "x", fbi=0)
    curves.run(w)
    w.idenCutPointsW("FirstDerivateSmoothed", "rollingFDS")
    w.idenPreviousDatesW("rollingFDS", "FirstDerivateSmoothed")
    w.filteOnInfectionItself()
    return float(len(w.cutDatesW) + 1)


def two_peak(y):
    """Hoen et al. 2015, eq. S1."""
    s = np.asarray(y, float)
    best = 0.0
    for i in range(len(s) - 1):
        v = np.minimum.accumulate(s[i:])          # v_ij for j >= i
        prod = (s[i] - v[1:]) * (s[i + 1:] - v[1:])
        if len(prod):
            best = max(best, float(np.sqrt(max(prod.max(), 0.0))))
    return best


def t_window(y, lo=0.10, hi=0.90):
    c = np.cumsum(np.asarray(y, float))
    if c[-1] <= 0:
        return None
    return int(np.searchsorted(c, lo * c[-1])), int(np.searchsorted(c, hi * c[-1]))


def duration(y, lo=0.10, hi=0.90):
    w = t_window(y, lo, hi)
    return np.nan if w is None else float(w[1] - w[0])


def peak_to_mean(y, lo=0.10, hi=0.90):
    w = t_window(y, lo, hi)
    if w is None:
        return np.nan
    y = np.asarray(y, float)
    m = y[w[0]:w[1] + 1].mean()
    return float(y.max() / m) if m > 0 else np.nan


def _movavg(x, w):
    """experiments/metrics.py's sm(), with the window as a parameter."""
    x = np.asarray(x, float)
    if len(x) < w:
        return x
    k = np.ones(w) / w
    return np.convolve(np.pad(x, (w // 2, w // 2), mode="edge"), k, mode="valid")[:len(x)]


def sym_a(y, window=7, cutoff=0.1):
    """experiments/metrics.py sym_pt, parameterised. Undefined (nan) if no pre-peak cutoff
    crossing, if t_P + dt runs past the series, or if the post value is 0 (metrics.py gives
    inf there)."""
    ys = _movavg(y, window)
    if ys.max() <= 0:
        return np.nan
    ip = int(ys.argmax()); pk = ys[ip]
    pre = np.nonzero(ys[:ip] <= cutoff * pk)[0]
    if not len(pre) or ip + (ip - pre[-1]) >= len(ys):
        return np.nan
    post = ys[ip + (ip - pre[-1])]
    return float(cutoff * pk / post) if post > 0 else np.nan


def loess_direct(x, y, xq, span=0.75, degree=2, chunk=2000):
    n = len(x)
    out = np.empty(len(xq))
    q = int(np.floor(n * span))
    for a in range(0, len(xq), chunk):
        x0 = xq[a:a + chunk][:, None]
        u = x[None, :] - x0
        d = np.abs(u)
        if span < 1:
            h = np.partition(d, q - 1, axis=1)[:, q - 1]
        else:
            h = d.max(axis=1) * span
        w = np.clip(1 - (d / h[:, None]) ** 3, 0, None) ** 3
        M = np.stack([np.stack([(w * u ** (r + c)).sum(1) for c in range(degree + 1)], -1)
                      for r in range(degree + 1)], -2)
        b = np.stack([(w * u ** r * y[None, :]).sum(1) for r in range(degree + 1)], -1)
        out[a:a + chunk] = np.linalg.solve(M, b[..., None])[:, 0, 0]
    return out


def sym_b(y, span=0.75, cutoff=0.1, grid=0.1):
    y = np.asarray(y, float)
    day = np.arange(len(y), dtype=float)
    keep = y > 0
    if keep.sum() < 4:
        return np.nan
    x, ly = day[keep], np.log(y[keep])
    pp = np.arange(x.min(), x.max() + 1e-9, grid)
    pred = np.exp(loess_direct(x, ly, pp, span))
    DP = pred.max(); tP = pp[pred.argmax()]
    left = np.nonzero((pred <= cutoff * DP) & (pp < tP))[0]
    if not len(left):
        return np.nan
    ww = left[-1]
    right = np.nonzero(pp >= tP + (tP - pp[ww]))[0]
    if not len(right):
        return np.nan
    return float(pred[ww] / pred[right[0]])


# name -> (function, default kwargs, P4 variants, plateau direction: -1 lower / +1 higher)
METRICS = {
    "M1_kabu_waves": (kabu_n_waves, dict(kernel=18), [dict(kernel=9), dict(kernel=36)], +1),
    "M2_two_peak": (two_peak, {}, [], +1),
    "M3_duration": (duration, dict(lo=0.10, hi=0.90),
                    [dict(lo=0.05, hi=0.95), dict(lo=0.20, hi=0.80)], +1),
    "M4_peak_to_mean": (peak_to_mean, dict(lo=0.10, hi=0.90),
                        [dict(lo=0.05, hi=0.95), dict(lo=0.20, hi=0.80)], -1),
    "SA_sym_metricspy": (sym_a, dict(window=7, cutoff=0.1),
                         [dict(window=4, cutoff=0.1), dict(window=14, cutoff=0.1),
                          dict(window=7, cutoff=0.05), dict(window=7, cutoff=0.2)], -1),
    "SB_sym_weitz_loess": (sym_b, dict(span=0.75, cutoff=0.1),
                           [dict(span=0.375, cutoff=0.1), dict(span=1.5, cutoff=0.1),
                            dict(span=0.75, cutoff=0.05), dict(span=0.75, cutoff=0.2)], -1),
}
PER_RUN = list(METRICS)
AVERAGED = ["M3_duration", "M4_peak_to_mean", "SA_sym_metricspy", "SB_sym_weitz_loess"]
ALIGN_DEFAULT, ALIGN_VARIANTS = 0.01, [0.005, 0.02]


def _apply(args):
    name, kw, y = args
    return METRICS[name][0](y, **kw)


def align_average(series, N, frac):
    """Per-capita curves aligned at the first day cumulative incidence >= frac*N; mean over
    the common window. Returns (mean curve, aligned curves, n used)."""
    starts, kept = [], []
    for y in series:
        c = np.cumsum(y)
        hit = np.nonzero(c >= frac * N)[0]
        if len(hit):
            starts.append(int(hit[0])); kept.append(np.asarray(y, float) / N)
    L = DAYS - max(starts)
    aligned = np.array([y[s:s + L] for y, s in zip(kept, starts)])
    return aligned.mean(0), aligned, len(kept)

# ---------------------------------------------------------------- scoring

def mean_sem(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.nan, np.nan, len(x)
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def closer_to_ctrl(v, ode_c, ode_b):
    return bool(np.isfinite(v) and abs(v - ode_c) < abs(v - ode_b))


def right_dir(beh, ctrl, sign):
    return bool(np.isfinite(beh) and np.isfinite(ctrl) and np.sign(beh - ctrl) == sign)


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--timing" in sys.argv:
        _, times = simulate([0])
        for k, v in times.items():
            print(f"  {k:8s} seed 0: {v[0]:.1f}s")
        t0 = time.time(); kabu_n_waves(np.random.default_rng(0).poisson(5, DAYS)); tk = time.time() - t0
        t0 = time.time(); sym_b(np.random.default_rng(0).poisson(5, DAYS)); tl = time.time() - t0
        print(f"  EpidemicKabu one call {tk:.1f}s; Weitz-LOESS one call {tl:.2f}s")
        return
    if "--simulate" in sys.argv:
        t0 = time.time()
        sims, _ = simulate(SEEDS)
        np.savez_compressed(CACHE, **sims)
        print(f"Simulated {len(SEEDS)} seeds x 3 cases in {(time.time()-t0)/60:.1f} min -> {CACHE}")
        return

    stage = 2 if "--stage2" in sys.argv else 1
    sims = dict(np.load(CACHE))
    ode_inc = {b: weitz_ode(b)[0] for b in (False, True)}
    ode_dth = {b: weitz_ode(b)[1] for b in (False, True)}
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    ctx = dict(sims=sims, ode_inc=ode_inc, ode_dth=ode_dth, boot_idx=boot_idx)

    if stage == 1:
        report = {"stage": 1, "ode_check": {}, "metrics": {}}
        print("=== K1 ODE: symmetry coefficients (incidence / deaths) ===")
        for nm in ("SA_sym_metricspy", "SB_sym_weitz_loess"):
            f, kw = METRICS[nm][0], METRICS[nm][1]
            vals = {f"{ser}_{lab}": f(d[b], **kw) for ser, d in (("inc", ode_inc), ("deaths", ode_dth))
                    for lab, b in (("ctrl", False), ("beh", True))}
            report["ode_check"][nm] = vals
            print(f"  {nm}: " + ", ".join(f"{k} {v:.3f}" for k, v in vals.items()))
        with mp.Pool(16) as pool:
            ctx["pool"] = pool
            for name in METRICS:
                f, kw0, _, sign = METRICS[name]
                print(f"\n=== {name} (plateau = {'higher' if sign > 0 else 'lower'}) ===")
                s0 = score_setting(ctx, name, kw0, ALIGN_DEFAULT, True, name in AVERAGED)
                rec = {"direction": "higher" if sign > 0 else "lower", "default": s0}
                for kind in ("per_run",) + (("avg",) if name in AVERAGED else ()):
                    v = dict(P1=s0["P1"], P2=s0[f"P2_{kind}"], P3=s0[f"P3_{kind}"])
                    v["P1_P3"] = all(v.values())
                    rec[f"stage1_{kind}"] = v
                    print(f"  STAGE 1 {name} [{kind}]: {v}")
                report["metrics"][name] = rec
        json.dump(report, open(STAGE1, "w"), indent=2, default=_json)
        figures(sims, ode_inc, boot_idx)
        print(f"\nWrote {STAGE1} and figures in {OUT}")
        return

    # ---------------- stage 2: P4 only for metric/kind pairs that passed P1-P3
    st1 = json.load(open(STAGE1))
    todo = []
    for name, rec in st1["metrics"].items():
        _, kw0, variants, _ = METRICS[name]
        for kind in ("per_run", "avg"):
            if rec.get(f"stage1_{kind}", {}).get("P1_P3"):
                combos = [(kw, ALIGN_DEFAULT) for kw in variants]
                if kind == "avg":
                    combos += [(kw0, a) for a in ALIGN_VARIANTS]
                todo.append((name, kind, combos))
    per_call = {"M1_kabu_waves": 5.5, "SB_sym_weitz_loess": 0.86}   # measured (--timing)
    cpu = sum(len(c) * (90 if kind == "per_run" else 2 * N_BOOT + 3) * per_call.get(n, 0.02)
              for n, kind, c in todo)
    print("Stage 2 work: " + ("; ".join(f"{n}[{k}] {len(c)} variants" for n, k, c in todo) or "none"))
    print(f"Projected CPU {cpu/60:.1f} min; wall-clock ideal {cpu/16/60:.1f} min, "
          f"upper end (x4 parallel slowdown) {4*cpu/16/60:.1f} min")
    if 4 * cpu / 16 / 60 > 10 and "--go" not in sys.argv:
        print("STOP: upper-end projection > 10 min. Re-run with --go once approved.")
        return
    report = {"stage": 2, "metrics": {}}
    with mp.Pool(16) as pool:
        ctx["pool"] = pool
        for name, kind, combos in todo:
            d0 = st1["metrics"][name]["default"]
            base = (d0["P1"], d0[f"P2_{kind}"], d0[f"P3_{kind}"])
            rows = []
            print(f"\n=== {name} [{kind}] P4 variants ===")
            for kw, align in combos:
                s = score_setting(ctx, name, kw, align, kind == "per_run", kind == "avg")
                t = (s["P1"], s[f"P2_{kind}"], s[f"P3_{kind}"])
                s["verdicts_same_as_default"] = t == base
                rows.append(s)
            p4 = all(r["verdicts_same_as_default"] for r in rows)
            report["metrics"].setdefault(name, {})[kind] = dict(variants=rows, P4=p4)
            print(f"  P4 {name} [{kind}]: {p4}")
    json.dump(report, open(STAGE2, "w"), indent=2, default=_json)
    print(f"\nWrote {STAGE2}")


def _json(o):
    return o.tolist() if hasattr(o, "tolist") else str(o)


def score_setting(ctx, name, kw, align, do_per_run, do_avg):
    """P1 (ODE), and P2/P3 per-run and/or averaged-curve, for one metric setting."""
    f, _, _, sign = METRICS[name]
    sims, pool, boot_idx = ctx["sims"], ctx["pool"], ctx["boot_idx"]
    ode_c, ode_b = f(ctx["ode_inc"][False], **kw), f(ctx["ode_inc"][True], **kw)
    s = {"kw": kw, "align": align, "ode_inc": dict(ctrl=ode_c, beh=ode_b),
         "ode_deaths": dict(ctrl=f(ctx["ode_dth"][False], **kw), beh=f(ctx["ode_dth"][True], **kw)),
         "P1": right_dir(ode_b, ode_c, sign)}
    gap = abs(ode_b - ode_c)
    line = f"  {kw} align={align}: ODE inc ctrl {ode_c:.4g} beh {ode_b:.4g} P1={s['P1']}"
    if do_per_run:
        pr = {}
        for case in ("K2_beh", "K2_ctrl", "K3"):
            scale = N_K2 if case.startswith("K2") else N_K3
            ys = sims[case] / scale if name == "M2_two_peak" else sims[case]
            pr[case] = np.array(pool.map(_apply, [(name, kw, y) for y in ys]))
        nb, nc = int(np.isfinite(pr["K2_beh"]).sum()), int(np.isfinite(pr["K2_ctrl"]).sum())
        dm, dse, dn = mean_sem(pr["K2_beh"] - pr["K2_ctrl"])
        z = dm / dse if (np.isfinite(dse) and dse > 0) else (np.inf * np.sign(dm) if dm else 0.0)
        k3m, k3se, k3n = mean_sem(pr["K3"])
        k3sd = float(np.nanstd(pr["K3"], ddof=1)) if k3n > 1 else np.nan
        s["per_run"] = dict(K2_beh=mean_sem(pr["K2_beh"]), K2_ctrl=mean_sem(pr["K2_ctrl"]),
                            n_defined=dict(K2_beh=nb, K2_ctrl=nc, K3=k3n, total=len(SEEDS)),
                            paired=dict(mean=dm, sem=dse, n=dn, sems=float(z)),
                            K3=(k3m, k3se, k3n), K3_sd=k3sd,
                            K3_sd_over_gap=k3sd / gap if gap > 0 else np.nan,
                            values={k: v.tolist() for k, v in pr.items()})
        s["P2_per_run"] = bool(nb == nc == len(SEEDS) and np.sign(dm) == sign and abs(z) > 2)
        s["P3_per_run"] = closer_to_ctrl(k3m, ode_c, ode_b)
        p = s["per_run"]
        line += (f"\n    per-run: n defined beh {nb}/30, ctrl {nc}/30, K3 {k3n}/30; "
                 f"K2 beh {p['K2_beh'][0]:.4g}, ctrl {p['K2_ctrl'][0]:.4g}; paired "
                 f"{dm:+.4g} +/- {dse:.3g} ({z:+.2f} SEM) P2={s['P2_per_run']}; K3 mean "
                 f"{k3m:.4g} (SD {k3sd:.3g} = {p['K3_sd_over_gap']:.2f} x ODE gap) P3={s['P3_per_run']}")
    if do_avg:
        av = {}
        for case in ("K2_beh", "K2_ctrl", "K3"):
            N = N_K2 if case.startswith("K2") else N_K3
            m, aligned, n_used = align_average(sims[case], N, align)
            entry = dict(value=f(m, **kw), n_used=n_used, length=int(aligned.shape[1]))
            if case.startswith("K2"):
                bvals = np.array(pool.map(_apply, [(name, kw, aligned[idx].mean(0))
                                                   for idx in boot_idx]))
                fin = bvals[np.isfinite(bvals)]
                entry["boot_ci"] = (tuple(np.percentile(fin, [2.5, 97.5])) if len(fin)
                                    else (np.nan, np.nan))
                entry["boot_n_defined"] = int(len(fin))
            av[case] = entry
        lo_b, hi_b = av["K2_beh"]["boot_ci"]; lo_c, hi_c = av["K2_ctrl"]["boot_ci"]
        overlap = not (hi_b < lo_c or hi_c < lo_b)
        s["averaged"] = av
        s["P2_avg"] = bool(right_dir(av["K2_beh"]["value"], av["K2_ctrl"]["value"], sign)
                           and not overlap and av["K2_beh"]["boot_n_defined"] == N_BOOT
                           and av["K2_ctrl"]["boot_n_defined"] == N_BOOT)
        s["P3_avg"] = bool(closer_to_ctrl(av["K2_ctrl"]["value"], ode_c, ode_b)
                           and closer_to_ctrl(av["K3"]["value"], ode_c, ode_b))
        a = av
        line += (f"\n    averaged (n used beh {a['K2_beh']['n_used']}, ctrl {a['K2_ctrl']['n_used']}, "
                 f"K3 {a['K3']['n_used']} of 30): beh {a['K2_beh']['value']:.4g} "
                 f"CI {np.round(a['K2_beh']['boot_ci'], 4)} (boot defined "
                 f"{a['K2_beh']['boot_n_defined']}/{N_BOOT}), ctrl {a['K2_ctrl']['value']:.4g} "
                 f"CI {np.round(a['K2_ctrl']['boot_ci'], 4)} ({a['K2_ctrl']['boot_n_defined']}/{N_BOOT}), "
                 f"K3 {a['K3']['value']:.4g}; P2={s['P2_avg']} P3={s['P3_avg']}")
    print(line, flush=True)
    return s


# ---------------------------------------------------------------- figures

BEH, CTRL = "#2a78d6", "#eb6834"      # dataviz reference palette, categorical slots 1-2
INK, INK2, SURF = "#0b0b0b", "#52514e", "#fcfcfb"


def _style(ax, title):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(INK2)
    ax.tick_params(colors=INK2)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.set_title(title, color=INK, loc="left", fontsize=11)
    ax.set_xlabel("days since cumulative incidence reached 1% of N", color=INK2)
    ax.set_ylabel("new infections per 1,000 people per day", color=INK2)


def figures(sims, ode_inc, boot_idx):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def ode_aligned(b):
        y = ode_inc[b]; c = np.cumsum(y); s = int(np.nonzero(c >= ALIGN_DEFAULT)[0][0])
        return y[s:] * 1000

    # K1
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURF)
    for b, col, lab in ((True, BEH, "behaviour (Weitz rule, k=2)"), (False, CTRL, "no behaviour")):
        y = ode_aligned(b); ax.plot(np.arange(len(y)), y, color=col, lw=2, label=lab)
        ax.annotate(lab, (np.argmax(y), y.max()), xytext=(6, 4), textcoords="offset points",
                    color=INK2, fontsize=8)
    _style(ax, "K1 - Weitz model B ODE (aligned at 1% cumulative incidence)")
    ax.set_xlim(0, 300); ax.legend(frameon=False, labelcolor=INK2)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "K1_ode.png")); plt.close(fig)

    def panel(cases, N, fname, title, refs=False):
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURF)
        for case, col, lab in cases:
            m, aligned, n = align_average(sims[case], N, ALIGN_DEFAULT)
            m, aligned = m * 1000, aligned * 1000
            t = np.arange(len(m))
            for r in aligned[:5]:
                ax.plot(t, r, color=col, lw=0.6, alpha=0.25)
            bc = np.array([aligned[idx].mean(0) for idx in boot_idx])
            ax.fill_between(t, *np.percentile(bc, [2.5, 97.5], axis=0), color=col, alpha=0.25,
                            linewidth=0)
            ax.plot(t, m, color=col, lw=2, label=f"{lab} (mean of {n} runs, 95% bootstrap band)")
        if refs:
            for b, ls, lab in ((False, "--", "ODE no behaviour"), (True, ":", "ODE behaviour")):
                y = ode_aligned(b); ax.plot(np.arange(len(y)), y, color=INK2, lw=1.2, ls=ls, label=lab)
        _style(ax, title); ax.set_xlim(0, 300); ax.legend(frameon=False, labelcolor=INK2, fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(OUT, fname)); plt.close(fig)

    panel([("K2_beh", BEH, "behaviour (Weitz rule)"), ("K2_ctrl", CTRL, "no behaviour")], N_K2,
          "K2_abm_N100000.png", "K2 - Weitz-rule ABM, N=100,000, 30 seeds", refs=True)
    panel([("K3", CTRL, "no behaviour")], N_K3, "K3_abm_N3000.png",
          "K3 - no-behaviour ABM, N=3,000, 30 seeds (ODE references dashed/dotted)", refs=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
