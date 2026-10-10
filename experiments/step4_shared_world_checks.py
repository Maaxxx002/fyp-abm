"""
Step 4: checks on the shared world (register A37-A45; pre-registered in C31 before running).

Seed counts (option (b), C31): N=100,000 runs use seeds 0-9; N=3,000 runs use seeds 0-29.

Check 1  no behaviour: AlwaysNormal in run_shared_world vs model.run(), Test 1's setup
         (R0=3, f_D=0.01, 900 days) at N=100,000 and N=3,000, plus the N=3,000 600-day
         foundation controls. Pass = bit-identical.
Check 2  known-answer physics, N=100,000, 900 days (A32's mean-field convention):
           (a) S1, every never_ill agent forced into precautions from day 0
           (b) S1, a fixed random 50% of never_ill agents forced to stay home
           (c) S2, as (a)
         vs Weitz model B ODEs (see ode_final_S). Pass = final S within 1% relative error for
         (a) and (b); (c) is report-only (C31). Also run at N=3,000, 600 days, foundation
         population: ODE comparison reported, plus "ceiling" numbers vs own AlwaysNormal control.
Check 3  arm 1 (CBFArm1) in the shared world vs run_cbf_behaviour, S1/S2/S3, N=3,000, seeds
         0-29, 600 days, foundation. Pass = bit-identical (fallback: paired diffs within 2 SEM
         and stretch within C30's 95% CI).

Usage:  python experiments/step4_shared_world_checks.py --refs | --timing | (no flag: run all)
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
from scipy.integrate import solve_ivp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)
from model import run, run_cbf_behaviour  # noqa: E402
from population import build_population  # noqa: E402
from shared_world import (  # noqa: E402
    AlwaysNormal, CBFArm1, ForcedPrecautions, ForcedStayHomeFraction, run_shared_world,
)
import step3_shape_metrics as sm  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "step4")
SEEDS = list(range(30))
BOOT_SEED = 20261005          # C30's bootstrap seed, for comparability
N_BOOT = 1000
N_BIG, N_SMALL = 100_000, 3_000
SEEDS_INFECTED = 10
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
C30_CI = {"S1": (1.018, 1.158), "S2": (0.962, 1.704), "S3": (0.987, 1.057)}
HOME_FRACTION = 0.5
SERIES = ("S", "prevalence", "incidence", "deaths", "exposed")

_POP = {}


def _pop():
    if "p" not in _POP:
        _POP["p"] = build_population(N=N_SMALL, seed=0)
    return _POP["p"]


def ode_final_S(R0, mult=1.0, home=0.0, I0=1e-6, days=900, T_H=14.0,
                latent_period_days=2.0, infectious_period_days=6.0, f_D=0.01):
    """Weitz model B (Test 1's ODE) with transmission x mult on the exposed susceptibles and a
    fraction `home` of the initial susceptibles held in a compartment that cannot be infected.
    Returns total final S (home + exposed). f_D does not enter S."""
    b = R0 / infectious_period_days * mult
    lat, inf, th = 1 / latent_period_days, 1 / infectious_period_days, 1 / T_H

    def rhs(t, y):
        Sh, So, E, I, H, R, D = y
        f = b * So * I
        return [0.0, -f, f - lat * E, lat * E - inf * I, f_D * inf * I - th * H,
                (1 - f_D) * inf * I, th * H]

    s0 = 1 - I0
    y0 = [home * s0, (1 - home) * s0, 0, I0, 0, 0, 0]
    y = solve_ivp(rhs, [0, days], y0, max_step=0.5, rtol=1e-10, atol=1e-14).y[:, -1]
    return float(y[0] + y[1])


def references(N, days):
    """ODE references with the ABM's own initial condition I(0)=10/N (C31); Test 1's I(0)=1e-6
    reported alongside. (b): the never_ill agents held home, as a fraction of N (D15)."""
    I0 = SEEDS_INFECTED / N
    home = round(HOME_FRACTION * (N - SEEDS_INFECTED)) / N / (1 - I0)
    kw = dict(days=days)
    return {
        "a": dict(primary=ode_final_S(3.0, 0.5, I0=I0, **kw), test1_I0=ode_final_S(3.0, 0.5, **kw)),
        "b": dict(primary=ode_final_S(3.0, 1.0, home=home, I0=I0, **kw),
                  test1_I0=ode_final_S(3.0, 1.0, home=home, **kw),
                  stated_beta_x05=ode_final_S(3.0, 0.5, I0=I0, **kw)),
        "c": dict(primary=ode_final_S(2.0, 0.5, I0=I0, **kw), test1_I0=ode_final_S(2.0, 0.5, **kw)),
        "control_S1": dict(primary=ode_final_S(3.0, I0=I0, **kw), test1_I0=ode_final_S(3.0, **kw)),
    }


DECISIONS = {
    "normal": AlwaysNormal, "precautions": ForcedPrecautions,
    "home50": lambda: ForcedStayHomeFraction(HOME_FRACTION), "cbf": CBFArm1,
    "cbf_off": lambda: CBFArm1(beta_B=0.0),
}


def worker(task):
    """task = (config name, cfg, seed). cfg: engine, N, days, scen, decision, foundation."""
    name, cfg, seed = task
    sc = SCEN[cfg["scen"]]
    common = dict(N=cfg["N"], seed=seed, days=cfg["days"], seeds_infected=SEEDS_INFECTED,
                  R0=sc["R0"], T_H=sc["T_H"])
    # foundation: per-agent f_D (A26); Test 1 setup: flat 0.01. Signal: A24/A25 either way.
    common.update(f_D=_pop().vulnerability if cfg["foundation"] else 0.01)
    world = dict(window=28, detection_rate=0.7)
    t0 = time.time()
    if cfg["engine"] == "run":
        out = run(**common)
    elif cfg["engine"] == "run_cbf":
        out = run_cbf_behaviour(**common, **world, r=0.5, mu_B=0.01, gamma_beh=1.0,
                                beta_B=0.0 if cfg["decision"] == "cbf_off" else 0.5)
    else:
        out = run_shared_world(**common, **world, decision=DECISIONS[cfg["decision"]]())
    rec = dict(final_S=float(out["S"][-1]), peak_I=float(out["prevalence"].max()),
               series={k: np.asarray(out[k]) for k in SERIES if k in out})
    if "SB" in out:
        rec["series"]["SB"] = np.asarray(out["SB"])
    if "recovered" in out:
        rec["series"]["recovered"] = np.asarray(out["recovered"])
    return name, seed, rec, time.time() - t0


SEEDS_BIG = list(range(10))     # option (b): N=100,000 at 10 seeds (C31)


def configs():
    big = dict(N=N_BIG, days=900, foundation=False, seeds=SEEDS_BIG)
    t1_small = dict(N=N_SMALL, days=900, foundation=False, seeds=SEEDS)   # Test 1 setup, N=3,000
    small = dict(N=N_SMALL, days=600, foundation=True, seeds=SEEDS)
    c = {
        # Check 1
        "c1_run": dict(big, engine="run", scen="S1", decision=None),
        "c1_world": dict(big, engine="world", scen="S1", decision="normal"),
        "c1_run_N3000": dict(t1_small, engine="run", scen="S1", decision=None),
        "c1_world_N3000": dict(t1_small, engine="world", scen="S1", decision="normal"),
        "c1_run_ctrl_S1_N3000": dict(small, engine="run", scen="S1", decision=None),
        "c1_run_ctrl_S2_N3000": dict(small, engine="run", scen="S2", decision=None),
        # Check 2
        "c2a": dict(big, engine="world", scen="S1", decision="precautions"),
        "c2b": dict(big, engine="world", scen="S1", decision="home50"),
        "c2c": dict(big, engine="world", scen="S2", decision="precautions"),
        "c2a_N3000": dict(small, engine="world", scen="S1", decision="precautions"),
        "c2b_N3000": dict(small, engine="world", scen="S1", decision="home50"),
        "c2c_N3000": dict(small, engine="world", scen="S2", decision="precautions"),
        "ctrl_S1_N3000": dict(small, engine="world", scen="S1", decision="normal"),
        "ctrl_S2_N3000": dict(small, engine="world", scen="S2", decision="normal"),
    }
    for s in SCEN:
        c[f"c3_world_{s}"] = dict(small, engine="world", scen=s, decision="cbf")
        c[f"c3_cbf_{s}"] = dict(small, engine="run_cbf", scen=s, decision="cbf")
        c[f"c3_world_{s}_ctrl"] = dict(small, engine="world", scen=s, decision="cbf_off")
        c[f"c3_cbf_{s}_ctrl"] = dict(small, engine="run_cbf", scen=s, decision="cbf_off")
    return c


def pool_run(tasks):
    res, times = {}, {}
    with mp.Pool(min(os.cpu_count() or 1, 16)) as p:
        for name, seed, rec, dt in p.imap_unordered(worker, tasks):
            res.setdefault(name, {})[seed] = rec
            times.setdefault(name, []).append(dt)
    return res, times


def mean_sem(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return float(x.mean()) if len(x) else np.nan, np.nan, len(x)
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def identical(res, a, b, seeds, keys=("S", "prevalence", "incidence", "deaths")):
    return sum(all(np.array_equal(res[a][s]["series"][k], res[b][s]["series"][k]) for k in keys)
               for s in seeds)


def ceiling(res, arm, ctl, seeds, boot_idx):
    """C30/A36-style shape and safety-net numbers, arm vs own control (paired seeds)."""
    inc_a = np.array([res[arm][s]["series"]["incidence"] for s in seeds])
    inc_c = np.array([res[ctl][s]["series"]["incidence"] for s in seeds])
    m3a = np.array([sm.duration(y) for y in inc_a])
    m3c = np.array([sm.duration(y) for y in inc_c])
    ok = np.isfinite(m3a) & np.isfinite(m3c)
    a, c = m3a[ok], m3c[ok]
    if len(a) == len(seeds):
        idx = boot_idx                                    # C30's paired seed resamples
    elif len(a):
        idx = np.random.default_rng(BOOT_SEED).integers(0, len(a), size=(N_BOOT, len(a)))
    ratio = a.mean() / c.mean() if len(a) else np.nan
    boot = np.array([a[i].mean() / c[i].mean() for i in idx]) if len(a) else np.array([np.nan])
    per_seed = a / c
    with mp.Pool(16) as p:
        wa = np.array(p.map(sm.kabu_n_waves, list(inc_a)))
        wc = np.array(p.map(sm.kabu_n_waves, list(inc_c)))

    def active600(k):
        return int(sum(res[k][s]["series"]["exposed"][599] + res[k][s]["series"]["prevalence"][599] > 0
                       for s in seeds))

    pI = np.array([res[arm][s]["peak_I"] for s in seeds])
    pIc = np.array([res[ctl][s]["peak_I"] for s in seeds])
    fS = np.array([res[arm][s]["final_S"] for s in seeds])
    fSc = np.array([res[ctl][s]["final_S"] for s in seeds])
    dI, dS = mean_sem(pI - pIc), mean_sem(fS - fSc)
    last_active = [int(np.flatnonzero(res[arm][s]["series"]["exposed"]
                                      + res[arm][s]["series"]["prevalence"] > 0).max() + 1)
                   if np.any(res[arm][s]["series"]["exposed"] + res[arm][s]["series"]["prevalence"] > 0)
                   else 0 for s in seeds]
    return dict(
        n_seeds=len(seeds), m3_defined=dict(arm=int(np.isfinite(m3a).sum()),
                                            ctrl=int(np.isfinite(m3c).sum()), both=int(ok.sum())),
        m3_arm=mean_sem(m3a), m3_ctrl=mean_sem(m3c),
        m3_arm_median=float(np.nanmedian(m3a)), m3_arm_max=float(np.nanmax(m3a)),
        stretch_ratio_of_means=dict(value=float(ratio), ci=tuple(np.nanpercentile(boot, [2.5, 97.5]))),
        stretch_mean_per_seed=mean_sem(per_seed),
        stretch_median_per_seed=float(np.median(per_seed)) if len(per_seed) else np.nan,
        share_gt_1_5=dict(k=int((per_seed > 1.5).sum()), n=int(len(per_seed))),
        peak_I=dict(arm=mean_sem(pI), ctrl=mean_sem(pIc), paired=dI,
                    reduction_pct=float(-dI[0] / pIc.mean() * 100)),
        final_S=dict(arm=mean_sem(fS), ctrl=mean_sem(fSc), paired=dS),
        waves=dict(arm=mean_sem(wa), ctrl=mean_sem(wc), arm_counts=np.bincount(wa.astype(int)).tolist()),
        active_at_day600=dict(arm=active600(arm), ctrl=active600(ctl), n=len(seeds)),
        last_active_day_arm=dict(median=float(np.median(last_active)), max=int(max(last_active))),
    )


def main():
    if "--refs" in sys.argv:
        print(json.dumps(dict(N100000_900d=references(N_BIG, 900),
                              N3000_600d=references(N_SMALL, 600)), indent=2))
        return
    cfgs = configs()
    if "--timing" in sys.argv:
        t0 = time.time()
        res, times = pool_run([(k, v, s) for k, v in cfgs.items() for s in (0, 1)])
        wall = time.time() - t0
        print(f"timing wall {wall:.1f}s for {2 * len(cfgs)} runs")
        total_cpu_hi = 0.0
        for k, v in cfgs.items():
            hi = max(times[k])
            total_cpu_hi += hi * len(v["seeds"])
            print(f"  {k:20s} N={v['N']:>6} per run {min(times[k]):6.1f}-{hi:6.1f}s")
        print(f"upper-end projection: {total_cpu_hi:.0f} CPU-s -> {total_cpu_hi / 16 / 60:.1f} min "
              f"on 16 workers (+ EpidemicKabu); naive x15 of this timing wall: {wall * 15 / 60:.1f} min")
        return

    t_all = time.time()
    tasks = [(k, v, s) for k, v in cfgs.items() for s in v["seeds"]]
    res, times = pool_run(tasks)
    sim_wall = time.time() - t_all
    print(f"Simulated {len(tasks)} runs ({len(cfgs)} configs; N=100,000 at seeds 0-9, N=3,000 at "
          f"seeds 0-29) in {sim_wall / 60:.1f} min")
    refs = references(N_BIG, 900)
    refs_small = references(N_SMALL, 600)
    out = dict(refs=refs, refs_N3000=refs_small, sim_wall_min=sim_wall / 60,
               runs={k: len(v) for k, v in res.items()},
               cpu_s={k: float(np.sum(v)) for k, v in times.items()})

    # ---- Check 1
    out["check1"] = {}
    for label, a, b, seeds in (("N100000_test1", "c1_run", "c1_world", SEEDS_BIG),
                               ("N3000_test1", "c1_run_N3000", "c1_world_N3000", SEEDS),
                               ("N3000_S1_ctrl_600d", "c1_run_ctrl_S1_N3000", "ctrl_S1_N3000", SEEDS),
                               ("N3000_S2_ctrl_600d", "c1_run_ctrl_S2_N3000", "ctrl_S2_N3000", SEEDS)):
        n_id = identical(res, a, b, seeds)
        fa = mean_sem([res[a][x]["final_S"] for x in seeds])
        fb = mean_sem([res[b][x]["final_S"] for x in seeds])
        out["check1"][label] = dict(bit_identical=n_id, n=len(seeds), run=fa, world=fb,
                                    passes=n_id == len(seeds))
        print(f"CHECK 1 {label}: bit-identical (S, prevalence, incidence, deaths) on "
              f"{n_id}/{len(seeds)} seeds; mean final S run {fa[0]:.5f}, world {fb[0]:.5f}")

    # ---- Check 2 vs ODE: pass mark on N=100,000 (a, b); (c) report-only; N=3,000 reported
    out["check2"] = {}
    for key in ("a", "b", "c"):
        for tag, name, seeds, rf in (("N100000", f"c2{key}", SEEDS_BIG, refs[key]),
                                     ("N3000", f"c2{key}_N3000", SEEDS, refs_small[key])):
            fs = [res[name][x]["final_S"] for x in seeds]
            m, se, n = mean_sem(fs)
            r = dict(mean=m, sem=se, n=n, ode=rf)
            for rk, rv in rf.items():
                r[f"rel_err_{rk}"] = abs(m - rv) / rv
                r[f"gap_sems_{rk}"] = (m - rv) / se
                r[f"attack_rel_err_{rk}"] = abs((1 - m) - (1 - rv)) / (1 - rv)
            if tag == "N100000" and key in ("a", "b"):
                r["verdict"] = "PASS" if r["rel_err_primary"] <= 0.01 else "FAIL"
            else:
                r["verdict"] = "report-only"
            r["peak_I"] = mean_sem([res[name][x]["peak_I"] for x in seeds])
            r["active_at_end"] = int(sum(res[name][x]["series"]["exposed"][-1]
                                         + res[name][x]["series"]["prevalence"][-1] > 0 for x in seeds))
            r["zero_incidence_runs"] = int(sum(res[name][x]["series"]["incidence"].sum() == 0
                                               for x in seeds))
            out["check2"][f"{key}_{tag}"] = r
            print(f"CHECK 2{key} {tag}: mean final S {m:.5f} +/- {se:.5f} (n={n}) vs ODE "
                  + ", ".join(f"{rk} {rv:.5f} ({r['rel_err_' + rk] * 100:.3f}%, "
                              f"{r['gap_sems_' + rk]:+.2f} SEM, attack {r['attack_rel_err_' + rk] * 100:.1f}%)"
                              for rk, rv in rf.items())
                  + f" -> {r['verdict']}")

    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    out["ceiling"] = {"a_S1": ceiling(res, "c2a_N3000", "ctrl_S1_N3000", SEEDS, boot_idx),
                      "b_S1": ceiling(res, "c2b_N3000", "ctrl_S1_N3000", SEEDS, boot_idx),
                      "c_S2": ceiling(res, "c2c_N3000", "ctrl_S2_N3000", SEEDS, boot_idx)}
    for k, v in out["ceiling"].items():
        print(f"CEILING {k}: {json.dumps(v, default=str)}")

    # ---- Check 3
    out["check3"] = {}
    for s in SCEN:
        w, g, wc, gc = f"c3_world_{s}", f"c3_cbf_{s}", f"c3_world_{s}_ctrl", f"c3_cbf_{s}_ctrl"
        n_arm = identical(res, w, g, SEEDS)
        n_ctl = identical(res, wc, gc, SEEDS)
        d_fs = mean_sem([res[w][x]["final_S"] - res[g][x]["final_S"] for x in SEEDS])
        d_pi = mean_sem([res[w][x]["peak_I"] - res[g][x]["peak_I"] for x in SEEDS])
        cw = ceiling(res, w, wc, SEEDS, boot_idx)
        lo, hi = C30_CI[s]
        st = cw["stretch_ratio_of_means"]["value"]
        out["check3"][s] = dict(bit_identical_arm=n_arm, bit_identical_ctrl=n_ctl, n=len(SEEDS),
                                paired_final_S=d_fs, paired_peak_I=d_pi, shared_world_scores=cw,
                                stretch_within_C30_CI=bool(lo <= st <= hi), C30_CI=C30_CI[s])
        print(f"CHECK 3 {s}: bit-identical arm {n_arm}/30, control {n_ctl}/30; stretch x{st:.3f} "
              f"(C30 CI [{lo}, {hi}])")

    # ---- never_ill vs recovered agent-days, arm 1 in the world (A42: recovered do not decide;
    # this sizes the arm-2 calls that decision avoids)
    out["agent_days"] = {}
    for s in SCEN:
        k = f"c3_world_{s}"
        never_ill, rec_days, never_ill_active, rec_active = [], [], [], []
        for x in SEEDS:
            ser = res[k][x]["series"]
            ni = N_SMALL * ser["S"] + ser["exposed"]          # S + E agents (never_ill)
            rc = ser["recovered"]
            act = np.flatnonzero(ser["exposed"] + ser["prevalence"] > 0)
            L = int(act.max()) + 1 if len(act) else 0
            never_ill.append(ni.sum()); rec_days.append(rc.sum())
            never_ill_active.append(ni[:L].sum()); rec_active.append(rc[:L].sum())
        out["agent_days"][s] = dict(
            never_ill_600=float(np.mean(never_ill)), recovered_600=float(np.mean(rec_days)),
            never_ill_until_EI0=float(np.mean(never_ill_active)),
            recovered_until_EI0=float(np.mean(rec_active)), n=len(SEEDS))
        print(f"AGENT-DAYS {s}: {out['agent_days'][s]}")

    out["total_wall_min"] = (time.time() - t_all) / 60
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "checks.json"), "w"), indent=2,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print(f"\nTotal wall {out['total_wall_min']:.1f} min. Wrote {OUT}/checks.json")


if __name__ == "__main__":
    mp.freeze_support()
    main()
