#!/usr/bin/env python3
"""Demonstrate the Milestone 2 analytical state-construction functions.

Run after `make init` (which installs the package into the project
environment), or with the repository root on PYTHONPATH:

    python scripts/demo_state_construction.py

This script does not touch any real data; it only uses hand-written
example values and the synthetic panel generator.
"""

from __future__ import annotations

from demand_propagation.state import bin_inventory, exposure_index, inventory_transition
from demand_propagation.synthetic_panel import generate_synthetic_panel


def demo_minimal_example() -> None:
    print("=== 1. Minimal hand-written example ===")

    # A household that bought sanitizer only in the most recent week (lag 1).
    sanitizer_history = [1, 0, 0, 0, 0, 0, 0, 0, 0]
    for eta in (0.5, 0.9, 1.0):
        idx = exposure_index(sanitizer_history, eta=eta)
        print(f"exposure_index(recent-only purchase, eta={eta}) -> {idx:.4f}")

    print()
    print("Inventory trajectory reproducing the paper's worked example (rho=0.84):")
    stock = 0.0
    purchase_schedule = [True, False, False, True, False]
    for week, purchased in enumerate(purchase_schedule, start=1):
        stock = inventory_transition(stock, purchased=purchased, rho=0.84)
        stock_bin = bin_inventory(stock)
        purchased_str = str(purchased).ljust(5)
        stock_str = f"{stock:.3f}"
        print(f"  week {week}: d={purchased_str} stock={stock_str} bin={stock_bin}")
    print()


def demo_synthetic_panel() -> None:
    print("=== 2. Synthetic panel (same shape as the real household-week data) ===")

    panel, truth = generate_synthetic_panel(n_households=5, n_weeks=12, seed=42)
    n_h, n_w = truth["n_households"], truth["n_weeks"]
    print(f"Generated {len(panel)} rows from {n_h} households x {n_w} weeks")
    print(f"Generating parameters (truth): {truth}")
    print()
    print("First household's weekly record:")
    first_household = panel[panel["household_code"] == panel["household_code"].iloc[0]]
    print(
        first_household[
            ["week", "bought_sanitizer", "bought_lotion", "san_lag1", "lot_lag1"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    demo_minimal_example()
    demo_synthetic_panel()
