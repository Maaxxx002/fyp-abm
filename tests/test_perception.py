"""
Perception dataclass shape tests (Design_Spec_Perception_and_Population.md Sec 2).

No renderer exists yet (out of scope for this build), so there is nothing to test for
totality/coverage here -- that test (CLAUDE.md Test 3) belongs with the renderer. This file
only checks the vector's SHAPE: exactly the eleven main-design fields (the original twelve,
+ current_action (A40), - own_health (A43), - local_deaths_7d (A46), deaths_prev_period
-> deaths_28day_mean_7d_ago (A47)), frozen, and that `current_action`
accepts each of its three actions.
"""
import dataclasses

import pytest

from perception import Perception

EXPECTED_FIELDS = {
    # dynamic
    "deaths_28day_mean", "deaths_cumulative", "deaths_28day_mean_7d_ago",
    "current_action", "social_norm",
    # static
    "age_band", "vulnerability", "occupation_flex", "response_efficacy",
    # context
    "population", "day",
}


def _sample_perception(**overrides):
    defaults = dict(
        deaths_28day_mean=0.5,
        deaths_cumulative=12,
        deaths_28day_mean_7d_ago=0.3,
        current_action="normal",
        social_norm=0.66,
        age_band=7,
        vulnerability=0.0193,
        occupation_flex=0.6,
        response_efficacy=0.5,
        population=3000,
        day=100,
    )
    defaults.update(overrides)
    return Perception(**defaults)


def test_perception_has_exactly_the_designed_fields():
    actual = {f.name for f in dataclasses.fields(Perception)}
    assert actual == EXPECTED_FIELDS


def test_own_health_is_not_in_the_main_design_vector():
    # A43: constant (never_ill) for every deciding agent under A38 + A42; returns with E21.
    assert "own_health" not in {f.name for f in dataclasses.fields(Perception)}


def test_perception_is_frozen():
    p = _sample_perception()
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.day = 101


def test_perception_requires_every_field():
    with pytest.raises(TypeError):
        Perception(day=0)  # missing everything else


@pytest.mark.parametrize("current_action", ["stay_home", "precautions", "normal"])
def test_perception_accepts_every_action(current_action):
    p = _sample_perception(current_action=current_action)
    assert p.current_action == current_action
