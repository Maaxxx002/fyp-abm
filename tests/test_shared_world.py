"""
Shared world (register A37-A41): physics and random-number equivalence checks, small and fast.
The full-scale versions are Checks 1-3 (experiments/step4_shared_world_checks.py, register C31).
"""
import numpy as np
import pytest

from model import run, run_cbf_behaviour, I
from population import build_population
from shared_world import (
    AlwaysNormal, CBFArm1, ForcedPrecautions, ForcedStayHomeFraction, DecisionFunction,
    NORMAL, PRECAUTIONS, STAY_HOME, run_shared_world,
)

SERIES = ("S", "prevalence", "incidence", "deaths")


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_always_normal_is_bit_identical_to_run(seed):
    a = run(N=2000, seed=seed, days=200)
    b = run_shared_world(N=2000, seed=seed, decision=AlwaysNormal(), days=200)
    for k in SERIES:
        assert np.array_equal(a[k], b[k]), k


@pytest.mark.parametrize("seed", [0, 1])
def test_cbf_adapter_is_bit_identical_to_run_cbf_behaviour(seed):
    pop = build_population(N=3000, seed=0)
    kw = dict(N=3000, seed=seed, days=150, f_D=pop.vulnerability, window=28,
              detection_rate=0.7)
    a = run_cbf_behaviour(**kw, beta_B=0.5, mu_B=0.01, gamma_beh=1.0, r=0.5)
    b = run_shared_world(**kw, decision=CBFArm1(beta_B=0.5, mu_B=0.01, gamma_beh=1.0))
    for k in SERIES + ("reported_deaths", "awareness_signal", "exposed"):
        assert np.array_equal(a[k], b[k]), k
    # run_cbf_behaviour stops filling SB after its early break; run_shared_world forward-fills
    last = int(np.flatnonzero(a["SB"] > 0).max())
    assert np.array_equal(a["SB"][:last + 1], b["SB"][:last + 1])
    assert a["SB"].max() > 0  # behaviour actually switched on


def test_cbf_never_stays_home():
    pop = build_population(N=3000, seed=0)
    out = run_shared_world(N=3000, seed=0, decision=CBFArm1(), days=150, f_D=pop.vulnerability)
    assert out["S_by_action"][:, STAY_HOME].max() == 0


def test_everyone_home_means_no_infection():
    out = run_shared_world(N=2000, seed=0, decision=ForcedStayHomeFraction(1.0), days=60)
    assert out["incidence"].sum() == 0


def test_stay_home_fraction_is_fixed_and_exact():
    out = run_shared_world(N=2000, seed=3, decision=ForcedStayHomeFraction(0.5), days=60)
    home = out["S_by_action"][:, STAY_HOME]
    assert home[0] == round(0.5 * (2000 - 10))
    assert np.all(home == home[0])  # never infected, never changes


def test_forced_precautions_covers_every_susceptible():
    out = run_shared_world(N=2000, seed=0, decision=ForcedPrecautions(), days=60)
    assert np.all(out["S_by_action"][:, NORMAL] == 0)


class _AlwaysStayHomeRedeciding(DecisionFunction):
    redecides = True

    def decide(self, day, agents, view, rng):
        assert np.all(view["own_health"][agents] == 0), "a non-never_ill agent was asked"
        return np.full(len(agents), STAY_HOME, dtype=np.int8)


class _AlwaysNormalRedeciding(DecisionFunction):
    redecides = True

    def __init__(self):
        self.asked_non_never_ill = 0

    def decide(self, day, agents, view, rng):
        self.asked_non_never_ill += int(np.count_nonzero(view["own_health"][agents] != 0))
        return np.full(len(agents), NORMAL, dtype=np.int8)


def test_redeciding_requires_explicit_cadence():
    with pytest.raises(ValueError):
        run_shared_world(N=500, seed=0, decision=_AlwaysStayHomeRedeciding(), days=5)


def test_everyone_home_from_day_0_gives_no_incidence():
    out = run_shared_world(N=1000, seed=0, decision=_AlwaysStayHomeRedeciding(), days=30,
                           redecide_prob=1.0)
    assert out["incidence"].sum() == 0


def test_ill_and_recovered_agents_are_never_asked():
    # A38 + A42: over a full epidemic, re-asked every day, only never_ill agents are asked.
    f = _AlwaysNormalRedeciding()
    out = run_shared_world(N=1000, seed=0, decision=f, days=200, redecide_prob=1.0)
    assert out["recovered"].max() > 0 and out["prevalence"].max() > 0
    assert f.asked_non_never_ill == 0


def test_social_norm_is_cbf_relaxation_term():
    # A44: (S_normal + R) / N, the quantity CBF's relaxation rate multiplies by mu_B.
    pop = build_population(N=3000, seed=0)
    out = run_shared_world(N=3000, seed=0, decision=CBFArm1(), days=120, f_D=pop.vulnerability)
    assert out["social_norm"][0] == (3000 - 10) / 3000
    assert out["social_norm"].min() < out["social_norm"][0]


def test_stay_home_is_not_counted_as_normal_in_social_norm():
    out = run_shared_world(N=2000, seed=0, decision=ForcedStayHomeFraction(1.0), days=5)
    # every susceptible is home, so only recovered agents count as normal
    assert out["social_norm"][0] == 0.0
    assert np.all(out["social_norm"][1:] == out["recovered"][:-1] / 2000)
