"""
Tests for the synthetic panel data generator in ``synthetic_panel.py``.

Overview:
- Purpose: Verify generate_synthetic_panel produces a well-formed,
  reproducible panel with the expected schema.
- Used by: `pytest` (run from the repository root; see README).
"""

import pytest

from demand_propagation.state import EXPOSURE_WINDOW
from demand_propagation.synthetic_panel import generate_synthetic_panel

EXPECTED_COLUMNS = (
    ["household_code", "week", "bought_sanitizer", "bought_lotion"]
    + [f"san_lag{k}" for k in range(1, EXPOSURE_WINDOW + 1)]
    + ["lot_lag1", "p_lotion"]
)


def test_generate_synthetic_panel_shape() -> None:
    """The panel should have one row per household-week."""
    panel, _truth = generate_synthetic_panel(n_households=4, n_weeks=6, seed=1)
    assert len(panel) == 4 * 6


def test_generate_synthetic_panel_schema() -> None:
    """Columns must match the schema expected by the state functions."""
    panel, _truth = generate_synthetic_panel(n_households=3, n_weeks=9, seed=1)
    assert list(panel.columns) == EXPECTED_COLUMNS


def test_generate_synthetic_panel_truth_records_parameters() -> None:
    """The truth dict should record the generating parameters, including seed."""
    _panel, truth = generate_synthetic_panel(n_households=2, n_weeks=5, seed=7)
    assert truth["seed"] == 7
    assert truth["n_households"] == 2
    assert truth["n_weeks"] == 5
    assert "alpha" in truth and "lam" in truth and "rho" in truth


def test_generate_synthetic_panel_reproducible_given_seed() -> None:
    """Two calls with the same seed must produce identical panels."""
    panel_a, _ = generate_synthetic_panel(n_households=5, n_weeks=12, seed=42)
    panel_b, _ = generate_synthetic_panel(n_households=5, n_weeks=12, seed=42)
    assert panel_a.equals(panel_b)


def test_generate_synthetic_panel_different_seed_differs() -> None:
    """Different seeds should (almost certainly) produce different data."""
    panel_a, _ = generate_synthetic_panel(n_households=5, n_weeks=12, seed=1)
    panel_b, _ = generate_synthetic_panel(n_households=5, n_weeks=12, seed=2)
    assert not panel_a["bought_lotion"].equals(panel_b["bought_lotion"])


def test_generate_synthetic_panel_binary_columns_are_0_1() -> None:
    """Purchase indicator columns must only contain 0/1 values."""
    panel, _truth = generate_synthetic_panel(n_households=6, n_weeks=15, seed=3)
    for col in ["bought_sanitizer", "bought_lotion", "lot_lag1"] + [
        f"san_lag{k}" for k in range(1, EXPOSURE_WINDOW + 1)
    ]:
        assert set(panel[col].unique()) <= {0, 1}


def test_generate_synthetic_panel_minimum_size() -> None:
    """Edge case: a single household for a single week still works."""
    panel, _truth = generate_synthetic_panel(n_households=1, n_weeks=1, seed=0)
    assert len(panel) == 1
    assert panel.loc[0, "lot_lag1"] == 0
    assert all(panel.loc[0, f"san_lag{k}"] == 0 for k in range(2, EXPOSURE_WINDOW + 1))


@pytest.mark.parametrize("bad_n_households", [0, -1])
def test_generate_synthetic_panel_invalid_n_households_raises(
    bad_n_households: int,
) -> None:
    with pytest.raises(ValueError):
        generate_synthetic_panel(n_households=bad_n_households, n_weeks=5, seed=0)


@pytest.mark.parametrize("bad_n_weeks", [0, -3])
def test_generate_synthetic_panel_invalid_n_weeks_raises(bad_n_weeks: int) -> None:
    with pytest.raises(ValueError):
        generate_synthetic_panel(n_households=5, n_weeks=bad_n_weeks, seed=0)


@pytest.mark.parametrize("bad_rho", [0.0, 1.0, -0.2])
def test_generate_synthetic_panel_invalid_rho_raises(bad_rho: float) -> None:
    with pytest.raises(ValueError):
        generate_synthetic_panel(n_households=2, n_weeks=5, seed=0, rho=bad_rho)
