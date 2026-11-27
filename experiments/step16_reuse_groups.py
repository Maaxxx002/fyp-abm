"""
A78 group sizes (register C61), offline, no API.

Re-runs C53's stub dry runs (S1, N = 15,000, seeds 0-9, stubs 10/60/30 and 40/50/10; arm 2's
decision loop: never-ill agents re-asked with p = 0.3/day, A55 stop, 7-day world window), with
prompts identified by the v2 renderer (render_v2): per day the rendered population, day, the two
v2 death sentences, cumulative deaths and social norm; per agent age band (with vulnerability),
occupation_flex 0-10, response_efficacy 0-10 and current action. A80: answers are never shared
between runs, so a group = one (day, distinct prompt) of one run, of size k = agents asked with it.
Checked against full v2 rendering (every decision rendered and hashed) on seed 0 of each stub.
Decision counts per run are checked against C53 (results/step7/step11_counts.json).

Phases per A78 / C59 (approved choices) on each run's own end-of-day prevalence; late = days after
the falling phase whose start-of-day E + I > 0.

  --verify   full v2 rendering on seed 0 of each stub: key <-> prompt one-to-one
  --sim      20 runs -> results/pilot/reuse_groups.npz
  --score    per stub and phase: groups, sum k, sum k^2, K = sum k^2 / sum k, largest k; sum min(m, k)
             for m = 1, 3, 5, 10, 20 beside C53 column (b); largest per-prompt SD of A passing A78
             with m = 1 and m = 3 at mean b = 0.05, 0.10, 0.15 (information only)

Usage:  py -3.14 experiments/step16_reuse_groups.py --verify | --sim | --score
"""
import hashlib
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
import render_v2 as r2  # noqa: E402
import step11_prompt_reuse as s11  # noqa: E402
from step14_pilot_inputs import phases_of, PHASES  # noqa: E402

N, SC = 15_000, "S1"
SEEDS = list(range(10))
STUBS = s11.STUBS
OUT = os.path.join(ROOT, "results", "pilot")
NPZ = os.path.join(OUT, "reuse_groups.npz")
MS = (1, 3, 5, 10, 20)
_POP = {}


def v2_day_fields(day, view):
    """The per-day rendered values of the v2 prompt (A74), from the world's 7-day window."""
    rep = view["reported_deaths"]                                  # days 0 .. day-1
    m7 = float(view["awareness_signal"])                           # 7-day mean, days strictly before today
    t7 = day - 7
    m7_ago = float(rep[max(0, t7 - 7):t7].mean()) if t7 > 0 else 0.0
    recent, earlier = r2.death_sentences(day, m7, m7_ago)
    return (f"{view['N']:,}", str(day), recent, earlier, str(r2.half_up(float(rep.sum()))),
            f"{r2.half_up(100 * view['social_norm'])}%"), (m7, m7_ago)


class V2Stub(s11.CountingStub):
    """C53's counting stub with the v2 day fields; the same decision draws (stub probabilities)."""

    def __init__(self, probs, pop, full_render=False):
        super().__init__(probs, pop, full_render=False)
        self.hashes = [] if full_render else None
        self.day_t = []

    def decide(self, day, agents, view, rng):
        dyn, (m7, m7_ago) = v2_day_fields(day, view)
        self.days.append(dyn)
        self.day_t.append(day)
        act = view["action"][agents].astype(np.int64)
        self.keys.append((len(self.days) - 1) * 3630 + self.static[agents] * 3 + act)
        if self.hashes is not None:
            from perception import PerceptionV2
            rep, pop = view["reported_deaths"], self.pop
            for i in agents:
                p = PerceptionV2(deaths_7day_mean=m7, deaths_cumulative=float(rep.sum()), deaths_7day_mean_7d_ago=m7_ago,
                                 current_action=s11.ACT_NAME[int(view["action"][i])],
                                 social_norm=float(view["social_norm"]), age_band=int(pop.age_band[i]),
                                 vulnerability=float(pop.vulnerability[i]), occupation_flex=float(pop.occupation_flex[i]),
                                 response_efficacy=float(pop.response_efficacy[i]), population=int(view["N"]), day=int(day))
                text = r2.render(p)
                assert all(v in text for v in dyn[2:4])
                self.hashes.append(hashlib.sha256(text.encode("utf-8")).digest())
        u = rng.random(len(agents))
        return np.where(u < self.p_home, s11.STAY_HOME,
                        np.where(u < self.p_home + self.p_prec, s11.PRECAUTIONS, s11.NORMAL)).astype(np.int8)


