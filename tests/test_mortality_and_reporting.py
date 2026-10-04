"""
Tests for register C23's two additions to src/model.py: per-agent (age-based) f_D, and
death reporting (detection_rate, optionally with Gozzi's literal per-age-band integer cast).

The bit-identity tests load src/model.py as of commit de9e06a (before C23's additions and
A29's flat-r refactor) via git, so "current code" means the earlier code, not a re-run of the
new code against itself.
"""
import importlib.util
import pathlib
import subprocess

import numpy as np
import pytest

from model import run, run_cbf_behaviour
from population import build_population

ROOT = pathlib.Path(__file__).resolve().parents[1]
N_SMALL = 600
DAYS_SMALL = 200
PRE_CHANGE_COMMIT = "de9e06a"


def _load_pre_change_model(tmp_path):
    try:
        src = subprocess.run(
            ["git", "show", f"{PRE_CHANGE_COMMIT}:src/model.py"], cwd=ROOT,
            capture_output=True, check=True, text=True, encoding="utf8",
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("pre-change src/model.py not available from git")
    path = tmp_path / "model_head.py"
    path.write_text(src, encoding="utf8")
    spec = importlib.util.spec_from_file_location("model_head", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_run_defaults_bit_identical_to_head(tmp_path, seed):
    head = _load_pre_change_model(tmp_path)
    old = head.run(N=N_SMALL, seed=seed, days=DAYS_SMALL)
    new = run(N=N_SMALL, seed=seed, days=DAYS_SMALL)
    assert np.array_equal(old["S"], new["S"])
    assert np.array_equal(old["deaths"], new["deaths"])


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_cbf_defaults_bit_identical_to_head(tmp_path, seed):
    head = _load_pre_change_model(tmp_path)
    re = np.full(N_SMALL, 0.5)
    old = head.run_cbf_behaviour(N=N_SMALL, seed=seed, response_efficacy=re, days=DAYS_SMALL)
    new = run_cbf_behaviour(N=N_SMALL, seed=seed, days=DAYS_SMALL,
                            f_D=0.01, detection_rate=1.0)  # default r = 0.5
    assert np.array_equal(old["S"], new["S"])
    assert np.array_equal(old["deaths"], new["deaths"])
    assert np.array_equal(new["reported_deaths"], new["deaths"])


def test_constant_f_D_array_equals_scalar():
    a = run_cbf_behaviour(N=N_SMALL, seed=4, days=DAYS_SMALL, f_D=0.01)
    b = run_cbf_behaviour(N=N_SMALL, seed=4, days=DAYS_SMALL,
                          f_D=np.full(N_SMALL, 0.01))
    assert np.array_equal(a["S"], b["S"]) and np.array_equal(a["deaths"], b["deaths"])
    c = run(N=N_SMALL, seed=4, days=DAYS_SMALL, f_D=0.01)
    d = run(N=N_SMALL, seed=4, days=DAYS_SMALL, f_D=np.full(N_SMALL, 0.01))
    assert np.array_equal(c["S"], d["S"]) and np.array_equal(c["deaths"], d["deaths"])


def test_f_D_wrong_length_rejected():
    with pytest.raises(ValueError):
        run(N=N_SMALL, seed=0, days=5, f_D=np.full(N_SMALL - 1, 0.01))
    with pytest.raises(ValueError):
        run_cbf_behaviour(N=N_SMALL, seed=0,
                          days=5, f_D=np.full(N_SMALL + 1, 0.01))


def test_age_based_f_D_mean_matches_population_weighted_ifr():
    pop = build_population(N=3000, seed=0)
    assert round(float(pop.vulnerability.mean()), 6) == 0.009718


def test_age_based_f_D_actually_changes_who_dies():
    # Deaths only possible in agents with f_D > 0; with f_D zero for every agent but a
    # handful, nobody else can die. Checks the array is index-aligned, not just averaged.
    N = 2000
    f_D = np.zeros(N)
    out = run(N=N, seed=0, days=300, f_D=f_D)
    assert out["deaths"].sum() == 0
    out = run(N=N, seed=0, days=300, f_D=np.ones(N))
    assert out["deaths"].sum() == out["total_infected"]


def _cbf(**kw):
    pop = build_population(N=3000, seed=0)
    args = dict(N=3000, seed=0, days=300,
                f_D=pop.vulnerability)
    args.update(kw)
    return run_cbf_behaviour(**args), pop


def _last_simulated_day(out):
    # run_cbf_behaviour stops early once I, E and H are all empty; the signal is only
    # computed up to that day. A death on day t, or E/I present on day t, means the run
    # was still going on day t, so this is a safe (conservative) bound.
    active = (out["deaths"] > 0) | (out["exposed"] + out["prevalence"] > 0)
    return int(np.nonzero(active)[0].max())


@pytest.mark.parametrize("window", [1, 28])
def test_signal_is_window_mean_of_detection_times_realised(window):
    out, _ = _cbf(detection_rate=0.7, window=window)
    deaths = out["deaths"]
    assert deaths.sum() > 0
    np.testing.assert_array_equal(out["reported_deaths"], 0.7 * deaths)
    t_end = _last_simulated_day(out)
    assert t_end > window
    for t in range(1, t_end + 1):
        expected = (0.7 * deaths[max(0, t - window):t]).mean()
        assert out["awareness_signal"][t] == pytest.approx(expected, rel=1e-12, abs=1e-15)
    assert out["awareness_signal"][0] == 0.0


def test_truncated_reporting_matches_gozzi_literal_cast():
    pop = build_population(N=3000, seed=0)
    out, _ = _cbf(detection_rate=0.7, truncate_by_age_band=pop.age_band)
    by_band = out["deaths_by_band"]
    np.testing.assert_array_equal(by_band.sum(axis=1), out["deaths"])
    np.testing.assert_array_equal(out["reported_deaths"],
                                  np.floor(0.7 * by_band).sum(axis=1))
    # a single death in a band is reported as zero
    assert np.floor(0.7 * 1) == 0
    for t in range(1, _last_simulated_day(out) + 1):
        expected = out["reported_deaths"][max(0, t - 28):t].mean()
        assert out["awareness_signal"][t] == pytest.approx(expected, rel=1e-12, abs=1e-15)


def test_detection_never_changes_realised_deaths():
    # With behaviour off (beta_B=0) the signal is never used, so the realised trajectory
    # must be identical whatever the detection rate; only reported_deaths differs.
    a, _ = _cbf(beta_B=0.0, detection_rate=1.0)
    b, _ = _cbf(beta_B=0.0, detection_rate=0.7)
    assert np.array_equal(a["deaths"], b["deaths"])
    assert np.array_equal(a["S"], b["S"])
    np.testing.assert_array_equal(b["reported_deaths"], 0.7 * b["deaths"])
