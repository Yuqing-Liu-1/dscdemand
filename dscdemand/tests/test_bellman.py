"""Tests for the Bellman solver and the parameter layout."""

import numpy as np
import pytest

from dscdemand.bellman import (
    EULER_GAMMA,
    BellmanNotConverged,
    choice_probabilities,
    expected_values,
    exposure_effect,
    solve_bellman,
)
from dscdemand.likelihood import ParamLayout

P = np.array([[0.9, 0.1], [0.2, 0.8]])
U0 = np.zeros((2, 2))
U1 = np.array([[0.5, -1.0], [1.0, 0.0]])


def test_exposure_effect_kink() -> None:
    np.testing.assert_allclose(
        exposure_effect(np.array([0.0, 1.0, 3.0]), 2.0, 0.5, 1.0), [0.0, 2.0, 3.0]
    )


def test_bellman_solution_is_a_fixed_point() -> None:
    beta = 0.9
    V = solve_bellman(U0, U1, P, P, P, beta)
    EV0, EV1 = expected_values(V, P, P, P, beta)
    v0, v1 = U0 + EV0, U1 + EV1
    np.testing.assert_allclose(V, np.logaddexp(v0, v1) + EULER_GAMMA, atol=1e-7)


def test_myopic_value_is_the_static_logsum() -> None:
    V = solve_bellman(U0, U1, P, P, P, beta=0.0)
    np.testing.assert_allclose(V, np.logaddexp(U0, U1) + EULER_GAMMA)


def test_choice_probabilities_are_logit() -> None:
    p = choice_probabilities(U0, U1, np.zeros((2, 2)), np.zeros((2, 2)))
    np.testing.assert_allclose(p, 1 / (1 + np.exp(-U1)))


def test_nonconvergence_raises() -> None:
    with pytest.raises(BellmanNotConverged):
        solve_bellman(U0, U1, P, P, P, beta=0.99, max_iter=2)


def test_param_layout_round_trip() -> None:
    layout = ParamLayout(("event",), ("a", "lam"), n_types=2)
    thetas = [
        {"a": 1, "gamma1": 2, "gamma2": 3, "lam": 4, "alpha": 5, "event": 6},
        {"a": -1, "gamma1": 2, "gamma2": 3, "lam": -4, "alpha": 5, "event": 6},
    ]
    vector = layout.pack(thetas)
    assert len(vector) == layout.size == 8
    assert [layout.theta(vector, k) for k in range(2)] == thetas
