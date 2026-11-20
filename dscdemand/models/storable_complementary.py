"""
Dynamic demand for a storable good with a complementary upstream good.

Households decide each week whether to buy the downstream good. Buying is
more attractive when recent upstream purchases have built up exposure
(usage complementarity, for example hand sanitizer creating a need for hand
lotion) and less attractive when the household already holds downstream
inventory (storability). Households are forward-looking and may belong to
discrete unobserved types.

Flow utility of buying, for a household of type ``k``::

    u1 = a_k + f(K; gamma1, gamma2, kappa) + lam_k * xi + alpha * price
         + sum_j b_j * x_j

where ``K`` is exposure, ``xi`` is inventory, ``f`` is piecewise linear with
a kink at ``kappa`` (the median positive exposure), and ``x_j`` are
covariates. Not buying has utility 0. Parameters are estimated by nested
fixed point maximum likelihood, with EM over types when ``n_types > 1``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ..counterfactual import shock_response as _shock_response
from ..data import PanelDataset
from ..em import THETA_BOUND, run_em
from ..likelihood import (
    ParamLayout,
    continuation_values,
    flow_utility,
    neg_log_likelihood,
    purchase_probability_grid,
)
from ..states import (
    ZERO_THRESHOLD,
    StateSpace,
    assign_bins,
    decay_transition,
    decayed_stock,
    discrete_support,
    stock_transition,
    zero_mass_grid,
)
from .base import DynamicDemandModel

__all__ = ["StorableComplementaryModel"]


def build_state_space(
    data: pd.DataFrame,
    eta: float,
    rho: float,
    n_k_bins: int,
    n_xi_bins: int,
    expect: np.ndarray,
) -> StateSpace:
    """
    Grids and transitions from a panel that already has ``K`` and ``xi``.

    ``expect`` marks the rows used to fit households' expectations of
    future upstream purchases and purchase volumes.
    """
    K_edges, K_reps = zero_mass_grid(data["K"], n_k_bins)
    xi_edges, xi_reps = zero_mass_grid(data["xi"], n_xi_bins)
    S_reps, S_probs = discrete_support(data.loc[expect, "upstream"])
    bought = expect & (data["volume"] > 0).to_numpy()
    Q_reps, Q_probs = discrete_support(data.loc[bought, "volume"], zero_point=False)
    return StateSpace(
        eta=eta,
        rho=rho,
        K_edges=K_edges,
        K_reps=K_reps,
        xi_edges=xi_edges,
        xi_reps=xi_reps,
        kappa=float(np.median(data.loc[data["K"] > ZERO_THRESHOLD, "K"])),
        P_K=stock_transition(K_edges, K_reps, eta, S_reps, S_probs),
        P_xi0=decay_transition(xi_edges, xi_reps, rho),
        P_xi1=stock_transition(xi_edges, xi_reps, rho, Q_reps, Q_probs),
    )


class StorableComplementaryModel(DynamicDemandModel):
    """
    Storable downstream good with usage complementarity to an upstream good.

    Parameters
    ----------
    eta, rho
        Weekly retention rates of the exposure and inventory stocks, in
        (0, 1). They are fixed, not estimated; ``dscdemand.states.
        estimate_decay`` gives the AR(1) calibration used in the research.
    n_types
        Number of discrete unobserved household types.
    beta
        Weekly discount factor (fixed, not estimated).
    n_k_bins, n_xi_bins
        Number of exposure and inventory bins (each includes a zero bin).
    type_specific
        Utility parameters that differ across types; the rest are shared.
    unanticipated
        Covariates households do not expect in advance (for example, a
        sudden event). Their weeks are left out of households' expectations
        of future upstream purchases and volumes, and they are set to 0
        when solving for the continuation value.
    seed
        Seed for the starting values of the types in EM.

    Attributes
    ----------
    params_ : pandas.DataFrame
        Estimated parameters, one column per type.
    pi_ : numpy.ndarray
        Estimated type shares.
    loglik_ : float
        Maximized log-likelihood.
    loglik_trace_ : list of float
        Log-likelihood after each EM iteration (one value without EM).
    state_space_ : StateSpace
        Grids and transitions used in the fit.

    Examples
    --------
    >>> from dscdemand import load_example
    >>> model = StorableComplementaryModel(eta=0.6, rho=0.8, unanticipated=("event",))
    >>> model = model.fit(load_example())  # doctest: +SKIP
    >>> model.shock_response(weeks=12)  # doctest: +SKIP
    """

    def __init__(
        self,
        eta: float,
        rho: float,
        n_types: int = 1,
        beta: float = 0.95,
        n_k_bins: int = 6,
        n_xi_bins: int = 8,
        type_specific: tuple[str, ...] = ("a", "lam"),
        unanticipated: tuple[str, ...] = (),
        seed: int = 0,
    ) -> None:
        for name, value in (("eta", eta), ("rho", rho)):
            if not 0 < value < 1:
                raise ValueError(f"{name} must be in (0, 1), got {value}")
        if n_types < 1:
            raise ValueError(f"n_types must be at least 1, got {n_types}")
        if not 0 < beta < 1:
            raise ValueError(f"beta must be in (0, 1), got {beta}")
        self.eta = eta
        self.rho = rho
        self.n_types = n_types
        self.beta = beta
        self.n_k_bins = n_k_bins
        self.n_xi_bins = n_xi_bins
        self.type_specific = tuple(type_specific)
        self.unanticipated = tuple(unanticipated)
        self.seed = seed

    # ------------------------------------------------------------------ fit

    def _references(self, data: pd.DataFrame, covariates) -> tuple[float, np.ndarray]:
        x_ref = [
            0.0 if c in self.unanticipated else float(data[c].mean())
            for c in covariates
        ]
        return float(data["price"].mean()), np.asarray(x_ref)

    def fit(
        self,
        dataset: PanelDataset,
        state_space: StateSpace | None = None,
        max_em_iter: int = 30,
        verbose: bool = False,
    ) -> StorableComplementaryModel:
        """
        Estimate the model by NFXP maximum likelihood (EM if ``n_types > 1``).

        Parameters
        ----------
        dataset
            The household-week panel.
        state_space
            Use these grids and transitions instead of building them from
            the data (for example, the true ones from ``simulate``).
        max_em_iter
            Maximum number of EM iterations.
        verbose
            Print EM progress.

        Returns
        -------
        StorableComplementaryModel
            The fitted model (``self``).
        """
        covariates = dataset.covariates
        unknown = set(self.unanticipated) - set(covariates)
        if unknown:
            raise ValueError(f"Unanticipated covariates not in dataset: {unknown}")

        data = dataset.data.copy()
        eta, rho = self.eta, self.rho
        data["K"] = decayed_stock(data, "upstream", eta)
        data["xi"] = decayed_stock(data, "volume", rho)
        expect = (data[list(self.unanticipated)] == 0).all(axis=1).to_numpy()
        if state_space is None:
            state_space = build_state_space(
                data, eta, rho, self.n_k_bins, self.n_xi_bins, expect
            )
        data["K_bin"] = assign_bins(data["K"], state_space.K_edges)
        data["xi_bin"] = assign_bins(data["xi"], state_space.xi_edges)

        p_ref, x_ref = self._references(data, covariates)
        codes, households = pd.factorize(data["household"], sort=True)
        arrays = {
            "K_bin": data["K_bin"].to_numpy(),
            "xi_bin": data["xi_bin"].to_numpy(),
            "price": data["price"].to_numpy(dtype=float),
            "X": data[list(covariates)].to_numpy(dtype=float).reshape(len(data), -1),
            "purchase": data["purchase"].to_numpy(),
            "p_ref": p_ref,
            "x_ref": x_ref,
            "household_code": codes,
            "n_households": len(households),
        }

        one = ParamLayout(covariates, self.type_specific, 1)
        res = minimize(
            neg_log_likelihood,
            np.zeros(one.size),
            args=(one, state_space, arrays, self.beta),
            method="L-BFGS-B",
            bounds=[(-THETA_BOUND, THETA_BOUND)] * one.size,
        )
        layout, vector, pi = one, res.x, np.ones(1)
        loglik, converged, resp = -float(res.fun), bool(res.success), None
        trace = [loglik]

        if self.n_types > 1:
            layout = ParamLayout(covariates, self.type_specific, self.n_types)
            base = one.theta(res.x, 0)
            rng = np.random.default_rng(self.seed)
            starts = []
            for k in range(self.n_types):
                th = dict(base)
                for name in self.type_specific:
                    th[name] += rng.normal(scale=0.5) if k else 0.0
                starts.append(th)
            em = run_em(
                layout.pack(starts),
                layout,
                state_space,
                arrays,
                self.beta,
                max_iter=max_em_iter,
                verbose=verbose,
            )
            vector, pi = em["vector"], em["pi"]
            loglik, converged = em["loglik"], em["converged"]
            resp = em["responsibilities"]
            trace = em["loglik_trace"]

        self.layout_ = layout
        self.vector_ = vector
        self.pi_ = pi
        self.loglik_ = loglik
        self.loglik_trace_ = trace
        self.converged_ = converged
        self.responsibilities_ = resp
        self.state_space_ = state_space
        self.p_ref_, self.x_ref_ = p_ref, x_ref
        self.data_ = data
        self.params_ = pd.DataFrame(
            {f"type_{k}": layout.theta(vector, k) for k in range(layout.n_types)}
        )
        return self

    def _check_fitted(self) -> None:
        if not hasattr(self, "params_"):
            raise RuntimeError("Call fit() before using the fitted model.")

    # ------------------------------------------------------------ results

    def shock_response(
        self, shock: float | None = None, weeks: int = 26
    ) -> pd.DataFrame:
        """
        Weekly purchase response to a one-time extra upstream purchase.

        Starts from the empirical distribution of households over states and
        averages over types with their estimated shares.

        Parameters
        ----------
        shock
            Size of the extra upstream purchase. Defaults to the 75th
            percentile of positive upstream purchases in anticipated weeks.
        weeks
            Number of weeks after the shock.

        Returns
        -------
        pandas.DataFrame
            Columns ``week``, ``p_shock``, ``p_baseline``, ``response``.
            Summarize with ``dscdemand.multipliers(result["response"])``.
        """
        self._check_fitted()
        data, space = self.data_, self.state_space_
        if shock is None:
            expect = (data[list(self.unanticipated)] == 0).all(axis=1)
            positive = data.loc[expect & (data["upstream"] > 0), "upstream"]
            shock = float(positive.quantile(0.75))
        D0 = np.zeros((len(space.K_reps), len(space.xi_reps)))
        np.add.at(D0, (data["K_bin"], data["xi_bin"]), 1.0)
        D0 /= D0.sum()
        ccps = [
            purchase_probability_grid(
                self.layout_.theta(self.vector_, k),
                space,
                self.beta,
                self.p_ref_,
                self.x_ref_,
                self.layout_.covariates,
            )
            for k in range(self.layout_.n_types)
        ]
        return _shock_response(space, ccps, self.pi_, D0, shock, weeks)

    # ----------------------------------------------------------- simulate

    def simulate(
        self,
        params: list[dict[str, float]],
        pi: list[float] | None = None,
        n_households: int = 300,
        n_weeks: int = 60,
        event_weeks: tuple[int, ...] = (40, 41, 42),
        seed: int = 0,
    ) -> tuple[PanelDataset, dict]:
        """
        Generate a synthetic panel from known parameters.

        Upstream purchases are 0 most weeks and 1-3 units otherwise, with
        larger, more frequent purchases during ``event_weeks`` (an
        unanticipated event recorded in the covariate ``event``). Prices
        are random; purchase volumes are 1-3 units. Each household's type
        is drawn with shares ``pi`` and kept for all weeks.

        Parameters
        ----------
        params
            One parameter dictionary per type, with keys ``a``, ``gamma1``,
            ``gamma2``, ``lam``, ``alpha``, and ``event``.
        pi
            Type shares; equal shares if omitted.
        n_households, n_weeks
            Panel size.
        event_weeks
            Weeks of the unanticipated event.
        seed
            Random seed; the same inputs and seed give the same panel.

        Returns
        -------
        dataset : PanelDataset
            The synthetic panel, with covariate ``event``.
        truth : dict
            ``params``, ``pi``, ``types``, and the true
            ``state_space``.
        """
        rng = np.random.default_rng(seed)
        eta, rho = self.eta, self.rho
        n_types = len(params)
        pi = np.full(n_types, 1 / n_types) if pi is None else np.asarray(pi, float)
        weeks = np.arange(n_weeks)
        event = np.isin(weeks, event_weeks).astype(float)

        normal = (np.array([0.0, 1, 2, 3]), np.array([0.8, 0.1, 0.06, 0.04]))
        surge = (np.array([0.0, 2, 3, 4]), np.array([0.4, 0.3, 0.2, 0.1]))
        volume = (np.array([1.0, 2, 3]), np.array([0.5, 0.3, 0.2]))

        S = np.where(
            event[None, :] == 1,
            rng.choice(surge[0], (n_households, n_weeks), p=surge[1]),
            rng.choice(normal[0], (n_households, n_weeks), p=normal[1]),
        )
        price = np.round(np.clip(rng.normal(4.0, 0.5, S.shape), 1.0, 8.0), 2)
        Q = rng.choice(volume[0], S.shape, p=volume[1])
        types = rng.choice(n_types, n_households, p=pi)

        K = np.zeros(S.shape)
        for t in range(1, n_weeks):
            K[:, t] = eta * K[:, t - 1] + S[:, t - 1]
        pilot = np.zeros(S.shape)
        buys = rng.random(S.shape) < 0.3
        for t in range(1, n_weeks):
            pilot[:, t] = rho * pilot[:, t - 1] + buys[:, t - 1] * Q[:, t - 1]

        K_edges, K_reps = zero_mass_grid(K.ravel(), self.n_k_bins)
        xi_edges, xi_reps = zero_mass_grid(pilot.ravel(), self.n_xi_bins)
        space = StateSpace(
            eta=eta,
            rho=rho,
            K_edges=K_edges,
            K_reps=K_reps,
            xi_edges=xi_edges,
            xi_reps=xi_reps,
            kappa=float(np.median(K[K > ZERO_THRESHOLD])),
            P_K=stock_transition(K_edges, K_reps, eta, *normal),
            P_xi0=decay_transition(xi_edges, xi_reps, rho),
            P_xi1=stock_transition(xi_edges, xi_reps, rho, *volume),
        )

        covariates = ("event",)
        x_ref = np.zeros(1)
        EVs = [
            continuation_values(th, space, self.beta, 4.0, x_ref, covariates)
            for th in params
        ]
        K_bin = assign_bins(K, K_edges)
        d = np.zeros(S.shape, dtype=int)
        xi = np.zeros(n_households)
        draws = rng.random(S.shape)
        for t in range(n_weeks):
            xi_bin = assign_bins(xi, xi_edges)
            for k in range(n_types):
                rows = types == k
                kb, xb = K_bin[rows, t], xi_bin[rows]
                u1 = flow_utility(
                    params[k],
                    K_reps[kb],
                    xi_reps[xb],
                    price[rows, t],
                    np.full((rows.sum(), 1), event[t]),
                    space.kappa,
                    covariates,
                )
                EV0, EV1 = EVs[k]
                p_buy = 1 / (1 + np.exp(EV0[kb, xb] - u1 - EV1[kb, xb]))
                d[rows, t] = draws[rows, t] < p_buy
            xi = rho * xi + d[:, t] * Q[:, t]

        df = pd.DataFrame(
            {
                "household": np.repeat(np.arange(n_households), n_weeks),
                "week": np.tile(weeks, n_households),
                "upstream_qty": S.ravel(),
                "purchase": d.ravel(),
                "volume": (d * Q).ravel(),
                "price": price.ravel(),
                "event": np.tile(event, n_households).astype(int),
            }
        )
        truth = {
            "params": params,
            "pi": pi,
            "types": types,
            "state_space": space,
        }
        return PanelDataset(df, covariates=covariates), truth
