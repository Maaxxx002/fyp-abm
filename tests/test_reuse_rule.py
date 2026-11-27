"""
A78's synthetic tests for the reuse-rule calculator (src/reuse_rule.py), plus A81's choice of m.
"""
import math

import numpy as np
import pytest

import reuse_rule as rr

PH = ("early", "rising", "peak", "falling", "late")


def test_sigma_zero_gives_zero():
    sits = [[0.2, 0.2, 0.2], [0.5, 0.5, 0.5]]
    assert rr.phase_ratio(sits, rr.group_sums([50, 3, 7]), 1) == 0.0


def test_all_k_one_gives_zero():
    sits = [[0.1, 0.3], [0.2, 0.6]]
    assert rr.phase_ratio(sits, rr.group_sums([1] * 40), 1) == 0.0


def test_hand_computed_case():
    # situation 1: mu 0.2, sigma^2 0.02, b 0.16; situation 2: mu 0.2, sigma^2 0, b 0.16
    # mean sigma^2 0.01, mean b 0.16; k = 3, 1, 2: sum k 6, sum k^2 14
    # R(1) = 0.01 * (14 - 6) / (1 * 0.16 * 6) = 0.08 / 0.96
    r = rr.phase_ratio([[0.1, 0.3], [0.2, 0.2]], rr.group_sums([3, 1, 2]), 1)
    assert r == pytest.approx(0.08 / 0.96)


def test_m3_is_one_third_of_m1():
    sits, sums = [[0.1, 0.3, 0.2], [0.0, 0.4, 0.1]], rr.group_sums([9, 4, 1, 12])
    assert rr.phase_ratio(sits, sums, 3) == pytest.approx(rr.phase_ratio(sits, sums, 1) / 3)


def test_zero_variance_phase_passes_even_with_b_zero():
    assert rr.ratio(0.0, 0.0, 10, 50, 1) == 0.0


def _sums(sk, sk2):
    return {"s": {p: (sk, sk2) for p in PH}}


def test_choose_m_follows_a78_then_a81():
    sits = {p: [[0.1, 0.3]] for p in PH}            # sigma^2 0.02, b 0.16
    # R(1) = 0.02 * (K - 1) / 0.16 with K - 1 = (sk2 - sk) / sk
    assert rr.choose_m(sits, _sums(100, 500)) == 1          # K-1 = 4  -> R(1) 0.5
    assert rr.choose_m(sits, _sums(100, 1300)) == 3         # K-1 = 12 -> R(1) 1.5 (m = 2 would pass; A78 goes to 3)
    assert rr.choose_m(sits, _sums(100, 3400)) == 5         # K-1 = 33 -> R(1) 4.125 -> smallest passing m = 5
    assert rr.passes(rr.all_ratios(sits, _sums(100, 3400), 5)) and not rr.passes(rr.all_ratios(sits, _sums(100, 3400), 4))


def test_calls_and_max_sd():
    assert rr.calls([1, 2, 5, 30], 1) == 4 and rr.calls([1, 2, 5, 30], 3) == 1 + 2 + 3 + 3
    sd = rr.max_sd_passing(100, 500, 1, 0.16)               # K - 1 = 4: sigma^2 < 0.04
    assert sd == pytest.approx(0.2)
    assert rr.ratio(sd ** 2, 0.16, 100, 500, 1) == pytest.approx(1.0)
    assert rr.max_sd_passing(10, 10, 1, 0.1) == math.inf


def test_icc_hand_computed():
    # rows means 2 and 6, grand 4: MSB = 2 * 8 / 1 = 16, MSW = 4 / 2 = 2 -> ICC = 14 / 18
    icc, (lo, hi) = rr.icc_1_1([[1, 3], [5, 7]])
    assert icc == pytest.approx(14 / 18) and lo < icc < hi


def test_bootstrap_interval_contains_point_and_is_reproducible():
    rng = np.random.default_rng(0)
    sits = [list(np.clip(rng.normal(0.2, 0.05, 20), 0, 1)) for _ in range(4)]
    sums = rr.group_sums(rng.integers(1, 40, 500))
    a = rr.bootstrap_ratio(sits, sums, 1, n_boot=300)
    assert a == rr.bootstrap_ratio(sits, sums, 1, n_boot=300)
    assert a[0] <= rr.phase_ratio(sits, sums, 1) * 1.2 and a[1] >= rr.phase_ratio(sits, sums, 1) * 0.8


def test_two_level_bootstrap_is_reproducible_and_ordered():
    rng = np.random.default_rng(1)
    sits = [list(np.clip(rng.normal(mu, 0.05, 20), 0, 1)) for mu in (0.1, 0.2, 0.3, 0.4)]
    sums = rr.group_sums(rng.integers(1, 40, 500))
    a = rr.bootstrap_ratio_two_level(sits, sums, 1, n_boot=300)
    assert a == rr.bootstrap_ratio_two_level(sits, sums, 1, n_boot=300) and a[0] <= a[1]
