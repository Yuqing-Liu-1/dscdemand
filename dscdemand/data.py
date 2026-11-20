"""
Household-week panel data for dynamic demand models.

A ``PanelDataset`` wraps a user's own ``pandas.DataFrame`` with one row per
household per week and maps its column names onto the roles the models need:
an upstream category whose purchases build an exposure stock, and a
downstream category whose purchases (and volumes) build an inventory stock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

__all__ = ["PanelDataset", "load_example"]

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_panel.csv"

CANONICAL = ["household", "week", "upstream", "purchase", "volume", "price"]


@dataclass
class PanelDataset:
    """
    A balanced household-week panel for two related product categories.

    Parameters
    ----------
    df
        One row per household per week, with consecutive weeks inside each
        household (integer weeks one apart, or dates seven days apart).
    household, week
        Column names of the household identifier and the week.
    upstream
        Column with the upstream category's weekly purchase quantity
        (for example, sanitizer). It is treated as exogenous.
    purchase
        Column with the downstream purchase indicator (0 or 1).
    volume
        Column with the downstream purchase volume; must be 0 in weeks
        without a purchase.
    price
        Column with the downstream price faced that week.
    covariates
        Other columns that shift current-period purchase utility only
        (for example, a holiday or an unexpected event indicator).

    Raises
    ------
    ValueError
        If a column is missing, purchases are not 0/1, volumes are negative
        or positive without a purchase, or the panel has duplicate or
        non-consecutive weeks.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({"household": [1, 1], "week": [0, 1],
    ...                    "upstream_qty": [0, 2], "purchase": [0, 1],
    ...                    "volume": [0.0, 1.5], "price": [4.0, 3.5]})
    >>> PanelDataset(df).n_households
    1
    """

    df: pd.DataFrame
    household: str = "household"
    week: str = "week"
    upstream: str = "upstream_qty"
    purchase: str = "purchase"
    volume: str = "volume"
    price: str = "price"
    covariates: tuple[str, ...] = ()
    data: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.covariates = tuple(self.covariates)
        source = [
            self.household,
            self.week,
            self.upstream,
            self.purchase,
            self.volume,
            self.price,
        ]
        missing = [c for c in source + list(self.covariates) if c not in self.df]
        if missing:
            raise ValueError(f"Columns not found in the DataFrame: {missing}")

        data = self.df[source + list(self.covariates)].copy()
        data.columns = CANONICAL + list(self.covariates)
        data = data.sort_values(["household", "week"]).reset_index(drop=True)

        if not data["purchase"].isin([0, 1]).all():
            raise ValueError("The purchase column must contain only 0 and 1.")
        if (data["volume"] < 0).any() or (data["upstream"] < 0).any():
            raise ValueError("Volumes and upstream quantities must be non-negative.")
        if ((data["purchase"] == 0) & (data["volume"] > 0)).any():
            raise ValueError("Volume must be 0 in weeks without a purchase.")
        if data.duplicated(["household", "week"]).any():
            raise ValueError("The panel has duplicate household-week rows.")

        step = (
            pd.Timedelta(days=7)
            if pd.api.types.is_datetime64_any_dtype(data["week"])
            else 1
        )
        gaps = data.groupby("household")["week"].diff().dropna()
        if (gaps != step).any():
            raise ValueError(
                "Weeks must be consecutive within each household (no missing weeks)."
            )
        self.data = data

    @property
    def n_households(self) -> int:
        """Number of households in the panel."""
        return int(self.data["household"].nunique())

    @property
    def n_rows(self) -> int:
        """Number of household-week rows."""
        return len(self.data)


def load_example() -> PanelDataset:
    """
    Load the synthetic example panel shipped in ``data/``.

    Returns
    -------
    PanelDataset
        Randomly generated household-week data with one covariate,
        ``event``, an unanticipated three-week shock.
    """
    return PanelDataset(pd.read_csv(EXAMPLE_PATH), covariates=("event",))
