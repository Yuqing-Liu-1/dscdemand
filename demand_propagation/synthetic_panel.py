"""
synthetic_panel.py

Generate a synthetic ("phantom") household-week purchase panel shaped like
the restricted Nielsen Consumer Panel data used in the underlying research,
without containing any real household records.

The column schema (household_code, week, bought_sanitizer, bought_lotion,
san_lag1..san_lag9, lot_lag1, p_lotion) mirrors the real panel's structure
so that the state-construction functions in ``state.py`` can be exercised
on data that looks like the real thing. Purchase behavior is generated from
a simple, known logistic process parameterized by (alpha, lam, rho); the
generating parameters are returned in a ``truth`` dictionary, following the
same "known model -> synthetic data -> hidden truth" pattern used in the
course's analytical-modeling unit (``generate_dataset.py``).

Examples
--------
>>> panel, truth = generate_synthetic_panel(n_households=5, n_weeks=12, seed=42)
>>> sorted(panel.columns)[:3]
['bought_lotion', 'bought_sanitizer', 'household_code']
>>> truth["seed"]
42
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .state import EXPOSURE_WINDOW, bin_inventory, exposure_index, inventory_transition

__all__ = ["generate_synthetic_panel"]

_BIN_TO_INT = {"0": 0, "1": 1, "2": 2, "3+": 3}
_WEEK_START = "2019-01-06"


def _lag_window(history: list[int], t: int) -> list[int]:
    """Build the 9-entry lag window ``[san_{t-1}, ..., san_{t-9}]`` for week t.

    Weeks before the start of the panel are treated as no purchase
    (``xi*_i0 = 0`` boundary convention from Eq. 8).
    """
    return [history[t - k] if t - k >= 0 else 0 for k in range(1, EXPOSURE_WINDOW + 1)]


def generate_synthetic_panel(
    n_households: int = 50,
    n_weeks: int = 20,
    seed: int = 42,
    p_sanitizer: float = 0.15,
    alpha: float = 1.5,
    lam: float = 0.6,
    rho: float = 0.84,
    price_mean: float = 5.0,
    price_sd: float = 1.0,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    Generate a synthetic household-week sanitizer/lotion purchase panel.

    Parameters
    ----------
    n_households
        Number of synthetic households. Must be a positive integer.
    n_weeks
        Number of weekly periods per household. Must be a positive integer.
    seed
        Random seed for reproducible generation.
    p_sanitizer
        Weekly probability of a sanitizer purchase (exogenous). Must be in
        (0, 1).
    alpha
        Cross-category spillover coefficient used to generate lotion
        purchase probability (Eq. 12 style).
    lam
        Inventory-satiation coefficient used to generate lotion purchase
        probability.
    rho
        Inventory depreciation retention rate, passed to
        :func:`state.inventory_transition`. Must be in (0, 1).
    price_mean, price_sd
        Mean and standard deviation of the (purely synthetic) lotion price.

    Returns
    -------
    pandas.DataFrame
        Household-week panel with columns: ``household_code``, ``week``,
        ``bought_sanitizer``, ``bought_lotion``, ``san_lag1``..``san_lag9``,
        ``lot_lag1``, ``p_lotion``.
    dict
        Dictionary of the generating parameters (the "truth"), including
        ``alpha``, ``lam``, ``rho``, ``p_sanitizer``, ``seed``.

    Raises
    ------
    ValueError
        If ``n_households`` or ``n_weeks`` is not a positive integer, or if
        ``p_sanitizer`` or ``rho`` is not in (0, 1).

    Examples
    --------
    >>> panel, truth = generate_synthetic_panel(n_households=3, n_weeks=10, seed=0)
    >>> len(panel) == 3 * 10
    True
    """
    if n_households < 1:
        raise ValueError(f"n_households must be a positive integer, got {n_households}")
    if n_weeks < 1:
        raise ValueError(f"n_weeks must be a positive integer, got {n_weeks}")
    if not (0 < p_sanitizer < 1):
        raise ValueError(f"p_sanitizer must be in (0, 1), got {p_sanitizer}")
    if not (0 < rho < 1):
        raise ValueError(f"rho must be in (0, 1), got {rho}")

    rng = np.random.default_rng(seed)
    weeks = pd.date_range(start=_WEEK_START, periods=n_weeks, freq="W-SUN")

    rows: list[dict[str, object]] = []

    for h in range(n_households):
        household_code = str(900000 + h)

        san_history = (rng.random(n_weeks) < p_sanitizer).astype(int).tolist()
        lot_history: list[int] = []
        stock = 0.0

        for t in range(n_weeks):
            lag_window = _lag_window(san_history, t)
            exposure = exposure_index(lag_window, eta=0.7)
            inv_bin = _BIN_TO_INT[bin_inventory(stock)]

            logit = alpha * exposure - lam * inv_bin
            prob = 1.0 / (1.0 + np.exp(-logit))
            bought_lotion = int(rng.random() < prob)

            lot_lag1 = lot_history[t - 1] if t > 0 else 0
            price = float(rng.normal(price_mean, price_sd))

            row: dict[str, object] = {
                "household_code": household_code,
                "week": weeks[t],
                "bought_sanitizer": san_history[t],
                "bought_lotion": bought_lotion,
                "lot_lag1": lot_lag1,
                "p_lotion": round(price, 2),
            }
            for k, lag_value in enumerate(lag_window, start=1):
                row[f"san_lag{k}"] = lag_value

            rows.append(row)

            lot_history.append(bought_lotion)
            stock = inventory_transition(stock, purchased=bool(bought_lotion), rho=rho)

    column_order = (
        ["household_code", "week", "bought_sanitizer", "bought_lotion"]
        + [f"san_lag{k}" for k in range(1, EXPOSURE_WINDOW + 1)]
        + ["lot_lag1", "p_lotion"]
    )
    panel = pd.DataFrame(rows)[column_order]

    truth = {
        "n_households": n_households,
        "n_weeks": n_weeks,
        "seed": seed,
        "p_sanitizer": p_sanitizer,
        "alpha": alpha,
        "lam": lam,
        "rho": rho,
        "price_mean": price_mean,
        "price_sd": price_sd,
    }

    return panel, truth
