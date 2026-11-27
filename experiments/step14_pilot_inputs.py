"""
Locked pilot inputs (register C59), built by code and rendered with the v2 DRAFT renderer. No API.

  results/pilot/situations_a62.json     A62 set, 14 = 7 death histories x bands 2 and 8 (step 3a)
  results/pilot/situations_repeat.json  repeat-pilot set, 20 = 5 A78 phases x 4 draws (step 3c)

Each situation carries its PerceptionV2 fields, the rendered prompt and the prompt's SHA-256; the
files' SHA-256 are printed (and recorded in C59).

A62 set: day 60, population 15,000, social norm 0.85, current action normal, occupation_flex and
response_efficacy = C34's agent values (as C37). Reported deaths fall only on days 25-59, constant
within each week W1 (days 25-31) ... W5 (days 53-59). The death fields are computed from that
daily series exactly as the world computes them (7-day mean over the days strictly before day 60).

Repeat set: C55's arm-1 S1 run (N = 15,000, seed 0, 7-day window) re-run read-only (start-of-day
state and actions recorded every day; outputs asserted equal to the step-12 cache). A78 phases on
the run's end-of-day prevalence; per phase 4 (day, never-ill agent) pairs drawn uniformly without
replacement (seed 20261127), then one of the 4 set to stay_home.

Usage:  py -3.14 experiments/step14_pilot_inputs.py
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import render_v2 as r2  # noqa: E402

OUT = os.path.join(ROOT, "results", "pilot")
CACHE12 = os.path.join(ROOT, "results", "step7", "step12_runs.npz")
C34_SIT = os.path.join(ROOT, "results", "step4", "pilot_situations.json")
N, DAY, NORM = 15_000, 60, 0.85
BANDS = (2, 8)
WEEKS = {"D0": [0] * 5, "D4": [3.75] * 5, "D15": [15] * 5, "D63": [62.5] * 5, "D125": [125] * 5,
         "Trise": [5, 5, 5, 5, 15], "Tfall": [31, 31, 31, 31, 15]}      # W1..W5 weekly totals
EXPECT = {"D0": (0, 0, 0), "D4": (4, 4, 19), "D15": (15, 15, 75), "D63": (63, 63, 313),
          "D125": (125, 125, 625), "Trise": (15, 5, 35), "Tfall": (15, 31, 139)}   # past week, week before, cumulative
SEED = 20261127
PHASES = ("early", "rising", "peak", "falling", "late")
DRAWS = 4
ACT = {0: "normal", 1: "precautions", 2: "stay_home"}


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    data = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    print(f"results/pilot/{name}  sha256 {sha(data)}  ({len(obj['situations'])} situations)")


def a62_set(pop):
    meta = json.load(open(C34_SIT))["meta"]
    occ, eff = meta["occupation_flex"], meta["response_efficacy"]
    sits = []
    for name, weeks in WEEKS.items():
        rep = np.zeros(DAY)
        for w, total in enumerate(weeks):
            rep[25 + 7 * w: 32 + 7 * w] = total / 7
        sig = np.array([rep[max(0, t - 7):t].mean() if t else 0.0 for t in range(DAY + 1)])
        for band in BANDS:
            vul = float(pop.vulnerability[pop.age_band == band][0])
            p = r2.perception_from_world(DAY, sig, rep, np.full(DAY + 1, NORM), N, (band, vul, occ, eff), "normal")
            text = r2.render(p)
            nums = (r2.half_up(7 * p.deaths_7day_mean), r2.half_up(7 * p.deaths_7day_mean_7d_ago),
                    r2.half_up(p.deaths_cumulative))
            assert nums == EXPECT[name], (name, nums)
            assert f"In the past week, {nums[0]} people" in text and f"In the week before that, {nums[1]} died." in text
            sits.append(dict(id=f"{name}_b{band}", history=name, band=band, weekly_totals_W1_W5=weeks,
                             fields={k: getattr(p, k) for k in r2.FIELD_PLACEHOLDER}, prompt=text,
                             prompt_sha256=sha(text)))
    return dict(set="A62 (C59 step 3a)", day=DAY, population=N, social_norm=NORM,
                occupation_flex=occ, response_efficacy=eff, situations=sits)


def arm1_snapshots(pop):
    from shared_world import CBFArm1, run_shared_world
    snap = {}

    class Recorder(CBFArm1):
        """CBF unchanged; reads run_shared_world's start-of-day state and actions (read-only)."""

        def transitions(self, view):
            f = sys._getframe(1)
            if f.f_code.co_name == "run_shared_world":
                t = f.f_locals["t"]
                if t not in snap:                    # first call of day t: the pre-sub-step check
                    snap[t] = (f.f_locals["state"].copy(), f.f_locals["action"].copy())
            return super().transitions(view)

    o = run_shared_world(N=N, seed=0, decision=Recorder(), days=600, f_D=pop.vulnerability, window=7,
                         detection_rate=0.7, R0=3.0, T_H=14.0)
    c = np.load(CACHE12)
    for k in ("incidence", "prevalence", "S", "awareness_signal", "deaths"):
        assert np.array_equal(np.asarray(o[k], float), c[f"arm1|arm1|S1|0#{k}"]), k
    return o, snap


