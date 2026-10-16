"""
Step 11 (register C53): how many DISTINCT arm-2 prompts are there? A COUNTING TOOL ONLY -- no API
calls, no change to any arm-2 code path; the exact-reuse cache is not used by any real run.

Step 10b's stub dry run (arm 2's decision loop: never-ill agents re-asked with p = 0.3/day, A55
stop; stub answers A/B/C = 10/60/30 or 40/50/10, action drawn from the decision stream), world
window 7 days (the stub ignores the signal, so dynamics and counts equal 10b's). For every
decision the frozen v1 arm-2 prompt is determined by the rendered field values (renderer
`step4_prompt_tokens.render`, asserted equal to prompts/frozen_v1/arm2_template_v1.txt):
  per day:   population, day, recent-deaths sentence, earlier-deaths sentence, cumulative deaths,
             social norm %        (the 4-week totals are computed from reported deaths exactly as
             v1 defines them: 28-day means, A58/A59, not the world's 7-day signal)
  per agent: age band text, vulnerability text (a function of age band), occupation_flex 0-10,
             response_efficacy 0-10, current action
A prompt is counted by the tuple of these rendered values. Checked against full rendering
(every decision rendered with the real renderer) on one complete run per stub at N = 3,000.

  (a) decisions; (b) distinct prompts per run; (c) distinct prompts across the seeds of a size;
  (d) distinct values per field. Cost at $0.0000427 per call, +/-30%.
S1 at N = 3,000 / 10,000 / 15,000; S2 and S3 at N = 15,000; 10 seeds each, both stubs.

Usage:  python experiments/step11_prompt_reuse.py --verify | --sim | --score
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
import step4_prompt_tokens as rt  # noqa: E402
from shared_world import DecisionFunction, NORMAL, PRECAUTIONS, STAY_HOME  # noqa: E402

FROZEN = os.path.join(ROOT, "prompts", "frozen_v1", "arm2_template_v1.txt")
assert open(FROZEN, encoding="utf-8", newline="").read() == rt.TEMPLATE, "renderer != frozen v1"

STUBS = {"10/60/30": (0.10, 0.60, 0.30), "40/50/10": (0.40, 0.50, 0.10)}
SCEN = {"S1": dict(R0=3.0, T_H=14.0), "S2": dict(R0=2.0, T_H=14.0), "S3": dict(R0=3.0, T_H=28.0)}
SEEDS = list(range(10))
CONFIGS = [("S1", 3000), ("S1", 10_000), ("S1", 15_000), ("S2", 15_000), ("S3", 15_000)]
COST = 0.0000427
ACT_NAME = {NORMAL: "normal", PRECAUTIONS: "precautions", STAY_HOME: "stay_home"}
DYN_FIELDS = ("population", "day", "deaths_recent", "deaths_earlier", "deaths_cumulative", "social_norm")
STAT_FIELDS = ("age_band", "vulnerability", "occupation_flex", "response_efficacy", "current_action")
OUT = os.path.join(ROOT, "results", "step7")
_POP = {}


def dyn_fields(day, rep, social_norm, N):
    """The per-day rendered values, exactly as rt.render computes them (28-day means, A58/A59)."""
    m28 = float(rep[max(0, day - 28):day].mean()) if day > 0 else 0.0
    t7 = day - 7
    m28_7 = float(rep[max(0, t7 - 28):t7].mean()) if t7 > 0 else 0.0
    n = rt.half_up(min(28, day) * m28)
    recent = (f"In the past four weeks, {n} people in your town died of it." if day >= 28
              else f"Since the outbreak began, {n} people in your town have died of it.")
    m = rt.half_up(min(28, max(day - 7, 0)) * m28_7)
    if day >= 35:
        earlier = f"In the four weeks up to a week ago, {m} died."
    elif day >= 7:
        earlier = f"Between the start of the outbreak and a week ago, {m} died."
    else:
        earlier = f"A week ago, {m} people had died of it."
    return (f"{N:,}", str(day), recent, earlier, str(rt.half_up(float(rep.sum()))),
            f"{rt.half_up(100 * social_norm)}%"), (m28, m28_7)


class CountingStub(DecisionFunction):
    mode = "discrete"
    redecides = True

    def __init__(self, probs, pop, full_render=False):
        self.p_home, self.p_prec, _ = probs
        self.pop = pop
        occ = np.array([rt.half_up(10 * x) for x in pop.occupation_flex])
        eff = np.array([rt.half_up(10 * x) for x in pop.response_efficacy])
        self.static = (np.asarray(pop.age_band) * 121 + occ * 11 + eff).astype(np.int64)   # < 1210
        self.days, self.keys, self.full = [], [], ([] if full_render else None)

    def decide(self, day, agents, view, rng):
        dyn, (m28, m28_7) = dyn_fields(day, view["reported_deaths"], view["social_norm"], view["N"])
        self.days.append(dyn)
        act = view["action"][agents].astype(np.int64)
        self.keys.append((len(self.days) - 1) * 3630 + self.static[agents] * 3 + act)
        if self.full is not None:
            from perception import Perception
            rep, pop = view["reported_deaths"], self.pop
            for i in agents:
                self.full.append(rt.render(Perception(
                    deaths_28day_mean=m28, deaths_cumulative=float(rep.sum()),
                    deaths_28day_mean_7d_ago=m28_7, current_action=ACT_NAME[int(view["action"][i])],
                    social_norm=float(view["social_norm"]), age_band=int(pop.age_band[i]),
                    vulnerability=float(pop.vulnerability[i]), occupation_flex=float(pop.occupation_flex[i]),
                    response_efficacy=float(pop.response_efficacy[i]), population=int(view["N"]), day=int(day))))
        u = rng.random(len(agents))
        return np.where(u < self.p_home, STAY_HOME,
                        np.where(u < self.p_home + self.p_prec, PRECAUTIONS, NORMAL)).astype(np.int8)


def run_one(task, full_render=False):
    stub, sc, n, seed = task
    from population import build_population
    from shared_world import run_shared_world
    if n not in _POP:
        _POP[n] = build_population(N=n, seed=0)
    d = CountingStub(STUBS[stub], _POP[n], full_render)
    t0 = time.time()
    run_shared_world(N=n, seed=seed, decision=d, days=600, f_D=_POP[n].vulnerability, window=7,
                     detection_rate=0.7, redecide_prob=0.3, stop_deciding_when_no_infection=True, **SCEN[sc])
    keys = np.concatenate(d.keys) if d.keys else np.zeros(0, np.int64)
    return dict(task=task, decisions=int(len(keys)), uniq=np.unique(keys), days=d.days,
                full=d.full, keys=keys if full_render else None, dt=time.time() - t0)


def verify():
    for stub in STUBS:
        r = run_one((stub, "S1", 3000, 0), full_render=True)
        n_full = len(set(r["full"]))
        n_pairs = len(set(zip(r["keys"].tolist(), r["full"])))   # one-to-one iff pairs == keys == strings
        ok = n_full == len(r["uniq"]) == n_pairs and len(r["full"]) == r["decisions"]
        print(f"  {stub} N 3,000 seed 0: decisions {r['decisions']:,} (rendered {len(r['full']):,}); distinct "
              f"by key {len(r['uniq']):,}; distinct full strings {n_full:,}; distinct (key, string) pairs "
              f"{n_pairs:,}; one-to-one {ok}")


def _work(task):
    r = run_one(task)
    return r["task"], r["decisions"], r["uniq"], r["days"], r["dt"]


def simulate():
    tasks = [(stub, sc, n, s) for stub in STUBS for sc, n in CONFIGS for s in SEEDS]
    tasks.sort(key=lambda t: -t[2])
    t0, res = time.time(), {}
    with mp.Pool(16) as pool:
        for task, dec, uniq, days, dt in pool.imap_unordered(_work, tasks):
            res[task] = (dec, uniq, days, dt)
    print(f"{len(tasks)} runs {(time.time() - t0) / 60:.1f} min (per run "
          f"{min(v[3] for v in res.values()):.1f}-{max(v[3] for v in res.values()):.1f}s)")
    out = {}
    for stub in STUBS:
        for sc, n in CONFIGS:
            dyn_ids, all_keys, per_run, decs, askdays = {}, [], [], [], []
            field_vals = {f: set() for f in DYN_FIELDS + STAT_FIELDS}
            for s in SEEDS:
                dec, uniq, days, _ = res[(stub, sc, n, s)]
                gid = np.array([dyn_ids.setdefault(dd, len(dyn_ids)) for dd in days], np.int64)
                local = uniq // 3630
                all_keys.append(gid[local] * 3630 + uniq % 3630)
                per_run.append(len(uniq)); decs.append(dec); askdays.append(len(days))
                for dd in days:
                    for f, v in zip(DYN_FIELDS, dd):
                        field_vals[f].add(v)
            ag = np.unique(np.concatenate(all_keys) % 3630)
            for k in ag:
                st, act = int(k // 3), int(k % 3)
                age, occ, eff = st // 121, (st % 121) // 11, st % 11
                field_vals["age_band"].add(age); field_vals["vulnerability"].add(age)
                field_vals["occupation_flex"].add(occ); field_vals["response_efficacy"].add(eff)
                field_vals["current_action"].add(act)
            across = int(len(np.unique(np.concatenate(all_keys))))
            out[f"{stub}|{sc}|{n}"] = dict(
                decisions_per_run=decs, distinct_per_run=per_run, ask_days=askdays,
                decisions_total=int(sum(decs)), distinct_per_run_total=int(sum(per_run)),
                distinct_across_seeds=across, distinct_day_contexts=len(dyn_ids),
                distinct_agent_contexts=int(len(ag)),
                field_distinct={f: len(v) for f, v in field_vals.items()})
    json.dump(out, open(os.path.join(OUT, "step11_counts.json"), "w"), indent=1)


def score():
    out = json.load(open(os.path.join(OUT, "step11_counts.json")))
    c10 = {(x["stub"], x["N"], x["seed"]): x["calls"] for x in json.load(open(os.path.join(OUT, "step10_calls.json")))}
    print(f"cost ${COST}/call, band +/-30%; 10 seeds per row")
    print("stub | scen | N | (a) decisions total (per-run mean) [= C52?] | (b) distinct per run, mean (sum) "
          "[share of decisions] | (c) distinct across seeds | cost (a) | cost (b) | cost (c) | asking days mean")
    for key_, r in out.items():
        stub, sc, n = key_.split("|"); n = int(n)
        dec, per = np.array(r["decisions_per_run"]), np.array(r["distinct_per_run"])
        same = (all(c10.get((stub, n, s)) == d for s, d in zip(SEEDS, dec)) if sc == "S1" else None)
        f = lambda c: f"${c * COST:,.2f} [${0.7 * c * COST:,.2f}, ${1.3 * c * COST:,.2f}]"  # noqa: E731
        print(f"{stub} | {sc} | {n:>6,} | {dec.sum():,} ({dec.mean():,.0f}) [{same}] | {per.mean():,.0f} ({per.sum():,}) "
              f"[{per.sum() / dec.sum():.3f}] | {r['distinct_across_seeds']:,} [{r['distinct_across_seeds'] / dec.sum():.3f}] | "
              f"{f(dec.sum())} | {f(per.sum())} | {f(r['distinct_across_seeds'])} | {np.mean(r['ask_days']):.1f}")
    print("\n(d) distinct rendered values per field, across the 10 seeds:")
    fields = list(next(iter(out.values()))["field_distinct"])
    print("stub | scen | N | " + " | ".join(fields) + " | day contexts | agent contexts")
    for key_, r in out.items():
        print(key_.replace("|", " | ") + " | " + " | ".join(str(r["field_distinct"][f]) for f in fields)
              + f" | {r['distinct_day_contexts']} | {r['distinct_agent_contexts']}")


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--verify", verify), ("--sim", simulate), ("--score", score)):
        if flag in sys.argv:
            fn()
