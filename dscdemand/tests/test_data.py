"""Tests for PanelDataset and the example data."""

import pandas as pd
import pytest

from dscdemand import PanelDataset, load_example


def panel(**changes) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "household": [1, 1, 1, 2, 2, 2],
            "week": [0, 1, 2, 0, 1, 2],
            "upstream_qty": [0, 2, 0, 1, 0, 0],
            "purchase": [0, 1, 0, 0, 0, 1],
            "volume": [0.0, 1.5, 0.0, 0.0, 0.0, 2.0],
            "price": [4.0, 3.5, 4.2, 4.1, 3.9, 3.8],
        }
    )
    for col, values in changes.items():
        df[col] = values
    return df


def test_valid_panel_is_sorted_and_counted() -> None:
    ds = PanelDataset(panel().sample(frac=1, random_state=0))
    assert ds.n_households == 2
    assert ds.n_rows == 6
    assert ds.data["week"].tolist() == [0, 1, 2, 0, 1, 2]


def test_custom_column_names() -> None:
    df = panel().rename(columns={"household": "hh", "upstream_qty": "sanitizer"})
    ds = PanelDataset(df, household="hh", upstream="sanitizer")
    assert list(ds.data.columns[:3]) == ["household", "week", "upstream"]


def test_date_weeks_must_be_seven_days_apart() -> None:
    weeks = pd.to_datetime(["2020-01-05", "2020-01-12", "2020-01-19"] * 2)
    assert PanelDataset(panel(week=weeks)).n_rows == 6


@pytest.mark.parametrize(
    "changes",
    [
        {"purchase": [0, 2, 0, 0, 0, 1]},
        {"volume": [0.0, 1.5, 0.5, 0.0, 0.0, 2.0]},
        {"volume": [0.0, -1.0, 0.0, 0.0, 0.0, 2.0]},
        {"week": [0, 1, 3, 0, 1, 2]},
        {"week": [0, 1, 1, 0, 1, 2]},
    ],
)
def test_invalid_panels_raise(changes) -> None:
    with pytest.raises(ValueError):
        PanelDataset(panel(**changes))


def test_missing_column_raises() -> None:
    with pytest.raises(ValueError, match="not found"):
        PanelDataset(panel(), covariates=("holiday",))


def test_load_example() -> None:
    ds = load_example()
    assert ds.n_households == 300
    assert ds.n_rows == 300 * 60
    assert ds.covariates == ("event",)
