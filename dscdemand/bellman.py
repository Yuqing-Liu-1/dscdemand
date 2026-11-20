"""
Bellman solver for the binary buy / no-buy dynamic program.

The state is the (exposure bin, inventory bin) pair. Flow utility of buying
is ``u1``; not buying is normalized to ``u0 = 0``. With type-I extreme value
taste shocks, the expected value function solves

    V(s) = log(exp(u0 + beta * E[V | s, 0]) + exp(u1 + beta * E[V | s, 1])) + gamma

where ``gamma`` is Euler's constant. Price and covariates enter current
utility only; the continuation value is solved once at reference values.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "EULER_GAMMA",
    "BellmanNotConverged",
    "exposure_effect",
    "solve_bellman",
    "expected_values",
    "choice_probabilities",
]

EULER_GAMMA = 0.5772156649015329


class BellmanNotConverged(RuntimeError):
    """Raised when value-function iteration does not converge."""


def exposure_effect(
    K: np.ndarray, gamma1: float, gamma2: float, kappa: float
) -> np.ndarray:
    """
    Piecewise-linear effect of exposure, with slope change at ``kappa``.

    Examples
    --------
    >>> exposure_effect(np.array([1.0, 3.0]), 1.0, 0.5, 2.0).tolist()
    [1.0, 2.5]
    """
    return gamma1 * np.minimum(K, kappa) + gamma2 * np.maximum(K - kappa, 0.0)


def _expected_next(V: np.ndarray, P_K: np.ndarray, P_xi: np.ndarray) -> np.ndarray:
    return P_K @ V @ P_xi.T


def solve_bellman(
    u0: np.ndarray,
    u1: np.ndarray,
    P_K: np.ndarray,
    P_xi0: np.ndarray,
    P_xi1: np.ndarray,
    beta: float,
    tol: float = 1e-8,
    max_iter: int = 5000,
) -> np.ndarray:
    """
    Value-function iteration on the (exposure, inventory) grid.

    Returns
    -------
    numpy.ndarray
        Expected value function, shape ``(n_K, n_xi)``.

    Raises
    ------
    BellmanNotConverged
        If the iteration does not reach ``tol`` within ``max_iter`` steps.
    """
    V = np.zeros(u0.shape)
    for _ in range(max_iter):
        v0 = u0 + beta * _expected_next(V, P_K, P_xi0)
        v1 = u1 + beta * _expected_next(V, P_K, P_xi1)
        m = np.maximum(v0, v1)
        V_new = m + np.log(np.exp(v0 - m) + np.exp(v1 - m)) + EULER_GAMMA
        if np.max(np.abs(V_new - V)) < tol:
            return V_new
        V = V_new
    raise BellmanNotConverged(f"No convergence after {max_iter} iterations.")


def expected_values(
    V: np.ndarray, P_K: np.ndarray, P_xi0: np.ndarray, P_xi1: np.ndarray, beta: float
) -> tuple[np.ndarray, np.ndarray]:
    """Discounted continuation values ``beta * E[V | s, d]`` for d = 0, 1."""
    return beta * _expected_next(V, P_K, P_xi0), beta * _expected_next(V, P_K, P_xi1)


def choice_probabilities(
    u0: np.ndarray, u1: np.ndarray, EV0: np.ndarray, EV1: np.ndarray
) -> np.ndarray:
    """Logit probability of buying, ``P(d = 1)``, element by element."""
    v0, v1 = u0 + EV0, u1 + EV1
    return 1.0 / (1.0 + np.exp(np.clip(v0 - v1, -700, 700)))