def run_one(task, full_render=False):
    stub, seed = task
    from population import build_population
    from shared_world import run_shared_world
    if N not in _POP:
        _POP[N] = build_population(N=N, seed=0)
    d = V2Stub(STUBS[stub], _POP[N], full_render)
    t0 = time.time()
    o = run_shared_world(N=N, seed=seed, decision=d, days=600, f_D=_POP[N].vulnerability, window=7,
                         detection_rate=0.7, redecide_prob=0.3, stop_deciding_when_no_infection=True, **s11.SCEN[SC])
    keys = np.concatenate(d.keys) if d.keys else np.zeros(0, np.int64)
    uniq, k = np.unique(keys, return_counts=True)
    day_of_group = np.asarray(d.day_t, np.int64)[uniq // 3630]
    prev, exp_ = np.asarray(o["prevalence"]), np.asarray(o["exposed"])
    start_EI = np.concatenate([[10], (prev + exp_)[:-1]])            # start of day t = end of day t - 1
    return dict(task=task, decisions=int(len(keys)), group_day=day_of_group, group_k=k.astype(np.int64),
                prevalence=prev, start_EI=start_EI, keys=keys if full_render else None,
                hashes=d.hashes, dt=time.time() - t0)


def verify():
    for stub in STUBS:
        r = run_one((stub, 0), full_render=True)
        n_hash = len(set(r["hashes"]))
        n_pairs = len(set(zip(r["keys"].tolist(), r["hashes"])))
        ok = n_hash == len(r["group_k"]) == n_pairs and len(r["hashes"]) == r["decisions"]
        print(f"  {stub} N {N:,} seed 0: decisions {r['decisions']:,} (rendered {len(r['hashes']):,}); distinct by key "
              f"{len(r['group_k']):,}; distinct v2 prompt hashes {n_hash:,}; distinct (key, hash) pairs {n_pairs:,}; "
              f"one-to-one {ok}  ({r['dt']:.0f}s)")


def _work(task):
    r = run_one(task)
    return {k: v for k, v in r.items() if k not in ("keys", "hashes")}


def simulate():
    tasks = [(stub, s) for stub in STUBS for s in SEEDS]
    t0, res = time.time(), {}
    with mp.Pool(min(16, len(tasks))) as pool:
        for r in pool.imap_unordered(_work, tasks):
            res[r["task"]] = r
    print(f"{len(tasks)} runs {(time.time() - t0) / 60:.1f} min")
    arr = {}
    for (stub, s), r in res.items():
        for f in ("group_day", "group_k", "prevalence", "start_EI"):
            arr[f"{stub}|{s}#{f}"] = r[f]
        arr[f"{stub}|{s}#decisions"] = np.array([r["decisions"]])
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(NPZ, **arr)


def load_groups():
    """{stub: {phase: k array}} summed over seeds, plus per-seed checks."""
    z = np.load(NPZ)
    c53 = json.load(open(os.path.join(ROOT, "results", "step7", "step11_counts.json")))
    out, info = {}, {}
    for stub in STUBS:
        ref = c53[f"{stub}|{SC}|{N}"]
        per_phase = {p: [] for p in PHASES}
        all_k, dec = [], []
        for s in SEEDS:
            gd, gk = z[f"{stub}|{s}#group_day"], z[f"{stub}|{s}#group_k"]
            prev, sEI = z[f"{stub}|{s}#prevalence"], z[f"{stub}|{s}#start_EI"]
            ph, _ = phases_of(prev, {t: int(v) for t, v in enumerate(sEI)}, len(prev) - 1)
            lab = np.full(len(prev), -1)
            for j, p in enumerate(PHASES):
                lab[list(ph[p])] = j
            gl = lab[gd]
            assert (gl >= 0).all(), f"{stub} seed {s}: a decision day outside every phase"
            for j, p in enumerate(PHASES):
                per_phase[p].append(gk[gl == j])
            all_k.append(gk)
            dec.append(int(z[f"{stub}|{s}#decisions"][0]))
            assert dec[-1] == gk.sum()
        assert dec == ref["decisions_per_run"], f"{stub}: decisions differ from C53"
        out[stub] = {p: np.concatenate(v) for p, v in per_phase.items()}
        out[stub]["all"] = np.concatenate(all_k)
        info[stub] = dict(decisions=dec, c53_b=ref["distinct_per_run_total"], c53_distinct_per_run=ref["distinct_per_run"])
    return out, info


def score():
    from reuse_rule import group_sums, max_sd_passing
    g, info = load_groups()
    for stub in STUBS:
        k = g[stub]["all"]
        print(f"\n=== stub {stub}: decisions per run {info[stub]['decisions']} (= C53: True); total {sum(info[stub]['decisions']):,}")
        print("phase | groups | sum k | sum k^2 | K = sum k^2 / sum k | largest k")
        for p in PHASES + ("all",):
            sk, sk2 = group_sums(g[stub][p])
            print(f"{p} | {len(g[stub][p]):,} | {sk:,} | {sk2:,} | {sk2 / sk:.3f} | {g[stub][p].max()}")
        print(f"sum min(m, k) over the 10 runs (C53 column (b) = {info[stub]['c53_b']:,}):")
        for m in MS:
            v = int(np.minimum(k, m).sum())
            print(f"  m = {m:2d}: {v:,}  (x{v / info[stub]['c53_b']:.3f} of column (b))")
        assert int(np.minimum(k, 1).sum()) == info[stub]["c53_b"]
        print("largest per-prompt SD of A (percentage points; root of the phase's mean variance) that passes A78:")
        print("phase | m=1 b=0.05 | m=1 b=0.10 | m=1 b=0.15 | m=3 b=0.05 | m=3 b=0.10 | m=3 b=0.15")
        for p in PHASES:
            sk, sk2 = group_sums(g[stub][p])
            vals = [max_sd_passing(sk, sk2, m, b) for m in (1, 3) for b in (0.05, 0.10, 0.15)]
            print(f"{p} | " + " | ".join(f"{100 * v:.2f}" for v in vals))


if __name__ == "__main__":
    mp.freeze_support()
    for flag, fn in (("--verify", verify), ("--sim", simulate), ("--score", score)):
        if flag in sys.argv:
            fn()