def phases_of(prev, start_EI, last_day):
    """A78 phases on daily prevalence; late = later days whose start-of-day E + I > 0."""
    t_max = int(np.argmax(prev))
    thr = 0.1 * prev[t_max]
    t10 = int(np.flatnonzero(prev >= thr)[0])
    t_last = int(np.flatnonzero(prev >= thr)[-1])
    ph = {"early": range(0, t10), "rising": range(t10, t_max - 3), "peak": range(t_max - 3, t_max + 4),
          "falling": range(t_max + 4, t_last + 1),
          "late": [t for t in range(t_last + 1, last_day + 1) if start_EI[t] > 0]}
    return ph, dict(t_max=t_max, P_max=float(prev[t_max]), t_first_10pct=t10, t_last_10pct=t_last)


def repeat_set(pop):
    from shared_world import own_health_of, NEVER_ILL
    from model import E, I
    o, snap = arm1_snapshots(pop)
    last = max(snap)
    start_EI = {t: int(np.count_nonzero((st == E) | (st == I))) for t, (st, _) in snap.items()}
    ph, info = phases_of(np.asarray(o["prevalence"]), start_EI, last)
    rng = np.random.default_rng(SEED)
    sits = []
    for name in PHASES:
        days = list(ph[name])
        assert days, f"phase {name} is empty"
        never = [np.flatnonzero(own_health_of(snap[t][0]) == NEVER_ILL) for t in days]
        counts = np.array([len(x) for x in never])
        pick = rng.choice(int(counts.sum()), DRAWS, replace=False)
        home = int(rng.integers(DRAWS))
        cum = np.cumsum(counts)
        for j, g in enumerate(pick):
            di = int(np.searchsorted(cum, g, side="right"))
            t = days[di]
            i = int(never[di][g - (cum[di - 1] if di else 0)])
            act = "stay_home" if j == home else ACT[int(snap[t][1][i])]
            p = r2.perception_from_world(t, o["awareness_signal"], o["reported_deaths"], o["social_norm"], N,
                                         (pop.age_band[i], pop.vulnerability[i], pop.occupation_flex[i],
                                          pop.response_efficacy[i]), act)
            text = r2.render(p)
            sits.append(dict(id=f"{name}{j}", phase=name, day=t, agent=i, draw=int(g),
                             action_in_run=ACT[int(snap[t][1][i])], set_to_stay_home=j == home,
                             fields={k: getattr(p, k) for k in r2.FIELD_PLACEHOLDER}, prompt=text,
                             prompt_sha256=sha(text)))
    phase_days = {k: [int(min(v)), int(max(v)), len(list(v))] for k, v in ph.items()}
    return dict(set="repeat pilot (C59 step 3c)", run=dict(arm="arm1 (CBF)", scenario="S1", N=N, seed=0, window=7),
                seed=SEED, phase_info=info, phase_days_first_last_count=phase_days,
                last_simulated_day=int(last), situations=sits)


def main():
    from population import build_population
    pop = build_population(N=N, seed=0)
    a = a62_set(pop)
    save("situations_a62.json", a)
    rp = repeat_set(pop)
    save("situations_repeat.json", rp)
    print(f"\nphases: {rp['phase_info']}; days (first, last, count) {rp['phase_days_first_last_count']}; "
          f"last simulated day {rp['last_simulated_day']}")
    for s in rp["situations"]:
        f = s["fields"]
        print(f"  {s['id']:9s} day {s['day']:3d} agent {s['agent']:5d} band {f['age_band']} action "
              f"{f['current_action']:11s} (run: {s['action_in_run']:11s}) | {s['prompt'].split(chr(10))[2]}")
    for sid in ("Trise_b8", "Tfall_b8"):
        print(f"\n===== A62 {sid}\n" + next(s for s in a["situations"] if s["id"] == sid)["prompt"])
    for ph in ("early", "peak"):
        s = next(x for x in rp["situations"] if x["phase"] == ph)
        print(f"\n===== repeat {s['id']} (day {s['day']}, agent {s['agent']})\n{s['prompt']}")


if __name__ == "__main__":
    main()
