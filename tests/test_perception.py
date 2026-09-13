"""
Perception dataclass shape tests (Design_Spec_Perception_and_Population.md Sec 2).

No renderer exists yet (out of scope for this build), so there is nothing to test for
totality/coverage here -- that test (CLAUDE.md Test 3) belongs with the renderer. This file
only checks the vector's SHAPE: exactly the twelve designed fields, frozen, and that
`own_health` accepts each of its three published observation states.
"""
import dataclasses

import pytest

from perception import Perception

EXPECTED_FIELDS = {
    # dynamic
    "own_health", "deaths_28day_mean", "deaths_cumulative", "deaths_prev_period",
    "local_deaths_7d", "social_norm",
    # static
    "age_band", "vulnerability", "occupation_flex", "response_efficacy",
    # context
    "population", "day",
}


def _sample_perception(**overrides):
    defaults = dict(
        own_health="never_ill",
        deaths_28day_mean=0.5,
        deaths_cumulative=12,
        deaths_prev_period=0.3,
        local_deaths_7d=1,
        social_norm=0.34,
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


def test_perception_is_frozen():
    p = _sample_perception()
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.day = 101


@pytest.mark.parametrize("own_health", ["never_ill", "currently_ill", "recovered"])
def test_perception_accepts_every_published_own_health_state(own_health):
    p = _sample_perception(own_health=own_health)
    assert p.own_health == own_health


def test_perception_requires_every_field():
    with pytest.raises(TypeError):
        Perception(own_health="never_ill")  # missing everything else
