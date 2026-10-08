"""
Tests for the analytical state-construction functions in ``state.py``.

Overview:
- Purpose: Verify exposure_index, inventory_transition, and bin_inventory.
- Used by: `pytest` (run from the repository root; see README).
- Adds: Confidence that the two closed-form Milestone 2 functions behave
  as specified in Eq. (7)-(11) of the underlying research paper.
"""

import pytest

from demand_propagation.state import bin_inventory, exposure_index, inventory_transition

# ---------------------------------------------------------------------------
# exposure_index
# ---------------------------------------------------------------------------


def test_exposure_index_all_zero_purchases() -> None:
    """No sanitizer purchases in the window should give an index of zero."""
    assert exposure_index([0] * 9, eta=0.7) == 0.0


def test_exposure_index_all_purchases_any_eta() -> None:
    """If every week had a purchase, the weighted average is exactly 1."""
    assert exposure_index([1] * 9, eta=0.3) == pytest.approx(1.0)


def test_exposure_index_eta_one_is_unweighted_average() -> None:
    """eta = 1 gives equal weights, i.e. a plain arithmetic mean."""
    purchases = [1, 0, 1, 0, 0, 0, 0, 0, 0]
    assert exposure_index(purchases, eta=1.0) == pytest.approx(2 / 9)


def test_exposure_index_known_value() -> None:
    """Known value: a single purchase at the most recent lag, eta = 0.7."""
    purchases = [1, 0, 0, 0, 0, 0, 0, 0, 0]
    weight_sum = sum(0.7**k for k in range(9))
    expected = 1.0 / weight_sum
    assert exposure_index(purchases, eta=0.7) == pytest.approx(expected)


@pytest.mark.parametrize("bad_len", [0, 8, 10])
def test_exposure_index_wrong_length_raises(bad_len: int) -> None:
    """purchases must have exactly 9 entries."""
    with pytest.raises(ValueError):
        exposure_index([0] * bad_len, eta=0.5)


def test_exposure_index_non_binary_entry_raises() -> None:
    """Entries other than 0/1 should raise ValueError."""
    with pytest.raises(ValueError):
        exposure_index([2, 0, 0, 0, 0, 0, 0, 0, 0], eta=0.5)


@pytest.mark.parametrize("bad_eta", [0.0, -0.1, 1.1])
def test_exposure_index_eta_out_of_range_raises(bad_eta: float) -> None:
    """eta must be in (0, 1]."""
    with pytest.raises(ValueError):
        exposure_index([0] * 9, eta=bad_eta)


# ---------------------------------------------------------------------------
# inventory_transition
# ---------------------------------------------------------------------------


def test_inventory_transition_paper_example_sequence() -> None:
    """Regression test reproducing the worked example in the paper (rho=0.84)."""
    stock = 0.0
    stock = inventory_transition(stock, purchased=True, rho=0.84)
    assert stock == pytest.approx(1.000, abs=1e-3)
    stock = inventory_transition(stock, purchased=False, rho=0.84)
    assert stock == pytest.approx(0.840, abs=1e-3)
    stock = inventory_transition(stock, purchased=False, rho=0.84)
    assert stock == pytest.approx(0.706, abs=1e-3)
    stock = inventory_transition(stock, purchased=True, rho=0.84)
    assert stock == pytest.approx(1.593, abs=1e-3)
    stock = inventory_transition(stock, purchased=False, rho=0.84)
    assert stock == pytest.approx(1.338, abs=1e-3)


def test_inventory_transition_no_purchase_pure_decay() -> None:
    """With no purchase, the stock is exactly rho times the previous stock."""
    assert inventory_transition(2.0, purchased=False, rho=0.5) == pytest.approx(1.0)


def test_inventory_transition_zero_stock_no_purchase_stays_zero() -> None:
    """Edge case: zero stock with no purchase stays at zero."""
    assert inventory_transition(0.0, purchased=False, rho=0.84) == pytest.approx(0.0)


def test_inventory_transition_negative_stock_raises() -> None:
    """prev_stock must be non-negative."""
    with pytest.raises(ValueError):
        inventory_transition(-1.0, purchased=True, rho=0.84)


@pytest.mark.parametrize("bad_rho", [0.0, 1.0, -0.1, 1.5])
def test_inventory_transition_rho_out_of_range_raises(bad_rho: float) -> None:
    """rho must be strictly between 0 and 1."""
    with pytest.raises(ValueError):
        inventory_transition(1.0, purchased=True, rho=bad_rho)


# ---------------------------------------------------------------------------
# bin_inventory
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stock", "expected_bin"),
    [
        (0.0, "0"),
        (0.49, "0"),
        (0.5, "1"),
        (1.0, "1"),
        (1.49, "1"),
        (1.5, "2"),
        (2.0, "2"),
        (2.49, "2"),
        (2.5, "3+"),
        (10.0, "3+"),
    ],
)
def test_bin_inventory_boundaries(stock: float, expected_bin: str) -> None:
    """Check every bin boundary from Eq. (10), including the edges."""
    assert bin_inventory(stock) == expected_bin


def test_bin_inventory_negative_stock_raises() -> None:
    """stock must be non-negative."""
    with pytest.raises(ValueError):
        bin_inventory(-0.01)
