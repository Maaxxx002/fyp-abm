"""
Population construction tests (Design_Spec_Perception_and_Population.md Sec 6).

Covers: the quota is exact (not a noisy multinomial draw), vulnerability is a zero-free-
parameter function of age_band, the two free distributions (occupation_flex, response_efficacy)
are actually configurable rather than hardcoded, and the population-weighted IFR reproduces the
already-published register figure (0.9718%) as a sourcing check on the transcribed IFR_10age
and quota-count constants.
"""
import numpy as np
import pytest

from population import (
    AGE_BAND_COUNTS_N3000,
    DEFAULT_RETIRED_AGE_BANDS,
    DEFAULT_SCHOOL_AGE_BANDS,
    IFR_10AGE,
    N_AGE_BANDS,
    build_population,
)


def test_age_band_counts_sum_to_3000():
    assert sum(AGE_BAND_COUNTS_N3000) == 3000


def test_build_population_age_band_matches_quota_exactly():
    pop = build_population(N=3000, seed=0)
    counts = np.bincount(pop.age_band, minlength=N_AGE_BANDS)
    assert counts.tolist() == AGE_BAND_COUNTS_N3000


def test_vulnerability_is_deterministic_function_of_age_band():
    pop = build_population(N=3000, seed=0)
    np.testing.assert_array_equal(pop.vulnerability, IFR_10AGE[pop.age_band])


def test_population_weighted_ifr_matches_register():
    # Decision_Register.md B2 / CLAUDE.md settled numbers: population-weighted IFR = 0.9718%.
    pop = build_population(N=3000, seed=0)
    weighted_ifr = pop.vulnerability.mean()
    assert weighted_ifr == pytest.approx(0.009718, abs=1e-5)


def test_school_and_retired_bands_get_fixed_occupation_flex():
    pop = build_population(N=3000, seed=0)
    is_school = np.isin(pop.age_band, list(DEFAULT_SCHOOL_AGE_BANDS))
    is_retired = np.isin(pop.age_band, list(DEFAULT_RETIRED_AGE_BANDS))
    assert np.all(pop.occupation_flex[is_school] == 0.5)
    assert np.all(pop.occupation_flex[is_retired] == 1.0)


def test_working_age_occupation_flex_is_drawn_and_bounded():
    pop = build_population(N=3000, seed=0)
    is_school = np.isin(pop.age_band, list(DEFAULT_SCHOOL_AGE_BANDS))
    is_retired = np.isin(pop.age_band, list(DEFAULT_RETIRED_AGE_BANDS))
    is_working = ~is_school & ~is_retired
    working_values = pop.occupation_flex[is_working]
    assert working_values.size > 0
    assert np.all((working_values >= 0) & (working_values <= 1))
    assert working_values.std() > 0  # actually drawn, not a second fixed constant


def test_response_efficacy_drawn_for_everyone_and_bounded():
    pop = build_population(N=3000, seed=0)
    assert pop.response_efficacy.shape == (3000,)
    assert np.all((pop.response_efficacy >= 0) & (pop.response_efficacy <= 1))
    assert pop.response_efficacy.std() > 0


def test_build_population_is_reproducible_given_same_seed():
    pop_a = build_population(N=3000, seed=42)
    pop_b = build_population(N=3000, seed=42)
    np.testing.assert_array_equal(pop_a.age_band, pop_b.age_band)
    np.testing.assert_array_equal(pop_a.occupation_flex, pop_b.occupation_flex)
    np.testing.assert_array_equal(pop_a.response_efficacy, pop_b.response_efficacy)


def test_different_seeds_give_different_free_draws():
    pop_a = build_population(N=3000, seed=1)
    pop_b = build_population(N=3000, seed=2)
    assert not np.array_equal(pop_a.response_efficacy, pop_b.response_efficacy)


def test_occupation_flex_beta_is_configurable_not_hardcoded():
    pop_default = build_population(N=3000, seed=0)
    pop_uniform = build_population(N=3000, seed=0, occupation_flex_beta=(1.0, 1.0))
    is_school = np.isin(pop_default.age_band, list(DEFAULT_SCHOOL_AGE_BANDS))
    is_retired = np.isin(pop_default.age_band, list(DEFAULT_RETIRED_AGE_BANDS))
    is_working = ~is_school & ~is_retired
    assert not np.array_equal(
        pop_default.occupation_flex[is_working], pop_uniform.occupation_flex[is_working]
    )


def test_response_efficacy_beta_is_configurable_not_hardcoded():
    pop_default = build_population(N=3000, seed=0)
    pop_uniform = build_population(N=3000, seed=0, response_efficacy_beta=(1.0, 1.0))
    assert not np.array_equal(pop_default.response_efficacy, pop_uniform.response_efficacy)


def test_school_retired_band_assignment_is_configurable_not_hardcoded():
    # The 60-69 boundary is an explicitly unresolved design choice (module docstring / this
    # build's report) -- verify the split is actually driven by the arguments, not hardcoded.
    pop_band7_retired = build_population(N=3000, seed=0)
    pop_band7_working = build_population(
        N=3000, seed=0,
        school_age_bands=frozenset({0, 1}),
        retired_age_bands=frozenset({8, 9}),  # band 7 now falls into "working"
    )
    band7_mask = pop_band7_retired.age_band == 7
    assert np.all(pop_band7_retired.occupation_flex[band7_mask] == 1.0)
    assert not np.all(pop_band7_working.occupation_flex[band7_mask] == 1.0)


def test_rejects_unsourced_N():
    with pytest.raises(NotImplementedError):
        build_population(N=1000)
