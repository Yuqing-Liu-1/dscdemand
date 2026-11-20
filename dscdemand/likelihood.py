"""
Nested fixed point (NFXP) log-likelihood.

For each candidate parameter vector, the Bellman equation is solved once
per household type, and every household-week's observed choice is scored
with its own price and covariates in current utility and the continuation
value of its (exposure bin, inventory bin) state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .bellman import (
    choice_probabilities,
    expected_values,
    exposure_effect,
    solve_bellman,
)
from .states import StateSpace

__all__ = [
    "BASE_PARAMS",
    "flow_utility",
    "ParamLayout",
    "utility_grid",
    "continuation_values",
    "row_log_probs",
    "neg_log_likelihood",
    "purchase_probability_grid",
]

BASE_PARAMS = ("a", "gamma1", "gamma2", "lam", "alpha")
"""Intercept, exposure slopes below/above the kink, inventory, and price."""


@dataclass(frozen=True)
class ParamLayout:
    """
    Order of parameters in the vector the optimizer sees.

    Parameters shared by all types come first, then one block of
    type-specific parameters per type.

    Examples
    --------
    >>> layout = ParamLayout(("event",), ("a", "lam"), n_types=2)
    >>> layout.size
    8
    >>> layout.theta(np.arange(8.0), 1)["a"]
    6.0
    """

    covariates: tuple[str, ...] = ()
    type_specific: tuple[str, ...] = ("a", "lam")
    n_types: int = 1

    @property
    def names(self) -> tuple[str, ...]:
        """All utility parameter names, base parameters first."""
        return BASE_PARAMS + tuple(self.covariates)

    @property
    def shared(self) -> tuple[str, ...]:
        """Parameter names common to all types."""
        return tuple(n for n in self.names if n not in self.type_specific)

    @property
    def size(self) -> int:
        """Length of the full parameter vector."""
        return len(self.shared) + self.n_types * len(self.type_specific)

    def theta(self, vector: np.ndarray, k: int) -> dict[str, float]:
        """Parameters of type ``k`` as a name-to-value dictionary."""
        out = dict(zip(self.shared, vector[: len(self.shared)], strict=True))
        start = len(self.shared) + k * len(self.type_specific)
        block = vector[start : start + len(self.type_specific)]
        out.update(zip(self.type_specific, block, strict=True))
        return {n: float(out[n]) for n in self.names}

    def pack(self, thetas: list[dict[str, float]]) -> np.ndarray:
        """Inverse of ``theta``: shared values are taken from type 0."""
        vec = [thetas[0][n] for n in self.shared]
        for th in thetas:
            vec += [th[n] for n in self.type_specific]
        return np.asarray(vec, dtype=float)


def flow_utility(theta, K, xi, price, X, kappa, covariates):
    """Flow utility of buying: intercept, exposure, inventory, price, covariates."""
    u = (
        theta["a"]
        + exposure_effect(K, theta["gamma1"], theta["gamma2"], kappa)
        + theta["lam"] * xi
        + theta["alpha"] * price
    )
    for j, name in enumerate(covariates):
        u = u + theta[name] * X[..., j]
    return u


def utility_grid(theta, space: StateSpace, p_ref, x_ref, covariates):
    """Flow utilities ``(u0, u1)`` on the state grid at reference covariates."""
    K, xi = np.meshgrid(space.K_reps, space.xi_reps, indexing="ij")
    X = np.broadcast_to(np.asarray(x_ref, dtype=float), K.shape + (len(covariates),))
    u1 = flow_utility(theta, K, xi, p_ref, X, space.kappa, covariates)
    return np.zeros_like(u1), u1


def continuation_values(theta, space: StateSpace, beta, p_ref, x_ref, covariates):
    """Discounted continuation values ``(EV0, EV1)`` on the state grid."""
    u0, u1 = utility_grid(theta, space, p_ref, x_ref, covariates)
    V = solve_bellman(u0, u1, space.P_K, space.P_xi0, space.P_xi1, beta)
    return expected_values(V, space.P_K, space.P_xi0, space.P_xi1, beta)


def row_log_probs(theta, space: StateSpace, arrays: dict, beta: float, covariates):
    """Log probabilities of buying and not buying for every household-week."""
    EV0, EV1 = continuation_values(
        theta, space, beta, arrays["p_ref"], arrays["x_ref"], covariates
    )
    kb, xb = arrays["K_bin"], arrays["xi_bin"]
    u1 = flow_utility(
        theta,
        space.K_reps[kb],
        space.xi_reps[xb],
        arrays["price"],
        arrays["X"],
        space.kappa,
        covariates,
    )
    v0, v1 = EV0[kb, xb], u1 + EV1[kb, xb]
    m = np.maximum(v0, v1)
    log_z = m + np.log(np.exp(v0 - m) + np.exp(v1 - m))
    return v1 - log_z, v0 - log_z


def neg_log_likelihood(
    vector: np.ndarray,
    layout: ParamLayout,
    space: StateSpace,
    arrays: dict,
    beta: float,
    weights: np.ndarray | None = None,
) -> float:
    """
    Negative log-likelihood of the observed purchases.

    ``weights`` (rows x types) are the EM posterior type probabilities; with
    one type and no weights, every row counts once.
    """
    total = 0.0
    for k in range(layout.n_types):
        logp1, logp0 = row_log_probs(
            layout.theta(vector, k), space, arrays, beta, layout.covariates
        )
        ll = np.where(arrays["purchase"] == 1, logp1, logp0)
        if weights is not None:
            ll = ll * weights[:, k]
        total += ll.sum()
    return -float(total)


def purchase_probability_grid(theta, space, beta, p_ref, x_ref, covariates):
    """Probability of buying at every grid state, at reference covariates."""
    u0, u1 = utility_grid(theta, space, p_ref, x_ref, covariates)
    EV0, EV1 = continuation_values(theta, space, beta, p_ref, x_ref, covariates)
    return choice_probabilities(u0, u1, EV0, EV1)
