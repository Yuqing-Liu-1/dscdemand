"""
Dynamic demand for a single storable good (planned).

Planned model: consumers stockpile when prices are low and consume from
inventory, as in Erdem, Imai and Keane (2003) and Hendel and Nevo (2006).
It will share the state, Bellman, likelihood, and EM machinery of
``StorableComplementaryModel`` without the upstream exposure stock.
"""

from __future__ import annotations

from .base import DynamicDemandModel

__all__ = ["StorableModel"]


class StorableModel(DynamicDemandModel):
    """Single-category storable-goods model. Not implemented yet."""

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "StorableModel is planned; use StorableComplementaryModel for now."
        )

    def fit(self, dataset, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def simulate(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def shock_response(self, shock=None, weeks=26):  # pragma: no cover
        raise NotImplementedError
