"""Tests for stocks, grids, transitions, and soft binning."""

import numpy as np
import pandas as pd
import pytest

from dscdemand.states import (
    assign_bins,
    decay_transition,
    decayed_stock,
    discrete_support,
    estimate_decay,
    soft_bin_weights,
    stock_transition,
    zero_mass_grid,
)


def test_decayed_stock_known_values_per_household() -> None:
    df = pd.DataFrame({"household": [1, 1, 1, 2, 2], "x": [2.0, 0, 0, 1.0, 0]})
    assert decayed_stock(df, "x", 0.5).tolist() == [0.0, 2.0, 1.0, 0.0, 1.0]


def test_estimate_decay_recovers_ar1() -> None:
    rng = np.random.default_rng(0)
    x = [1.0]
    for _ in range(5000):
        x.append(0.7 * x[-1] + rng.normal(scale=0.1))
    df = pd.DataFrame({"household": 1, "x": x})
    assert estimate_decay(df, "x") == pytest.approx(0.7, abs=0.02)


def test_discrete_support_zero_point() -> None:
    reps, probs = discrete_support(np.array([0, 0, 0, 1, 2, 3]))
    assert reps[0] == 0
    assert probs[0] == 0.5
    assert probs.sum() == pytest.approx(1)


def test_discrete_support_positive_only_rejects_zero() -> None:
    with pytest.raises(ValueError):
        discrete_support(np.array([0.0, 1.0]), zero_point=False)


def test_zero_mass_grid_has_zero_bin() -> None:
    values = np.concatenate([np.zeros(50), np.linspace(0.1, 5, 50)])
    edges, reps = zero_mass_grid(values, 4)
    assert reps[0] == 0
    assert len(edges) == len(reps) + 1 == 5
    assert assign_bins(np.array([0.0]), edges)[0] == 0


def test_zero_mass_grid_without_positive_values_raises() -> None:
    with pytest.raises(ValueError):
        zero_mass_grid(np.zeros(10), 4)


def test_transitions_are_stochastic_matrices() -> None:
    edges, reps = zero_mass_grid(np.linspace(0, 5, 100), 5)
    P = stock_transition(edges, reps, 0.6, np.array([0.0, 2.0]), np.array([0.7, 0.3]))
    P0 = decay_transition(edges, reps, 0.6)
    np.testing.assert_allclose(P.sum(axis=1), 1)
    np.testing.assert_allclose(P0.sum(axis=1), 1)
    assert P0[0, 0] == 1  # zero stays zero without inflow


def test_assign_bins_clips_outside_values() -> None:
    edges = np.array([0.0, 1.0, 2.0])
    assert assign_bins(np.array([-5.0, 0.5, 99.0]), edges).tolist() == [0, 0, 1]


def test_soft_bin_weights() -> None:
    reps = np.array([0.0, 1.0, 2.0])
    np.testing.assert_allclose(soft_bin_weights(0.25, reps), [0.75, 0.25, 0])
    np.testing.assert_allclose(soft_bin_weights(9.0, reps), [0, 0, 1])
    np.testing.assert_allclose(soft_bin_weights(-1.0, reps), [1, 0, 0])
