"""
State construction: exposure and inventory stocks, grids, and transitions.

Two stocks summarize a household's history:

- exposure ``K_t``, built from upstream purchases ``S``:
  ``K_{t+1} = eta * K_t + S_t``;
- inventory ``xi_t``, built from downstream purchase volumes ``Q``:
  ``xi_{t+1} = rho * xi_t + d_t * Q_t``.

Each stock is recorded as of the start of a week (before that week's own
purchases), discretized into bins with a separate zero bin, and given a
Markov transition matrix for the dynamic program.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = [
    "ZERO_THRESHOLD",
    "StateSpace",
    "decayed_stock",
    "estimate_decay",
    "discrete_support",
    "zero_mass_grid",
    "stock_transition",
    "decay_transition",
    "assign_bins",
    "soft_bin_weights",
]

ZERO_THRESHOLD = 1e-3


@dataclass
class StateSpace:
    """Discretized exposure and inventory states with their transitions."""

    eta: float
    rho: float
    K_edges: np.ndarray
    K_reps: np.ndarray
    xi_edges: np.ndarray
    xi_reps: np.ndarray
    kappa: float
    P_K: np.ndarray
    P_xi0: np.ndarray
    P_xi1: np.ndarray


def decayed_stock(df: pd.DataFrame, col: str, decay: float) -> np.ndarray:
    """
    Stock at the start of each week: ``stock_{t+1} = decay * stock_t + x_t``.

    Parameters
    ----------
    df
        Panel sorted by household and week.
    col
        Column with the weekly inflow ``x_t``.
    decay
        Weekly retention rate.

    Returns
    -------
    numpy.ndarray
        Stock before each row's own inflow, starting from 0 per household.

    Examples
    --------
    >>> df = pd.DataFrame({"household": [1, 1, 1], "x": [1.0, 0.0, 0.0]})
    >>> decayed_stock(df, "x", 0.5).tolist()
    [0.0, 1.0, 0.5]
    """
    out = np.empty(len(df))
    values = df[col].to_numpy(dtype=float)
    for idx in df.groupby("household").indices.values():
        stock = 0.0
        for i in idx:
            out[i] = stock
            stock = decay * stock + values[i]
    return out


def estimate_decay(df: pd.DataFrame, col: str) -> float:
    """
    Weekly persistence of a series: no-intercept OLS of ``x_t`` on ``x_{t-1}``.

    The lag is taken within household. The estimate is clipped to
    [0.01, 0.99] so the stock always decays.
    """
    lag = df.groupby("household")[col].shift(1)
    mask = lag.notna().to_numpy()
    x = lag.to_numpy(dtype=float)[mask]
    y = df[col].to_numpy(dtype=float)[mask]
    if x @ x == 0:
        return 0.5
    return float(np.clip((x @ y) / (x @ x), 0.01, 0.99))


def discrete_support(
    values: np.ndarray, n_support: int = 4, zero_point: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """
    Discrete approximation of a non-negative distribution.

    With ``zero_point=True``, 0 gets its own support point with its observed
    share, and the positive values are split into ``n_support - 1``
    equal-probability quantile points. With ``zero_point=False`` all values
    must be positive and are split into ``n_support`` quantile points.
    """
    values = np.asarray(values, dtype=float)
    if zero_point:
        p_zero = float((values == 0).mean())
        pos = values[values > 0]
        n_pos = n_support - 1
        if len(pos) == 0:
            return np.array([0.0]), np.array([1.0])
        reps = np.quantile(pos, (np.arange(n_pos) + 0.5) / n_pos)
        probs = np.full(n_pos, (1 - p_zero) / n_pos)
        return np.concatenate([[0.0], reps]), np.concatenate([[p_zero], probs])
    if np.any(values <= 0):
        raise ValueError("Without a zero point, all values must be positive.")
    reps = np.quantile(values, (np.arange(n_support) + 0.5) / n_support)
    return reps, np.full(n_support, 1.0 / n_support)


def zero_mass_grid(
    values: np.ndarray,
    n_bins: int,
    zero_threshold: float = ZERO_THRESHOLD,
    winsor_pct: float = 99.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Bin edges and representative values with a separate zero bin.

    Values at or below ``zero_threshold`` form bin 0 (representative value
    exactly 0). The positive values, capped at their ``winsor_pct``
    percentile, are split into ``n_bins - 1`` quantile bins represented by
    their midpoints.

    Raises
    ------
    ValueError
        If the positive values are too concentrated to form two bins.
    """
    values = np.asarray(values, dtype=float)
    pos = values[values > zero_threshold]
    if len(pos) == 0:
        raise ValueError("No positive values to discretize.")
    pos = np.minimum(pos, np.percentile(pos, winsor_pct))
    pos_edges = np.quantile(pos, np.linspace(0, 1, n_bins))
    edges = np.unique(np.concatenate([[-1e-6], pos_edges]))
    edges[-1] += 1e-6
    if len(edges) < 3:
        raise ValueError("Positive values are too concentrated to discretize.")
    if len(edges) != n_bins + 1:
        warnings.warn(
            f"Requested {n_bins} bins; ties leave {len(edges) - 1}.", stacklevel=2
        )
    reps = (edges[:-1] + edges[1:]) / 2
    reps[0] = 0.0
    return edges, reps


def _bin_of(value: float, edges: np.ndarray) -> int:
    return int(np.clip(np.digitize(value, edges) - 1, 0, len(edges) - 2))


def stock_transition(
    edges: np.ndarray,
    reps: np.ndarray,
    decay: float,
    support: np.ndarray,
    probs: np.ndarray,
) -> np.ndarray:
    """Transition matrix for ``stock' = decay * stock + x``, x discrete."""
    n = len(reps)
    P = np.zeros((n, n))
    for i in range(n):
        for x, p in zip(support, probs, strict=True):
            P[i, _bin_of(decay * reps[i] + x, edges)] += p
    return P / P.sum(axis=1, keepdims=True)


def decay_transition(edges: np.ndarray, reps: np.ndarray, decay: float) -> np.ndarray:
    """Transition matrix for pure decay, ``stock' = decay * stock``."""
    n = len(reps)
    P = np.zeros((n, n))
    for i in range(n):
        P[i, _bin_of(decay * reps[i], edges)] = 1.0
    return P


def assign_bins(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Bin index of each value; values outside the grid go to the end bins."""
    idx = np.digitize(np.asarray(values, dtype=float), edges) - 1
    return np.clip(idx, 0, len(edges) - 2)


def soft_bin_weights(value: float, reps: np.ndarray) -> np.ndarray:
    """
    Split a value across the two nearest representative values.

    Linear interpolation instead of hard rounding, so two different shock
    sizes do not collapse onto the same bin. Values outside the grid put
    all weight on the end bin.

    Examples
    --------
    >>> soft_bin_weights(1.5, np.array([0.0, 1.0, 2.0])).tolist()
    [0.0, 0.5, 0.5]
    """
    reps = np.asarray(reps, dtype=float)
    w = np.zeros(len(reps))
    if value <= reps[0]:
        w[0] = 1.0
    elif value >= reps[-1]:
        w[-1] = 1.0
    else:
        hi = int(np.searchsorted(reps, value))
        frac = (value - reps[hi - 1]) / (reps[hi] - reps[hi - 1])
        w[hi - 1], w[hi] = 1.0 - frac, frac
    return w
