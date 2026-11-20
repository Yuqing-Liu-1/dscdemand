"""
EM algorithm for discrete unobserved household types.

Following Arcidiacono and Jones (2003), EM is wrapped around full-solution
NFXP. A household's type is fixed over its whole history, so the E-step
scores each household's full sequence of choices under every type, and the
M-step maximizes the type-weighted log-likelihood.
"""

from __future__ import annotations

import warnings

import numpy as np
from scipy.optimize import minimize

from .likelihood import ParamLayout, neg_log_likelihood, row_log_probs
from .states import StateSpace

__all__ = ["THETA_BOUND", "e_step", "run_em"]

THETA_BOUND = 15.0
"""Box bound on every parameter; keeps mixture fits away from degenerate types."""


def e_step(
    vector: np.ndarray,
    pi: np.ndarray,
    layout: ParamLayout,
    space: StateSpace,
    arrays: dict,
    beta: float,
) -> tuple[np.ndarray, float]:
    """
    Posterior type probabilities per household and the total log-likelihood.

    Returns
    -------
    responsibilities
        Array of shape ``(n_households, n_types)``; rows sum to 1.
    loglik
        Log-likelihood of the data under the mixture.
    """
    codes, n_hh = arrays["household_code"], arrays["n_households"]
    hh_ll = np.zeros((n_hh, layout.n_types))
    for k in range(layout.n_types):
        logp1, logp0 = row_log_probs(
            layout.theta(vector, k), space, arrays, beta, layout.covariates
        )
        ll = np.where(arrays["purchase"] == 1, logp1, logp0)
        hh_ll[:, k] = np.bincount(codes, weights=ll, minlength=n_hh)
    log_joint = hh_ll + np.log(pi)[None, :]
    m = log_joint.max(axis=1, keepdims=True)
    log_norm = m + np.log(np.exp(log_joint - m).sum(axis=1, keepdims=True))
    return np.exp(log_joint - log_norm), float(log_norm.sum())


def run_em(
    vector: np.ndarray,
    layout: ParamLayout,
    space: StateSpace,
    arrays: dict,
    beta: float,
    pi: np.ndarray | None = None,
    max_iter: int = 30,
    tol: float = 1e-4,
    verbose: bool = False,
) -> dict:
    """
    Alternate E- and M-steps until parameters, type shares, and the
    log-likelihood stop changing.

    Returns
    -------
    dict
        ``vector``, ``pi``, ``responsibilities``, ``loglik``,
        ``loglik_trace``, ``n_iter``, and ``converged``.
    """
    vector = np.asarray(vector, dtype=float).copy()
    pi = np.full(layout.n_types, 1 / layout.n_types) if pi is None else pi
    bounds = [(-THETA_BOUND, THETA_BOUND)] * layout.size
    trace: list[float] = []
    converged = False

    for it in range(max_iter):
        resp, loglik = e_step(vector, pi, layout, space, arrays, beta)
        trace.append(loglik)
        row_weights = resp[arrays["household_code"]]
        res = minimize(
            neg_log_likelihood,
            vector,
            args=(layout, space, arrays, beta, row_weights),
            method="L-BFGS-B",
            bounds=bounds,
        )
        pi_new = resp.mean(axis=0)
        step = max(np.max(np.abs(res.x - vector)), np.max(np.abs(pi_new - pi)))
        rel = abs(trace[-1] - trace[-2]) / abs(trace[-2]) if it else np.inf
        vector, pi = res.x, pi_new
        if verbose:
            print(f"EM iter {it}: loglik={loglik:.3f}, pi={np.round(pi, 3)}")
        if step < tol and rel < 1e-6:
            converged = True
            break

    resp, loglik = e_step(vector, pi, layout, space, arrays, beta)
    trace.append(loglik)
    if not converged:
        warnings.warn(f"EM stopped after {max_iter} iterations.", stacklevel=2)
    return {
        "vector": vector,
        "pi": pi,
        "responsibilities": resp,
        "loglik": loglik,
        "loglik_trace": trace,
        "n_iter": it + 1,
        "converged": converged,
    }
