"""
Step 3: score arm 1 with the frozen shape-metric list (register A33-A35, C30).

Arm 1 = foundation CBF (step2_common.FOUNDATION: flat r=0.5, window 28, detection 0.7 plain,
per-agent f_D, Weitz disease, 48 sub-steps, 10 initial infected), N=3,000, days=600, seeds 0-29
(the C26/C27 seeds).
  (a) S1, S2, S3 (C27), each with its own no-behaviour control
  (b) S1 at gamma_beh in {0.25, 0.5, 1, 2, 4} (C26), sharing the S1 control
S1 and gamma_beh=1 are the same configuration and are run once.

No series were cached by C26/C27, so every config is re-run at days=600 with the series kept;
final S and peak I are checked bit-identical to the stored C26/C27 runs (valid because every
N=3,000 run ends by day 401, C28, and the first 600 days use the same random draws).

Metrics (A33): PRIMARY M3 = T10-90 duration (per-run, and on the 1%-aligned averaged curve with
a 1,000-resample bootstrap); SECONDARY M1 = EpidemicKabu wave count (kernel 18); SAFETY NET =
peak-I reduction and final-S increase vs own control. STRETCH FACTOR (A34) = arm M3 / own-control
M3. Truncation rule (A35): M3 is reported as a duration only if every run has E+I = 0 by day 600.

Usage:  python experiments/step3_score_arm1.py [--timing]
"""
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step2_common as c  # noqa: E402
import step3_shape_metrics as sm  # noqa: E402

N = 3_000
DAYS = 600
SEEDS = list(range(30))
N_BOOT = 1000
BOOT_SEED = 20261005
OUT = os.path.join(HERE, "..", "results", "step3")
RESULTS = os.path.join(HERE, "..", "results")

BASE = dict(c.FOUNDATION, N=N, days=DAYS, keep_series=True)
ARMS = {
    "S1": dict(BASE, R0=3.0, T_H=14.0),                    # = gamma_beh 1
    "S2": dict(BASE, R0=2.0, T_H=14.0),
    "S3": dict(BASE, R0=3.0, T_H=28.0),
    **{f"g{g}": dict(BASE, R0=3.0, T_H=14.0, gamma_beh=g) for g in (0.25, 0.5, 2.0, 4.0)},
}
CONTROLS = {
    "S1_ctrl": dict(BASE, R0=3.0, T_H=14.0, behaviour=False),
    "S2_ctrl": dict(BASE, R0=2.0, T_H=14.0, behaviour=False),
    "S3_ctrl": dict(BASE, R0=3.0, T_H=28.0, behaviour=False),
}
CONTROL_OF = {"S1": "S1_ctrl", "S2": "S2_ctrl", "S3": "S3_ctrl",
              **{f"g{g}": "S1_ctrl" for g in (0.25, 0.5, 2.0, 4.0)}}
# report order: the 8 configs of the prompt (S1 doubles as gamma_beh 1)
REPORT = [("S1", "S1"), ("S2", "S2"), ("S3", "S3"), ("gamma 0.25", "g0.25"),
          ("gamma 0.5", "g0.5"), ("gamma 1 (= S1)", "S1"), ("gamma 2", "g2.0"),
          ("gamma 4", "g4.0")]
# stored C26/C27 runs for the bit-identity check
STORED = {"S1": ("grad", "N3000_g1.0"), "S2": ("scen", "N3000_S2"), "S3": ("scen", "N3000_S3"),
          "g0.25": ("grad", "N3000_g0.25"), "g0.5": ("grad", "N3000_g0.5"),
          "g2.0": ("grad", "N3000_g2.0"), "g4.0": ("grad", "N3000_g4.0"),
          "S1_ctrl": ("grad", "N3000_ctrl"), "S2_ctrl": ("scen", "N3000_S2_ctrl"),
          "S3_ctrl": ("scen", "N3000_S3_ctrl")}
WEITZ_STRETCH = "K1 ODE 461/23 = x20.0; K2 averaged 477/23 = x20.7 (both truncated at day 600, C29)"


def _waves(y):
    return sm.kabu_n_waves(y, kernel=18)


