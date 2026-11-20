"""Common interface of all dynamic demand models in ``dscdemand``."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from ..data import PanelDataset

__all__ = ["DynamicDemandModel"]


class DynamicDemandModel(ABC):
    """
    Base class: every model can be fit to a panel, simulate data, and
    report the purchase response to a shock.
    """

    @abstractmethod
    def fit(self, dataset: PanelDataset, **kwargs) -> DynamicDemandModel:
        """Estimate the model's parameters from a panel; returns ``self``."""

    @abstractmethod
    def simulate(self, **kwargs) -> tuple[PanelDataset, dict]:
        """Generate a synthetic panel and the parameters that produced it."""

    @abstractmethod
    def shock_response(
        self, shock: float | None = None, weeks: int = 26
    ) -> pd.DataFrame:
        """Weekly purchase response to a one-time shock, after fitting."""
