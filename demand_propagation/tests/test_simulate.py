"""
Tests for the forward simulation in ``simulate.py``.

Overview:
- Purpose: Verify purchase_probability, simulate_response, and
  response_multipliers, including the two dynamical properties promised in
  paper/proposal.md: zero response without a shock, and identical results
  for identical inputs.
- Used by: `pytest` (run from the repository root; see README).
"""

import pandas as pd
import pytest

from demand_propagation.simulate import (
    purchase_probability,
    response_multipliers,
    simulate_response,
)

SMALL = {"n_weeks": 12, "n_households": 100}


def test_purchase_probability_known_value() -> None:
    """No exposure and no inventory gives logit 0, i.e. probability 0.5."""
    assert purchase_probability(0.0, 0.0, alpha=1.5, lam=0.6) == 0.5


def test_purchase_probability_direction() -> None:
    """More exposure raises the probability; more inventory lowers it."""
    base = purchase_probability(0.2, 1.0, alpha=1.5, lam=0.6)
    assert purchase_probability(0.8, 1.0, alpha=1.5, lam=0.6) > base
    assert purchase_probability(0.2, 3.0, alpha=1.5, lam=0.6) < base


def test_no_shock_gives_zero_response() -> None:
    """When the shocked scenario equals the baseline, the response is zero."""
    result = simulate_response(shock_weeks=(), seed=1, **SMALL)
    assert (result["response"] == 0).all()


def test_no_spillover_gives_zero_response() -> None:
    """With alpha = 0, sanitizer exposure cannot affect lotion purchases."""
    result = simulate_response(alpha=0.0, seed=1, **SMALL)
    assert (result["response"] == 0).all()


def test_simulation_is_reproducible() -> None:
    """The same inputs and seed always give the same result."""
    first = simulate_response(seed=3, **SMALL)
    second = simulate_response(seed=3, **SMALL)
    pd.testing.assert_frame_equal(first, second)


def test_shock_raises_purchases_the_next_week() -> None:
    """A week-0 sanitizer shock first shows up in week 1, as a positive response."""
    result = simulate_response(seed=0, **SMALL)
    assert result.loc[0, "response"] == 0
    assert result.loc[1, "response"] > 0


def test_output_shape_and_columns() -> None:
    """One row per week with the documented columns."""
    result = simulate_response(seed=0, **SMALL)
    assert list(result.columns) == ["week", "p_baseline", "p_shock", "response"]
    assert len(result) == SMALL["n_weeks"]


def test_multipliers_known_values() -> None:
    """Gross counts only positive weeks; net lets later reductions offset them."""
    assert response_multipliers([0.2, 0.1, -0.05]) == {"gross": 0.3, "net": 0.25}


def test_multipliers_net_never_exceeds_gross() -> None:
    """On a simulated path, net is at most gross, and gross is positive."""
    result = simulate_response(seed=0, **SMALL)
    multipliers = response_multipliers(result["response"])
    assert multipliers["gross"] > 0
    assert multipliers["net"] <= multipliers["gross"]


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"n_weeks": 0},
        {"n_households": 0},
        {"shock_weeks": (12,)},
        {"p_sanitizer": 1.5},
    ],
)
def test_simulate_response_invalid_inputs_raise(bad_kwargs: dict) -> None:
    """Invalid sizes, shock weeks, or probabilities raise ValueError."""
    kwargs = {**SMALL, **bad_kwargs}
    with pytest.raises(ValueError):
        simulate_response(**kwargs)
