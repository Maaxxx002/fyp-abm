"""
Tests for wiring per-agent response_efficacy into CBF's r (Decision_Register.md A13,
this build's new entry recording r_i = 1 - response_efficacy_i as a stated, unsourced
mapping). Covers the formula itself, its monotonicity, and that run_cbf_behaviour actually
accepts and uses a per-agent array instead of the old flat r_factor=0.5.

NOT covered here (deliberately, per this round's scope): the N=3,000/10,000/30,000
validation battery -- that is a separate step once this wiring is confirmed correct.
"""
import numpy as np
import pytest

from model import cbf_r_from_response_efficacy, run_cbf_behaviour
from population import build_population

R0 = 3.0  # CLAUDE.md settled value; model.py's run_cbf_behaviour default


def test_r_equals_one_minus_response_efficacy_for_a_few_agents():
    response_efficacy = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    r = cbf_r_from_response_efficacy(response_efficacy)
    np.testing.assert_allclose(r, 1.0 - response_efficacy)


def test_r_equals_one_minus_response_efficacy_for_a_real_population():
    pop = build_population(N=3000, seed=0)
    r = cbf_r_from_response_efficacy(pop.response_efficacy)
    np.testing.assert_allclose(r, 1.0 - pop.response_efficacy)


def test_effective_cautious_transmission_rate_strictly_decreases_with_response_efficacy():
    # "Effective transmission rate when cautious" = r_i * beta, beta = R0 * infectious_rate
    # (src/model.py's `transmission_rate`). Must strictly decrease as response_efficacy
    # rises from 0 to 1, for any fixed disease parameters.
    infectious_period_days = 6.0
    beta = R0 * (1.0 / infectious_period_days)

    response_efficacy = np.linspace(0.0, 1.0, 101)
    r = cbf_r_from_response_efficacy(response_efficacy)
    effective_rate = r * beta

    diffs = np.diff(effective_rate)
    assert np.all(diffs < 0), "effective cautious transmission rate must strictly decrease"


def test_run_cbf_behaviour_accepts_per_agent_response_efficacy():
    # Smoke test: the real Beta(2,2)-drawn population wires through end to end.
    pop = build_population(N=3000, seed=0)
    result = run_cbf_behaviour(
        N=3000, seed=0, response_efficacy=pop.response_efficacy,
        days=120, n_substeps=48,
    )
    assert result["S"].shape == (120,)
    assert np.all(np.isfinite(result["S"]))
    assert 0.0 <= result["S"][-1] <= 1.0


def test_run_cbf_behaviour_rejects_mismatched_response_efficacy_length():
    with pytest.raises(ValueError):
        run_cbf_behaviour(N=3000, seed=0, response_efficacy=np.full(10, 0.5), days=5)


def test_realised_population_average_r_near_gozzi_default():
    # Report, don't assume: Beta(2,2) has an expectation of 0.5, so the realised
    # population-average r should land near Gozzi's flat demo default (r=0.5, C13), but
    # this is checked against the actual draw, not asserted to equal 0.5 exactly.
    pop = build_population(N=3000, seed=0)
    r = cbf_r_from_response_efficacy(pop.response_efficacy)
    mean_r = r.mean()
    # Loose bound: this is a report-the-number check, not a tight equality assertion.
    assert 0.4 < mean_r < 0.6
