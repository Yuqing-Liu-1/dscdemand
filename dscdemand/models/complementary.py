"""
Dynamic demand for complementary goods (planned).

Planned model: purchases of one good raise the value of another, as with
tied goods such as razors and blades (Hartmann and Nair, 2010) or base
products and add-ons (Liu, Derdenger and Sun, 2018), without inventory of
the downstream good.
"""

from __future__ import annotations

from .base import DynamicDemandModel

__all__ = ["ComplementaryModel"]


class ComplementaryModel(DynamicDemandModel):
    """Complementary-goods model without storage. Not implemented yet."""

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "ComplementaryModel is planned; use StorableComplementaryModel for now."
        )

    def fit(self, dataset, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def simulate(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def shock_response(self, shock=None, weeks=26):  # pragma: no cover
        raise NotImplementedError
