"""
state.py

Closed-form state-construction functions for the cross-category demand
propagation model.

This module implements the analytical layer of the model described in
``paper/proposal.md`` (Section 2): the sanitizer-exposure index and the
lotion-inventory transition/binning step. Both are fixed equations with no
fitting or simulation involved (Eq. 7-11 in the underlying research paper).

Examples
--------
Weighted exposure index over the last nine weeks:

>>> round(exposure_index([1, 0, 0, 0, 0, 0, 0, 0, 0], eta=0.7), 4)
0.3126

Inventory transition after a purchase, then binning:

>>> stock = inventory_transition(prev_stock=0.0, purchased=True, rho=0.84)
>>> bin_inventory(stock)
'1'
"""

from __future__ import annotations

__all__ = ["exposure_index", "inventory_transition", "bin_inventory"]

EXPOSURE_WINDOW = 9


def exposure_index(purchases: list[int], eta: float) -> float:
    """
    Compute the cross-category exposure index (Eq. 7).

    The index is a weighted average of the last nine weeks of upstream
    (sanitizer) purchase indicators, with geometrically decaying weights
    controlled by ``eta``.

    Parameters
    ----------
    purchases
        Sequence of exactly 9 purchase indicators, ordered from the most
        recent week (lag 1) to the most distant week (lag 9). Each entry
        must be 0 or 1.
    eta
        Decay parameter in (0, 1]. Smaller values put more weight on the
        most recent purchases; ``eta = 1`` gives an unweighted average
        over the 9-week window.

    Returns
    -------
    float
        The weighted exposure index.

    Raises
    ------
    ValueError
        If ``purchases`` does not have exactly 9 entries, if any entry is
        not 0 or 1, or if ``eta`` is not in (0, 1].

    Examples
    --------
    >>> exposure_index([0, 0, 0, 0, 0, 0, 0, 0, 0], eta=0.7)
    0.0
    >>> exposure_index([1, 1, 1, 1, 1, 1, 1, 1, 1], eta=1.0)
    1.0
    """
    if len(purchases) != EXPOSURE_WINDOW:
        raise ValueError(
            f"purchases must have exactly {EXPOSURE_WINDOW} entries, "
            f"got {len(purchases)}"
        )
    if not all(value in (0, 1) for value in purchases):
        raise ValueError("purchases entries must all be 0 or 1")
    if not (0 < eta <= 1):
        raise ValueError(f"eta must be in (0, 1], got {eta}")

    weights = [eta**k for k in range(EXPOSURE_WINDOW)]
    weight_sum = sum(weights)

    return sum(w * p for w, p in zip(weights, purchases, strict=True)) / weight_sum


def inventory_transition(prev_stock: float, purchased: bool, rho: float) -> float:
    """
    Advance the latent lotion-inventory stock by one week (Eq. 8 / 11).

    Parameters
    ----------
    prev_stock
        Latent inventory stock at the start of the current week (``ξ*_t``).
        Must be non-negative.
    purchased
        Whether lotion was purchased this week (``d_t``).
    rho
        Weekly depreciation retention rate, in (0, 1). Higher values mean
        slower depletion.

    Returns
    -------
    float
        The latent stock at the start of next week (``ξ*_{t+1}``).

    Raises
    ------
    ValueError
        If ``prev_stock`` is negative, or ``rho`` is not in (0, 1).

    Examples
    --------
    Reproduces the worked example in the underlying paper (rho = 0.84):

    >>> stock = 1.0
    >>> stock = inventory_transition(stock, purchased=False, rho=0.84)
    >>> round(stock, 3)
    0.84
    >>> stock = inventory_transition(stock, purchased=False, rho=0.84)
    >>> round(stock, 3)
    0.706
    """
    if prev_stock < 0:
        raise ValueError(f"prev_stock must be non-negative, got {prev_stock}")
    if not (0 < rho < 1):
        raise ValueError(f"rho must be in (0, 1), got {rho}")

    return rho * prev_stock + (1.0 if purchased else 0.0)


def bin_inventory(stock: float) -> str:
    """
    Map a continuous latent inventory stock to a discrete bin (Eq. 9-10).

    Parameters
    ----------
    stock
        Latent inventory stock (``ξ*``). Must be non-negative.

    Returns
    -------
    str
        One of ``"0"``, ``"1"``, ``"2"``, ``"3+"``, following the bin
        boundaries ``[0, 0.5)``, ``[0.5, 1.5)``, ``[1.5, 2.5)``,
        ``[2.5, inf)``.

    Raises
    ------
    ValueError
        If ``stock`` is negative.

    Examples
    --------
    >>> bin_inventory(0.0)
    '0'
    >>> bin_inventory(1.0)
    '1'
    >>> bin_inventory(2.5)
    '3+'
    """
    if stock < 0:
        raise ValueError(f"stock must be non-negative, got {stock}")

    if stock < 0.5:
        return "0"
    if stock < 1.5:
        return "1"
    if stock < 2.5:
        return "2"
    return "3+"
