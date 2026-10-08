# Dynamic Cross-Category Demand Propagation

## Overview

This repository turns the computational workflow of a dynamic model of
cross-category consumer demand into a modular, tested, reproducible Python
package, `demand_propagation`. The motivating research question: does a
surge in hand sanitizer use during COVID-19 generate delayed, downstream
demand for hand lotion through *usage complementarity* (intensive use of one
product creates a maintenance need that a second product restores)?

This is a software-engineering project, not a re-derivation of the economic
model. The goal is to take the existing analysis — building state variables,
fitting a choice model, simulating forward in time, and summarizing the
result as an impulse-response curve and multipliers — and turn it into
independently testable, documented, reusable components. See
`paper/proposal.md` for the full proposal.

## Model Components

The model has three computational layers, each mapped to a modeling
approach used later in this course:

| Layer | What it does | Type |
|---|---|---|
| State construction | Build the sanitizer-exposure index and the lotion-inventory state from closed-form equations | Analytical |
| Forward simulation | Iterate the fitted decision rule and inventory recursion forward in time to trace a multi-week response | Dynamical-system (physical-modeling style) |
| Model fitting | Estimate purchase probability from data via logistic regression, plus a future-value correction | Data-driven |

## Planned Software Workflow

1. Construct the sanitizer-exposure index and lotion-inventory state (analytical).
2. Fit the purchase-probability model from data (data-driven).
3. Simulate purchase behavior forward in time under baseline and exposure-increase scenarios (dynamical-system simulation).
4. Compute the model-implied response curve and the two summary multipliers.
5. Validate each step with automated tests and cross-check the simulated response shape against the reduced-form pattern from the research.

The workflow is developed incrementally, in the order above, over the
semester (see the timeline in `paper/proposal.md`, Section 4).

## Repository Structure

- `demand_propagation/` — the Python package:
  - `state.py` — the two analytical state-construction functions: `exposure_index` and `inventory_transition` + `bin_inventory`.
  - `synthetic_panel.py` — `generate_synthetic_panel`, a synthetic ("phantom") household-week data generator shaped like the real (restricted) research panel, with a known/hidden `truth` of generating parameters.
  - `tests/` — pytest suite for both modules (known values, edge cases, invalid-input cases).
- `examples/` — Jupyter notebooks that demonstrate the package, with Markdown explanations between the steps:
  - `demo_state_construction.ipynb` — walks through both modules end to end; see Quick Example below.
- `scripts/` — command-line scripts that use the package (run them from the repository root after installation):
  - `generate_example_data.py` — regenerates `data/example/synthetic_panel.csv` from a fixed seed; this script is the single source of truth for that file.
- `data/example/synthetic_panel.csv` — a small (50 households x 20 weeks) synthetic example dataset, fully reproducible from `scripts/generate_example_data.py`. Contains no real data.
- `paper/` — `proposal.md` (this project's proposal) and `paper.md` (JOSS-style manuscript).
- `environment.yml` — Conda environment and dependencies.
- `pyproject.toml` — package metadata (used by `pip install -e .`) and tool configuration for pytest and ruff.
- `AGENTS.md`, `CLAUDE.md`, `guides/ai-policy.md` — guidance for AI coding assistants used on this project.

## Reflections

The in-class activity reflections are in `paper/paper.md`, in the section
**Project evolution and lessons learned** (one subsection per course module).

## Data Availability

The empirical application uses restricted Nielsen Consumer Panel data that
cannot be distributed with this repository. No real data file is included
anywhere in this repository. `demand_propagation/synthetic_panel.py`
generates synthetic data with the same column schema as the real panel
(inspected locally to confirm column names/types only; the real file itself
was never copied into this project) so the computational workflow can be
demonstrated and tested publicly.

## Installation

From the repository root:

```
conda env create -f environment.yml --solver libmamba
conda activate demand_propagation
pip install -e .
python -c "import demand_propagation"
```

The last command prints nothing if the installation worked.
`pip install -e .` is the step that makes `demand_propagation` importable
from `scripts/` and `examples/`; without it you get
`ModuleNotFoundError: No module named 'demand_propagation'`.

`--solver libmamba` selects conda's fast dependency solver (already the
default in conda 23.10 and later). If your conda reports that option as
unknown, update conda first with `conda update -n base conda`.

## Quick Example

```
jupyter lab examples/demo_state_construction.ipynb
```

Then choose **Kernel → Restart Kernel and Run All Cells**. The notebook
explains each step in Markdown: the exposure index, the inventory trajectory
(matching the worked example in the underlying paper), and a preview of a
generated synthetic panel. Clear all outputs before committing changes to
the notebook.

## Development Commands

Run from the repository root with the environment active:

| Task | Command |
|---|---|
| Run the tests | `pytest` |
| Lint | `ruff check .` |
| Auto-format | `ruff format .` |
| Regenerate the example dataset | `python scripts/generate_example_data.py` |

## Current Status

**Milestone 2 (Sept 27):** The two analytical state-construction functions
(`exposure_index`, `inventory_transition` + `bin_inventory`) are implemented
and tested, including a regression test reproducing the paper's own worked
example at `rho = 0.84`. A synthetic panel generator (`synthetic_panel.py`)
produces data shaped like the real research panel for testing and
demonstration, and `examples/demo_state_construction.ipynb` walks through
both. `ruff check .` and the full `pytest` suite (44 tests) pass cleanly.

## Next Step

**By Milestone 3 (Oct 11):** implement the forward-simulation engine that
iterates the state transitions over a multi-week horizon under an
exposure-increase vs. baseline scenario, initially driven by fixed or
hand-calibrated decision-rule parameters rather than a fitted model (see
`paper/proposal.md`, Section 4). Add tests checking basic dynamical
properties: the response is zero when the exposure scenario equals the
baseline, and repeated runs on the same inputs are deterministic.
