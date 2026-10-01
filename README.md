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

- `paper/` — `proposal.md` (this project's proposal) and `paper.md` (JOSS-style manuscript, including per-module reflections).
- `demand_propagation/` — the Python package:
  - `state.py` — the two analytical state-construction functions: `exposure_index` and `inventory_transition` + `bin_inventory`.
  - `synthetic_panel.py` — `generate_synthetic_panel`, a synthetic ("phantom") household-week data generator shaped like the real (restricted) research panel, with a known/hidden `truth` of generating parameters.
  - `tests/` — pytest suite for both modules (known values, edge cases, invalid-input cases).
- `scripts/` — supporting scripts:
  - `rename_package.py` — one-time template rename helper (already run for Milestone 1).
  - `generate_example_data.py` — regenerates `data/example/synthetic_panel.csv` from a fixed seed; this script is the single source of truth for that file.
  - `demo_state_construction.py` — runnable example exercising both modules end to end; see Quick Example below.
- `data/example/synthetic_panel.csv` — a small (50 households x 20 weeks) synthetic example dataset, fully reproducible from `scripts/generate_example_data.py`. Contains no real data.
- `environment.yml` — Conda environment and dependencies.
- `makefile` — documented workflow commands (see below).
- `pyproject.toml` — tool configuration for pytest, ruff, and mypy.
- `00_START_HERE.ipynb` — walkthrough notebook from the course software template.

## Data Availability

The empirical application uses restricted Nielsen Consumer Panel data that
cannot be distributed with this repository. No real data file is included
anywhere in this repository. `demand_propagation/synthetic_panel.py`
generates synthetic data with the same column schema as the real panel
(inspected locally to confirm column names/types only; the real file itself
was never copied into this project) so the computational workflow can be
demonstrated and tested publicly.

## Quick Example

```
python scripts/demo_state_construction.py
```

This prints a hand-written exposure-index/inventory-trajectory example
(matching the worked example in the underlying paper) followed by a preview
of a freshly generated synthetic panel. No data files are required.

## Environment and Installation

**First-time setup** (the `make` command itself is not preinstalled on
Windows, so the very first environment has to be created without it):

```
conda env create --prefix ./envs -f environment.yml
conda activate ./envs
```

**From then on**, `make` is available inside the activated environment
(`environment.yml` includes `make` as a dependency for exactly this reason),
so the normal workflow is:

```
make init    # re-create/update the environment and (re)install the package
make check   # run lint (ruff) and tests (pytest)
```

Run `make help` for the full list of commands (`lint`, `format`, `test`,
`type`, `docs`, `check`, `check-full`, `clean`). The repository is based on
the CMSE 802 Scientific Software Starter Template.

The underlying commands have been verified directly (`ruff check .` passes
with zero warnings; the full test suite of 44 tests passes via `pytest -v`).
`make init` also runs `pip install -e .` inside the environment so
`demand_propagation` and the scripts in `scripts/` are importable without
manual `PYTHONPATH` configuration.

## Current Status

**Milestone 2 (Sept 27):** The two analytical state-construction functions
(`exposure_index`, `inventory_transition` + `bin_inventory`) are implemented
and tested, including a regression test reproducing the paper's own worked
example at `rho = 0.84`. A synthetic panel generator (`synthetic_panel.py`)
produces data shaped like the real research panel for testing and
demonstration. `ruff check .` and the full `pytest` suite (44 tests) pass
cleanly. The template's placeholder `example.py` module has been removed
and `00_START_HERE.ipynb` updated to match.

## Next Step

**By Milestone 3 (Oct 11):** implement the forward-simulation engine that
iterates the state transitions over a multi-week horizon under an
exposure-increase vs. baseline scenario, initially driven by fixed or
hand-calibrated decision-rule parameters rather than a fitted model (see
`paper/proposal.md`, Section 4). Add tests checking basic dynamical
properties: the response is zero when the exposure scenario equals the
baseline, and repeated runs on the same inputs are deterministic.
