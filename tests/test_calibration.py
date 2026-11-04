import numpy as np
import pytest

from odormap.calibration import expected_calibration_error, reliability_bins


def test_perfectly_calibrated_is_near_zero():
    rng = np.random.default_rng(0)
    s = rng.random(200_000)
    y = rng.random(200_000) < s
    assert expected_calibration_error(y, s) < 0.01


def test_known_ece_value():
    # all scores 0.9, half positive -> ECE = |0.5 - 0.9| = 0.4
    y = np.array([1, 0, 1, 0])
    s = np.full(4, 0.9)
    assert expected_calibration_error(y, s) == pytest.approx(0.4)


def test_bins_cover_endpoints():
    b = reliability_bins([0, 1], [0.0, 1.0], n_bins=10)
    assert b["count"][0] == 1 and b["count"][-1] == 1 and b["count"].sum() == 2