def mean_sem(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def main():
    cfgs = {**ARMS, **CONTROLS}
    if "--timing" in sys.argv:
        res, times, _ = c.run_pool([(k, v, 0) for k, v in cfgs.items()])
        for k, v in times.items():
            print(f"  {k:8s} seed 0: {v[0]:.1f}s")
        t0 = time.time(); _waves(res["S1"][0]["series"]["incidence"])
        print(f"  EpidemicKabu one call: {time.time()-t0:.1f}s")
        return

    t0 = time.time()
    res, _, _ = c.run_pool([(k, v, s) for k, v in cfgs.items() for s in SEEDS])
    print(f"Simulated {len(cfgs)} configs x {len(SEEDS)} seeds in {(time.time()-t0)/60:.1f} min")
    stored = {"grad": json.load(open(os.path.join(RESULTS, "step2_gradation.json")))["per_seed"],
              "scen": json.load(open(os.path.join(RESULTS, "step2_scenarios.json")))["per_seed"]}
    inc = {k: np.array([res[k][s]["series"]["incidence"] for s in SEEDS]) for k in cfgs}
    active600 = {k: int(sum(res[k][s]["series"]["exposed"][DAYS - 1]
                            + res[k][s]["series"]["prevalence"][DAYS - 1] > 0 for s in SEEDS))
                 for k in cfgs}
    ident = {}
    for k in cfgs:
        src, nm = STORED[k]
        ident[k] = sum(res[k][s]["final_S"] == stored[src][nm][str(s)]["final_S"]
                       and res[k][s]["peak_I"] == stored[src][nm][str(s)]["peak_I"] for s in SEEDS)
    print("Bit-identical to stored C26/C27 (final S and peak I): "
          + ", ".join(f"{k} {v}/30" for k, v in ident.items()))

    t0 = time.time()
    with mp.Pool(16) as pool:
        waves = {k: np.array(pool.map(_waves, list(inc[k]))) for k in cfgs}
    print(f"EpidemicKabu on {len(cfgs) * len(SEEDS)} runs in {(time.time()-t0)/60:.1f} min")
    m3 = {k: np.array([sm.duration(y) for y in inc[k]]) for k in cfgs}

    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    avg = {}
    for k in cfgs:
        m, aligned, n_used = sm.align_average(inc[k], N, 0.01)
        bvals = np.array([sm.duration(aligned[idx].mean(0)) for idx in boot_idx])
        avg[k] = dict(value=sm.duration(m), ci=tuple(np.percentile(bvals, [2.5, 97.5])),
                      n_used=n_used, n_boot_defined=int(np.isfinite(bvals).sum()))

    summary = {}
    for label, k in REPORT:
        if k in summary:
            summary[label] = summary[k]; continue
        ctl = CONTROL_OF[k]
        trunc = active600[k] > 0 or active600[ctl] > 0
        a, cc = m3[k], m3[ctl]
        d = mean_sem(a - cc)
        ratio_means = a.mean() / cc.mean()
        boot_r = np.array([a[i].mean() / cc[i].mean() for i in boot_idx])
        per_seed = mean_sem(a / cc)
        w_d = mean_sem(waves[k] - waves[ctl])
        pI = np.array([res[k][s]["peak_I"] for s in SEEDS])
        pIc = np.array([res[ctl][s]["peak_I"] for s in SEEDS])
        fS = np.array([res[k][s]["final_S"] for s in SEEDS])
        fSc = np.array([res[ctl][s]["final_S"] for s in SEEDS])
        dI, dS = mean_sem(pI - pIc), mean_sem(fS - fSc)
        r = dict(
            control=ctl, truncated=bool(trunc), active_at_600=dict(arm=active600[k], control=active600[ctl], n=len(SEEDS)),
            m3_arm=mean_sem(a), m3_ctrl=mean_sem(cc), m3_paired=dict(mean=d[0], sem=d[1], n=d[2], sems=d[0] / d[1]),
            stretch_ratio_of_means=dict(value=float(ratio_means), ci=tuple(np.percentile(boot_r, [2.5, 97.5]))),
            stretch_mean_per_seed=dict(mean=per_seed[0], sem=per_seed[1], n=per_seed[2]),
            m3_avg_arm=avg[k], m3_avg_ctrl=avg[ctl],
            m1_arm=mean_sem(waves[k]), m1_ctrl=mean_sem(waves[ctl]),
            m1_paired=dict(mean=w_d[0], sem=w_d[1], n=w_d[2], sems=w_d[0] / w_d[1] if w_d[1] > 0 else np.nan),
            peak_I_reduction_pct=float(-dI[0] / pIc.mean() * 100),
            peak_I_paired=dict(mean=dI[0], sem=dI[1], n=dI[2], sems=dI[0] / dI[1]),
            final_S_paired=dict(mean=dS[0], sem=dS[1], n=dS[2], sems=dS[0] / dS[1]),
            bit_identical=dict(arm=ident[k], control=ident[ctl]))
        summary[k] = r
        summary[label] = r
        print(f"\n=== {label} (control {ctl}) ===")
        print(f"  truncation: E+I>0 at day 600 arm {active600[k]}/30, control {active600[ctl]}/30"
              f" -> {'TRUNCATED' if trunc else 'valid'}")
        print(f"  M3 per-run: arm {r['m3_arm'][0]:.2f} +/- {r['m3_arm'][1]:.2f} (n={r['m3_arm'][2]}), "
              f"control {r['m3_ctrl'][0]:.2f} +/- {r['m3_ctrl'][1]:.2f} (n={r['m3_ctrl'][2]}); paired "
              f"{d[0]:+.2f} +/- {d[1]:.2f} d ({d[0]/d[1]:+.2f} SEM, n={d[2]})")
        print(f"  STRETCH: ratio of means x{ratio_means:.3f} [95% CI {r['stretch_ratio_of_means']['ci'][0]:.3f}, "
              f"{r['stretch_ratio_of_means']['ci'][1]:.3f}]; mean per-seed ratio x{per_seed[0]:.3f} +/- "
              f"{per_seed[1]:.3f} (n={per_seed[2]})")
        print(f"  M3 averaged (1% alignment): arm {avg[k]['value']:.0f} [{avg[k]['ci'][0]:.0f}, {avg[k]['ci'][1]:.0f}]"
              f" (n used {avg[k]['n_used']}/30), control {avg[ctl]['value']:.0f} "
              f"[{avg[ctl]['ci'][0]:.0f}, {avg[ctl]['ci'][1]:.0f}] (n used {avg[ctl]['n_used']}/30)")
        print(f"  M1 waves: arm {r['m1_arm'][0]:.2f} +/- {r['m1_arm'][1]:.2f}, control {r['m1_ctrl'][0]:.2f} "
              f"+/- {r['m1_ctrl'][1]:.2f} (n={r['m1_arm'][2]}/{r['m1_ctrl'][2]}); paired {w_d[0]:+.2f} +/- "
              f"{w_d[1]:.2f} ({r['m1_paired']['sems']:+.2f} SEM)")
        print(f"  peak I: {dI[0]:+.1f} +/- {dI[1]:.1f} ({dI[0]/dI[1]:+.2f} SEM) = "
              f"{r['peak_I_reduction_pct']:.1f}% reduction; final S {dS[0]:+.4f} +/- {dS[1]:.4f} "
              f"({dS[0]/dS[1]:+.2f} SEM), n=30")
        print(f"  reference: Weitz plateau stretch >= x20 ({WEITZ_STRETCH})")

    # agreement M3 vs M1
    from scipy.stats import spearmanr
    arm_keys = list(ARMS)
    all_m3 = np.concatenate([m3[k] for k in arm_keys])
    all_m1 = np.concatenate([waves[k] for k in arm_keys])
    rho, pval = spearmanr(all_m3, all_m1)
    rank_m3 = sorted(arm_keys, key=lambda k: m3[k].mean())
    rank_m1 = sorted(arm_keys, key=lambda k: waves[k].mean())
    rho_cfg, _ = spearmanr([m3[k].mean() for k in arm_keys], [waves[k].mean() for k in arm_keys])
    print(f"\n=== Agreement M3 vs M1 ===\n  Spearman over {len(all_m3)} arm runs (7 distinct configs x 30;"
          f" S1 = gamma 1 counted once): rho = {rho:.3f} (p = {pval:.2g})")
    print(f"  config order by mean M3: {rank_m3}\n  config order by mean M1: {rank_m1}\n"
          f"  same order: {rank_m3 == rank_m1}; Spearman over the 7 config means: {rho_cfg:.3f}")
    agreement = dict(spearman_runs=float(rho), p=float(pval), n_runs=int(len(all_m3)),
                     rank_m3=rank_m3, rank_m1=rank_m1, same_order=rank_m3 == rank_m1,
                     spearman_config_means=float(rho_cfg))

    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(summary={label: summary[label] for label, _ in REPORT},
                   agreement=agreement, bit_identical=ident, active_at_600=active600,
                   per_run=dict(m3={k: v.tolist() for k, v in m3.items()},
                                m1={k: v.tolist() for k, v in waves.items()})),
              open(os.path.join(OUT, "arm1_scores.json"), "w"), indent=2,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(inc, summary, boot_idx)
    print(f"\nWrote {OUT}/arm1_scores.json and arm1_*.png")


def figures(inc, summary, boot_idx):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    BEH, CTRL, INK, INK2, SURF = sm.BEH, sm.CTRL, sm.INK, sm.INK2, sm.SURF
    titles = {"S1": "S1 (R0=3, T_H=14)", "S2": "S2 (R0=2, T_H=14)", "S3": "S3 (R0=3, T_H=28)"}
    for k in ("S1", "S2", "S3"):
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURF)
        for key, col, lab in ((k, BEH, "arm 1 (CBF)"), (summary[k]["control"], CTRL, "no behaviour")):
            m, aligned, n = sm.align_average(inc[key], N, 0.01)
            m, aligned = m * 1000, aligned * 1000
            t = np.arange(len(m))
            for run_ in aligned[:5]:
                ax.plot(t, run_, color=col, lw=0.6, alpha=0.25)
            bc = np.array([aligned[idx].mean(0) for idx in boot_idx])
            ax.fill_between(t, *np.percentile(bc, [2.5, 97.5], axis=0), color=col, alpha=0.25, lw=0)
            ax.plot(t, m, color=col, lw=2, label=f"{lab}: mean of {n} runs, 95% bootstrap band")
        sm._style(ax, f"Arm 1 vs own control - {titles[k]}, N=3,000, 30 seeds")
        ax.set_xlim(0, 150)
        st = summary[k]["stretch_ratio_of_means"]
        ax.text(0.98, 0.62, f"stretch x{st['value']:.2f} [{st['ci'][0]:.2f}, {st['ci'][1]:.2f}]\n"
                f"peak I {summary[k]['peak_I_reduction_pct']:.0f}% lower",
                transform=ax.transAxes, ha="right", color=INK2, fontsize=9)
        ax.legend(frameon=False, labelcolor=INK2, fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(OUT, f"arm1_{k}.png")); plt.close(fig)

    labels = ["S1\n(= γ 1)", "S2", "S3", "γ 0.25", "γ 0.5", "γ 2", "γ 4"]
    keys = ["S1", "S2", "S3", "g0.25", "g0.5", "g2.0", "g4.0"]
    vals = [summary[k]["stretch_ratio_of_means"]["value"] for k in keys]
    lo = [v - summary[k]["stretch_ratio_of_means"]["ci"][0] for v, k in zip(vals, keys)]
    hi = [summary[k]["stretch_ratio_of_means"]["ci"][1] - v for v, k in zip(vals, keys)]
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURF)
    x = np.arange(len(keys))
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="o", color=BEH, ecolor=INK2, elinewidth=1.2,
                capsize=4, markersize=7)
    for xi, v in zip(x, vals):
        ax.annotate(f"x{v:.2f}", (xi, v), xytext=(8, 0), textcoords="offset points",
                    color=INK2, fontsize=8, va="center")
    ax.axhline(1, color=INK2, lw=1, ls="--")
    ax.axvline(2.5, color="#e6e5e0", lw=1)
    ax.set_xticks(x, labels)
    ax.set_facecolor(SURF)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=INK2)
    ax.set_ylabel("stretch factor (arm T10-90 / own-control T10-90)", color=INK2)
    ax.set_title("Arm 1 stretch factor, N=3,000, 30 seeds (95% bootstrap CI)", color=INK,
                 loc="left", fontsize=11)
    ax.text(0.01, 0.02, "x1 = no flattening (dashed). Weitz plateau reference (K1/K2): >= x20, "
            "truncated at 600 d - off this scale.", transform=ax.transAxes, color=INK2, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "arm1_stretch_summary.png")); plt.close(fig)


if __name__ == "__main__":
    mp.freeze_support()
    main()
