from slm_lab.lib import math_util
import numpy as np
import pytest
import torch


def test_calc_gaes():
    rewards = torch.tensor([1., 0., 1., 1., 0., 1., 1., 1.])
    dones = torch.tensor([0., 0., 1., 1., 0., 0., 0., 0.])
    v_preds = torch.tensor([1.1, 0.1, 1.1, 1.1, 0.1, 1.1, 1.1, 1.1, 1.1])
    assert len(v_preds) == len(rewards) + 1  # includes last state
    gamma = 0.99
    lam = 0.95
    gaes = math_util.calc_gaes(rewards, dones, v_preds, gamma, lam)
    res = torch.tensor([0.84070045, 0.89495, -0.1, -0.1, 3.616724, 2.7939649, 1.9191545, 0.989])
    # use allclose instead of equal to account for atol
    assert torch.allclose(gaes, res)


@pytest.mark.parametrize('vec,res', [
    ([1, 1, 1], [False, False, False]),
    ([1, 1, 2], [False, False, True]),
    ([[1, 1], [1, 1], [1, 2]], [False, False, True]),
])
def test_is_outlier(vec, res):
    assert np.array_equal(math_util.is_outlier(vec), res)


@pytest.mark.parametrize('start_val, end_val, start_step, end_step, step, correct', [
    (0.1, 0.0, 0, 100, 0, 0.1),
    (0.1, 0.0, 0, 100, 50, 0.05),
    (0.1, 0.0, 0, 100, 100, 0.0),
    (0.1, 0.0, 0, 100, 150, 0.0),
    (0.1, 0.0, 100, 200, 50, 0.1),
    (0.1, 0.0, 100, 200, 100, 0.1),
    (0.1, 0.0, 100, 200, 150, 0.05),
    (0.1, 0.0, 100, 200, 200, 0.0),
    (0.1, 0.0, 100, 200, 250, 0.0),
])
def test_linear_decay(start_val, end_val, start_step, end_step, step, correct):
    assert math_util.linear_decay(start_val, end_val, start_step, end_step, step) == correct


@pytest.mark.parametrize('start_val, end_val, start_step, end_step, step, correct', [
    (1.0, 0.0, 0, 100, 0, 1.0),
    (1.0, 0.0, 0, 100, 5, 0.9),
    (1.0, 0.0, 0, 100, 10, 0.81),
    (1.0, 0.0, 0, 100, 25, 0.59049),
    (1.0, 0.0, 0, 100, 50, 0.3486784401),
    (1.0, 0.0, 0, 100, 100, 0.0),
    (1.0, 0.0, 0, 100, 150, 0.0),
    (1.0, 0.0, 100, 200, 0, 1.0),
    (1.0, 0.0, 100, 200, 50, 1.0),
    (1.0, 0.0, 100, 200, 100, 1.0),
    (1.0, 0.0, 100, 200, 105, 0.9),
    (1.0, 0.0, 100, 200, 125, 0.59049),
    (1.0, 0.0, 100, 200, 200, 0.0),
    (1.0, 0.0, 100, 200, 250, 0.0),
])
def test_rate_decay(start_val, end_val, start_step, end_step, step, correct):
    np.testing.assert_almost_equal(math_util.rate_decay(start_val, end_val, start_step, end_step, step), correct)
