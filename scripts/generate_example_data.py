#!/usr/bin/env python3
"""Regenerate the committed synthetic example panel.

This script is the single source of truth for ``data/example/synthetic_panel.csv``.
The file is fully synthetic (see ``demand_propagation/synthetic_panel.py``) and
contains no real household data; it is regenerated here with a fixed seed so
its contents stay reproducible rather than hand-edited.

Usage (from the repository root, after `pip install -e .`; see README):
    python scripts/generate_example_data.py
"""

from __future__ import annotations

from pathlib import Path

from demand_propagation.synthetic_panel import generate_synthetic_panel

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "example" / "synthetic_panel.csv"

# Fixed generation parameters: the "recipe" for the committed example file.
N_HOUSEHOLDS = 50
N_WEEKS = 20
SEED = 42


def main() -> None:
    panel, truth = generate_synthetic_panel(
        n_households=N_HOUSEHOLDS,
        n_weeks=N_WEEKS,
        seed=SEED,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(panel)} rows to {OUTPUT_PATH}")
    print(f"Generating parameters (truth): {truth}")


if __name__ == "__main__":
    main()
