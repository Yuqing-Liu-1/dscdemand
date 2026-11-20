"""
Counterfactual response of downstream purchases to an upstream shock.

The distribution of households over (exposure bin, inventory bin) states is
pushed forward week by week under two scenarios that differ only in a
one-time extra upstream purchase. Exposure follows its Markov transition;
inventory follows a mix of the no-buy and buy transitions, weighted by the
model's own purchase probability in each state. The weekly response is the
difference in expected purchase probability; a zero shock gives exactly
zero response.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .states import StateSpace, soft_bin_weights

__all__ = ["propagate", "shift_exposure", "shock_response", "multipliers"]


def propagate(D: np.ndarray, space: StateSpace, ccp: np.ndarray) -> np.ndarray:
    """One-week update of a joint state distribution ``D`` (n_K x n_xi)."""
    buy = D * ccp
    return space.P_K.T @ (D - buy) @ space.P_xi0 + space.P_K.T @ buy @ space.P_xi1


def shift_exposure(D: np.ndarray, space: StateSpace, shock: float) -> np.ndarray:
    """Apply ``K' = eta * K + shock`` to every exposure bin, with soft binning."""
    D_new = np.zeros_like(D)
    for k, K in enumerate(space.K_reps):
        D_new += soft_bin_weights(space.eta * K + shock, space.K_reps)[:, None] * D[k]
    return D_new


def shock_response(
    space: StateSpace,
    ccps: list[np.ndarray],
    pi: np.ndarray,
    D0: np.ndarray,
    shock: float,
    weeks: int = 26,
) -> pd.DataFrame:
    """
    Weekly purchase response to a one-time upstream purchase of size ``shock``.

    Parameters
    ----------
    space
        State space of the fitted model.
    ccps
        Purchase-probability grid of each household type.
    pi
        Type shares; responses are averaged over types with these weights.
    D0
        Starting distribution over states (for example, the empirical one).
    shock
        Size of the extra upstream purchase.
    weeks
        Number of weeks after the shock.

    Returns
    -------
    pandas.DataFrame
        Columns ``week`` (1 = first week after the shock), ``p_shock``,
        ``p_baseline``, and ``response`` (their difference).
    """
    p_shock = np.zeros(weeks)
    p_base = np.zeros(weeks)
    for ccp, share in zip(ccps, pi, strict=True):
        D_s = shift_exposure(D0, space, shock)
        D_b = shift_exposure(D0, space, 0.0)
        for t in range(weeks):
            p_shock[t] += share * float((D_s * ccp).sum())
            p_base[t] += share * float((D_b * ccp).sum())
            D_s, D_b = propagate(D_s, space, ccp), propagate(D_b, space, ccp)
    return pd.DataFrame(
        {
            "week": np.arange(1, weeks + 1),
            "p_shock": p_shock,
            "p_baseline": p_base,
            "response": p_shock - p_base,
        }
    )


def multipliers(response) -> dict[str, float]:
    """
    Summarize a weekly response path.

    Returns
    -------
    dict
        ``gross``: sum of positive weekly responses (extra purchases).
        ``net``: sum of all weekly responses, after later reductions.
        ``offset_ratio``: share of the extra purchases that later
        reductions cancel (0 = none, 1 = all).

    Examples
    --------
    >>> multipliers([0.2, 0.1, -0.06])
    {'gross': 0.3, 'net': 0.24, 'offset_ratio': 0.2}
    """
    r = np.asarray(response, dtype=float)
    gross = float(r[r > 0].sum())
    negative = float(-r[r < 0].sum()) + 0.0
    return {
        "gross": round(gross, 12),
        "net": round(gross - negative, 12),
        "offset_ratio": round(negative / gross, 12) if gross > 0 else float("nan"),
    }
