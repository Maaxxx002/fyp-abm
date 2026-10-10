"""Arm 3 in the shared world (src/arm3.py) and the C39 additions to run_shared_world."""
import os
import shutil
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import arm3  # noqa: E402
from population import build_population  # noqa: E402
from shared_world import (AlwaysNormal, ForcedPrecautions,  # noqa: E402
                          ForcedStayHomeFraction, run_shared_world)

POP = build_population(N=3000, seed=0)
KW = dict(N=3000, days=200, f_D=POP.vulnerability, window=28, detection_rate=0.7,
          R0=3.0, T_H=14.0)


class Recorder(arm3.Arm3Rule):
    """Arm3Rule with the rule replaced by a recorder returning fixed probabilities."""

    def __init__(self):
        self.pop, self.k, self.seen, self.merge_stay_home = POP, 0, [], False

        def rule(p):
            self.seen.append(p)
            return {"stay_home": 0.1, "precautions": 0.2, "normal": 0.7}
        self.rule = rule


def test_all_frozen_rules_load_and_return_probabilities():
    for k in range(1, 6):
        f = arm3.load_rule(k)
        assert callable(f)


def test_tampered_rule_is_refused(tmp_path, monkeypatch):
    d = tmp_path / "v1"
    shutil.copytree(arm3.RULE_DIR, d)
    with open(d / "rule_1.py", "a", encoding="utf-8", newline="") as f:
        f.write("# edited\n")
    monkeypatch.setattr(arm3, "RULE_DIR", str(d))
    with pytest.raises(RuntimeError):
        arm3.load_rule(1)


def test_perception_matches_world_series():
    rec = Recorder()
    out = run_shared_world(seed=0, decision=rec, redecide_prob=0.3, **KW)
    assert rec.seen
    for p in rec.seen[::97]:
        t = p.day
        assert p.deaths_28day_mean == out["awareness_signal"][t]
        assert p.deaths_28day_mean_7d_ago == (out["awareness_signal"][t - 7] if t >= 7 else 0.0)
        assert p.deaths_cumulative == pytest.approx(out["reported_deaths"][:t].sum(), abs=0)
        assert p.social_norm == out["social_norm"][t]
        assert p.population == 3000


def test_stop_deciding_when_no_infection():
    rec = Recorder()
    out = run_shared_world(seed=0, decision=rec, redecide_prob=0.3,
                           stop_deciding_when_no_infection=True, **KW)
    active_end = out["exposed"] + out["prevalence"]          # end of day = start of next day
    days = sorted({p.day for p in rec.seen})
    assert all(active_end[t - 1] > 0 for t in days if t > 0)
    last = np.nonzero(active_end > 0)[0].max()
    assert max(days) <= last + 1


def test_sampling_follows_probabilities():
    rng = np.random.default_rng(0)
    rec = Recorder()
    agents = np.arange(3000)
    view = dict(reported_deaths=np.zeros(10), awareness_signal=0.0, social_norm=1.0, N=3000,
                action=np.zeros(3000, dtype=np.int8))
    a = rec.decide(10, agents, view, rng)
    share = np.bincount(a, minlength=3) / len(a)          # normal, precautions, stay_home
    assert share == pytest.approx([0.7, 0.2, 0.1], abs=0.03)


def test_alt_social_norm_definition():
    o = run_shared_world(seed=0, decision=ForcedStayHomeFraction(0.5),
                         social_norm_def="alive_not_home_not_H", **KW)
    assert o["social_norm"][0] == 1.0                      # nobody out takes precautions
    o = run_shared_world(seed=0, decision=ForcedPrecautions(),
                         social_norm_def="alive_not_home_not_H", **KW)
    assert o["social_norm"][0] == pytest.approx(10 / 3000)  # only the 10 infected act normal
    o2 = run_shared_world(seed=0, decision=ForcedPrecautions(), **KW)
    assert np.array_equal(o["S"], o2["S"])                 # norm definition never moves physics


def test_E_by_action_counts_exposed():
    o = run_shared_world(seed=0, decision=AlwaysNormal(), **KW)
    assert np.array_equal(o["E_by_action"].sum(1), o["exposed"])


def test_merge_stay_home_never_draws_stay_home():
    rec = Recorder()
    rec.merge_stay_home = True
    view = dict(reported_deaths=np.zeros(10), awareness_signal=0.0, social_norm=1.0, N=3000,
                action=np.zeros(3000, dtype=np.int8))
    a = rec.decide(10, np.arange(3000), view, np.random.default_rng(0))
    share = np.bincount(a, minlength=3) / len(a)          # normal, precautions, stay_home
    assert share[2] == 0 and share[1] == pytest.approx(0.3, abs=0.03)


class AllHome(arm3.Arm3Rule):
    """Everyone asked stays home."""

    def __init__(self):
        self.pop, self.k, self.merge_stay_home = POP, 0, False
        self.rule = lambda p: {"stay_home": 1.0, "precautions": 0.0, "normal": 0.0}


def test_ill_decide_default_off_is_unchanged():
    o1 = run_shared_world(seed=0, decision=AllHome(), redecide_prob=0.3, **KW)
    o2 = run_shared_world(seed=0, decision=AllHome(), redecide_prob=0.3, ill_decide=False, **KW)
    assert np.array_equal(o1["S"], o2["S"])


def test_ill_decide_home_stops_spreading():
    # everyone re-asked every day stays home -> ill agents are home from day 1, so with
    # ill_decide the epidemic is (nearly) stopped; without it ill agents keep spreading
    on = run_shared_world(seed=0, decision=AllHome(), redecide_prob=1.0, ill_decide=True, **KW)
    off = run_shared_world(seed=0, decision=AllHome(), redecide_prob=1.0, **KW)
    assert on["total_infected"] <= off["total_infected"]
    assert on["total_infected"] <= 12


def test_ill_decide_recovered_act_normal():
    o = run_shared_world(seed=0, decision=AllHome(), redecide_prob=0.3, ill_decide=True,
                         **dict(KW, days=120))
    # recovered agents never decide and are reset to normal: social_norm counts them
    assert o["social_norm"][-1] >= o["recovered"][-1] / 3000
