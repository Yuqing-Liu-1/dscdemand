"""
dscdemand: Dynamic Storable-Complementary demand models.

Main entry points:

- ``PanelDataset`` and ``load_example``: household-week panel data.
- ``StorableComplementaryModel``: forward-looking demand for a storable good
  whose need is created by purchases of a complementary upstream good.
- ``multipliers``: gross and net summaries of a shock response.
"""

from importlib.metadata import PackageNotFoundError, version

from .counterfactual import multipliers
from .data import PanelDataset, load_example
from .models import (
    ComplementaryModel,
    StorableComplementaryModel,
    StorableModel,
)

__all__ = [
    "PanelDataset",
    "load_example",
    "StorableComplementaryModel",
    "StorableModel",
    "ComplementaryModel",
    "multipliers",
]

try:
    __version__ = version("dscdemand")
except PackageNotFoundError:
    __version__ = "0.0.0"
