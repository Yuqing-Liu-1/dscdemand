"""Tests for StorableComplementaryModel, counterfactuals, and placeholders."""

import warnings

import numpy as np
import pandas as pd
import pytest

from dscdemand import (
    ComplementaryModel,
    StorableComplementaryModel,
    StorableModel,
    multipliers,
)

TRUE = {
    "a": 1.0,
    "gamma1": 0.8,
    "gamma2": 0.2,
    "lam": -2.5,
    "alpha": -0.4,
    "event": 1.0,
}


def make_model(**kwargs) -> StorableComplementaryModel:
    return StorableComplementaryModel(
        eta=0.6, rho=0.8, unanticipated=("event",), **kwargs
    )


@pytest.fixture(scope="module")
def simulated():
    return make_model().simulate([TRUE], n_households=300, n_weeks=60, seed=1)


@pytest.fixture(scope="module")
def fitted(simulated):
    dataset, truth = simulated
    return make_model().fit(dataset, state_space=truth["state_space"])


def test_parameter_recovery(fitted) -> None:
    """With the true grid, every parameter is recovered within 0.3."""
    estimates = fitted.params_["type_0"]
    for name, value in TRUE.items():
        assert estimates[name] == pytest.approx(value, abs=0.3), name
    assert fitted.converged_


def test_simulation_is_reproducible() -> None:
    a, _ = make_model().simulate([TRUE], n_households=20, n_weeks=10, seed=3)
    b, _ = make_model().simulate([TRUE], n_households=20, n_weeks=10, seed=3)
    pd.testing.assert_frame_equal(a.df, b.df)


def test_zero_shock_gives_zero_response(fitted) -> None:
    result = fitted.shock_response(shock=0.0, weeks=12)
    assert (result["response"] == 0).all()


def test_shock_raises_purchases_first(fitted) -> None:
    result = fitted.shock_response(weeks=26)
    assert list(result.columns) == ["week", "p_shock", "p_baseline", "response"]
    assert result.loc[0, "response"] > 0
    summary = multipliers(result["response"])
    assert summary["gross"] > 0
    assert summary["net"] <= summary["gross"]


def test_multipliers_known_values() -> None:
    assert multipliers([0.2, 0.1, -0.06]) == {
        "gross": 0.3,
        "net": 0.24,
        "offset_ratio": 0.2,
    }


def test_em_likelihood_never_decreases() -> None:
    """Each EM iteration weakly raises the mixture log-likelihood."""
    two = [dict(TRUE, a=-0.5), dict(TRUE, a=2.0)]
    model = make_model(n_types=2)
    dataset, truth = model.simulate(two, n_households=150, n_weeks=40, seed=2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # a short run may stop before converging
        model.fit(dataset, state_space=truth["state_space"], max_em_iter=3)
    assert model.pi_.sum() == pytest.approx(1)
    assert model.responsibilities_.shape == (150, 2)
    assert np.all(np.diff(model.loglik_trace_) > -1e-6)


@pytest.mark.parametrize(
    "kwargs", [{"eta": 0.0}, {"rho": 1.0}, {"n_types": 0}, {"beta": 1.0}]
)
def test_invalid_settings_raise(kwargs) -> None:
    settings = {"eta": 0.6, "rho": 0.8, **kwargs}
    with pytest.raises(ValueError):
        StorableComplementaryModel(**settings)


def test_unknown_unanticipated_covariate_raises(simulated) -> None:
    dataset, _ = simulated
    with pytest.raises(ValueError):
        StorableComplementaryModel(eta=0.6, rho=0.8, unanticipated=("holiday",)).fit(
            dataset
        )


def test_results_need_fit() -> None:
    with pytest.raises(RuntimeError):
        make_model().shock_response()


@pytest.mark.parametrize("model", [StorableModel, ComplementaryModel])
def test_planned_models_are_not_implemented(model) -> None:
    with pytest.raises(NotImplementedError):
        model()


def test_response_is_deterministic(fitted) -> None:
    np.testing.assert_array_equal(
        fitted.shock_response(weeks=8)["response"],
        fitted.shock_response(weeks=8)["response"],
    )
