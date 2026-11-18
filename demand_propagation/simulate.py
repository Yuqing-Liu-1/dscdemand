"""
simulate.py

Forward simulation of the lotion-purchase response to a sanitizer-exposure
shock.

This module implements the dynamical-system layer of the model described in
``paper/proposal.md`` (Section 2). Households are simulated week by week
under two scenarios that share the same random draws: a baseline, and a
shocked scenario with an extra sanitizer purchase in the shock week(s). The
weekly response is the difference in the average lotion-purchase
probability between the two scenarios. Because the draws are shared, the
response comes only from the shock.

The decision rule is the same fixed logistic rule used by
``synthetic_panel.generate_synthetic_panel``:

    Pr(buy lotion_t) = 1 / (1 + exp(-(alpha * E_t - lam * bin(stock_t))))

Examples
--------
>>> result = simulate_response(n_weeks=12, n_households=200, seed=0)
>>> list(result.columns)
['week', 'p_baseline', 'p_shock', 'response']
>>> multipliers = response_multipliers(result["response"])
>>> multipliers["net"] <= multipliers["gross"]
True
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .state import EXPOSURE_WINDOW, bin_inventory, exposure_index, inventory_transition

__all__ = ["purchase_probability", "simulate_response", "response_multipliers"]


def purchase_probability(
    exposure: float, stock: float, alpha: float, lam: float
) -> float:
    """
    Weekly lotion-purchase probability under the fixed logistic rule.

    Parameters
    ----------
    exposure
        Sanitizer-exposure index for the week (from ``exposure_index``).
    stock
        Latent lotion-inventory stock at the start of the week. Must be
        non-negative; it is binned with ``bin_inventory``.
    alpha
        Cross-category spillover coefficient (effect of exposure).
    lam
        Inventory-satiation coefficient (effect of the inventory bin).

    Returns
    -------
    float
        Purchase probability in (0, 1).

    Examples
    --------
    >>> purchase_probability(exposure=0.0, stock=0.0, alpha=1.5, lam=0.6)
    0.5
    """
    inv_bin = {"0": 0, "1": 1, "2": 2, "3+": 3}[bin_inventory(stock)]
    logit = alpha * exposure - lam * inv_bin
    return float(1.0 / (1.0 + np.exp(-logit)))


def simulate_response(
    n_weeks: int = 26,
    n_households: int = 500,
    shock_weeks: Sequence[int] = (0,),
    p_sanitizer: float = 0.15,
    alpha: float = 1.5,
    lam: float = 0.6,
    rho: float = 0.84,
    eta: float = 0.7,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Simulate the weekly lotion-purchase response to a sanitizer shock.

    Every household starts with no inventory and no sanitizer history. In
    both scenarios, sanitizer is bought at random with probability
    ``p_sanitizer`` each week, using the same draws. In the shocked
    scenario, every household also buys sanitizer in each week listed in
    ``shock_weeks``. Lotion purchases follow ``purchase_probability`` and
    update the inventory with ``inventory_transition``, again with draws
    shared across scenarios.

    Parameters
    ----------
    n_weeks
        Number of simulated weeks. Must be a positive integer.
    n_households
        Number of simulated households. Must be a positive integer.
    shock_weeks
        Weeks (0-based) in which the shocked scenario adds a sanitizer
        purchase. An empty sequence makes both scenarios identical.
    p_sanitizer
        Weekly probability of a sanitizer purchase, in [0, 1].
    alpha, lam
        Decision-rule coefficients (see ``purchase_probability``).
    rho
        Inventory retention rate, in (0, 1).
    eta
        Exposure-index decay parameter, in (0, 1].
    seed
        Random seed. The same inputs and seed always give the same result.

    Returns
    -------
    pandas.DataFrame
        One row per week with columns ``week``, ``p_baseline``, ``p_shock``
        (average purchase probabilities), and ``response``
        (``p_shock - p_baseline``).

    Raises
    ------
    ValueError
        If ``n_weeks`` or ``n_households`` is not a positive integer, if a
        shock week is outside ``[0, n_weeks)``, or if ``p_sanitizer`` is
        outside [0, 1]. ``rho`` and ``eta`` are checked by the state
        functions.

    Examples
    --------
    >>> no_shock = simulate_response(n_weeks=5, n_households=50, shock_weeks=())
    >>> bool((no_shock["response"] == 0).all())
    True
    """
    if n_weeks < 1:
        raise ValueError(f"n_weeks must be a positive integer, got {n_weeks}")
    if n_households < 1:
        raise ValueError(f"n_households must be a positive integer, got {n_households}")
    if any(not 0 <= w < n_weeks for w in shock_weeks):
        raise ValueError(
            f"shock_weeks must lie in [0, {n_weeks}), got {list(shock_weeks)}"
        )
    if not 0 <= p_sanitizer <= 1:
        raise ValueError(f"p_sanitizer must be in [0, 1], got {p_sanitizer}")

    rng = np.random.default_rng(seed)
    sanitizer_draws = rng.random((n_households, n_weeks)) < p_sanitizer
    lotion_draws = rng.random((n_households, n_weeks))

    shocked = sanitizer_draws.copy()
    shocked[:, list(shock_weeks)] = True

    def average_probabilities(sanitizer: np.ndarray) -> np.ndarray:
        probs = np.zeros((n_households, n_weeks))
        for h in range(n_households):
            stock = 0.0
            for t in range(n_weeks):
                lags = [
                    int(sanitizer[h, t - k]) if t - k >= 0 else 0
                    for k in range(1, EXPOSURE_WINDOW + 1)
                ]
                p = purchase_probability(exposure_index(lags, eta), stock, alpha, lam)
                probs[h, t] = p
                bought = bool(lotion_draws[h, t] < p)
                stock = inventory_transition(stock, purchased=bought, rho=rho)
        return probs.mean(axis=0)

    p_baseline = average_probabilities(sanitizer_draws)
    p_shock = average_probabilities(shocked)

    return pd.DataFrame(
        {
            "week": np.arange(n_weeks),
            "p_baseline": p_baseline,
            "p_shock": p_shock,
            "response": p_shock - p_baseline,
        }
    )


def response_multipliers(response: Sequence[float]) -> dict[str, float]:
    """
    Summarize a weekly response path as gross and net multipliers.

    Parameters
    ----------
    response
        Weekly change in lotion-purchase probability per household caused
        by the shock (the ``response`` column of ``simulate_response``).

    Returns
    -------
    dict
        ``gross``: sum of the positive weekly responses (extra purchases
        only). ``net``: sum of all weekly responses, so later reductions
        (households that bought earlier and now hold inventory) offset the
        extra purchases. Both are in expected lotion purchases per
        household over the simulated horizon.

    Examples
    --------
    >>> response_multipliers([0.2, 0.1, -0.05])
    {'gross': 0.3, 'net': 0.25}
    """
    values = np.asarray(response, dtype=float)
    return {
        "gross": round(float(values[values > 0].sum()), 12),
        "net": round(float(values.sum()), 12),
    }
