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
- `demo_state_construction.ipynb` — Jupyter notebook that walks through both modules end to end, with Markdown explanations between the steps; see Quick Example below.
- `scripts/` — command-line scripts that use the package (run them from the repository root after installation):
  - `generate_example_data.py` — regenerates `data/example/synthetic_panel.csv` from a fixed seed; this script is the single source of truth for that file.
- `data/example/synthetic_panel.csv` — a small (50 households x 20 weeks) synthetic example dataset, fully reproducible from `scripts/generate_example_data.py`. Contains no real data.
- `paper/` — `proposal.md` (this project's proposal), `paper.md` (JOSS-style manuscript), and `reflections.md` (in-class activity reflections).
- `Makefile` — project commands (`make help`; see Commands).
- `environment.yml` — Conda environment and dependencies.
- `pyproject.toml` — package metadata (used by `pip install -e .`) and tool configuration for pytest and ruff.
- `AGENTS.md`, `CLAUDE.md`, `guides/ai-policy.md` — guidance for AI coding assistants used on this project.

## Reflections

The in-class activity reflections are in
[`paper/reflections.md`](paper/reflections.md) (one section per activity).

## Data Availability

The empirical application uses restricted Nielsen Consumer Panel data that
cannot be distributed with this repository. No real data file is included
anywhere in this repository. `demand_propagation/synthetic_panel.py`
generates synthetic data with the same column schema as the real panel
(inspected locally to confirm column names/types only; the real file itself
was never copied into this project) so the computational workflow can be
demonstrated and tested publicly.

## Installation

From the repository root (macOS/Linux):

```
make envs
conda activate demand_propagation
make check
```

`make envs` creates (or updates) the conda environment and installs the
package with `pip install -e .`; `make check` should end with `45 passed`.

**Windows:** `make` is not preinstalled, but the environment includes it.
The first time, run the commands that `make envs` runs, then use `make`
inside the activated environment:

```
conda env create -f environment.yml --solver libmamba
conda activate demand_propagation
pip install -e .
make check
```

`pip install -e .` makes `demand_propagation` importable from any folder;
without it you get `ModuleNotFoundError: No module named 'demand_propagation'`.
`--solver libmamba` selects conda's fast solver (the default since conda
23.10); if your conda does not know it, run `conda update -n base conda`.

## Quick Example

```
make serve
```

This runs `jupyter lab demo_state_construction.ipynb`. Run it from the repository root with the `demand_propagation` environment
active, so the notebook uses that environment (if you open the notebook from
an already running Jupyter or from VS Code, select the `demand_propagation`
environment as the kernel). Then choose
**Kernel → Restart Kernel and Run All Cells**. The notebook
explains each step in Markdown: the exposure index, the inventory trajectory
(matching the worked example in the underlying paper), and a preview of a
generated synthetic panel. Clear all outputs before committing changes to
the notebook.

Expected output (first two steps):

```
exposure_index(recent-only purchase, eta=0.5) -> 0.5010
exposure_index(recent-only purchase, eta=0.9) -> 0.1632
exposure_index(recent-only purchase, eta=1.0) -> 0.1111
week 1: d=True  stock=1.000 bin=1
week 2: d=False stock=0.840 bin=1
week 3: d=False stock=0.706 bin=1
week 4: d=True  stock=1.593 bin=2
week 5: d=False stock=1.338 bin=1
```

## Documentation

API documentation is generated from the docstrings with
[pdoc](https://pdoc.dev/). From the repository root, with the environment
active, run `make docs`. Then open `docs/index.html` in a browser. The `docs/` folder is generated,
so it is not committed.

## Testing

From the repository root, with the environment active, run `make test`
(or `pytest`). pytest runs every `test_*` function in `demand_propagation/tests/`.
**Success** ends with `45 passed`. **Failure** reports `N failed` with the
test name and the line that failed:

- `test_imports.py` — imports numpy, pandas, and the package. If this fails,
  the environment is not set up correctly; fix that first.
- `test_state.py` — known values (including the paper's worked example at
  `rho = 0.84`), edge cases, and invalid inputs for the state functions.
- `test_synthetic_panel.py` — shape, column schema, reproducibility from a
  fixed seed, and invalid inputs for the synthetic panel generator.

Any other failure means a function no longer behaves as specified.

## Assumptions, Limitations, and Edge Cases

**Assumptions**
- Weeks before the start of the panel count as "no purchase" when building
  the 9-week exposure window.
- In the synthetic data, sanitizer purchases are independent across weeks
  (fixed weekly probability), and the exposure index uses a fixed
  `eta = 0.7`.

**Limitations**
- All data is synthetic; results check the software, not economic findings.
- Only the state-construction layer exists; forward simulation and model
  fitting are not implemented yet (see Next Step).
- The synthetic lotion-purchase rule has no intercept, so the baseline
  weekly purchase probability is 50%, higher than realistic. Synthetic
  prices are normal draws with no lower bound.

**Edge cases** (covered by tests)
- `eta = 1` gives a plain 9-week average.
- A stock exactly on a bin boundary (0.5, 1.5, 2.5) goes to the higher bin;
  everything from 2.5 up is `"3+"`.
- A panel with one household and one week is generated correctly.
- Invalid inputs raise `ValueError` instead of returning a wrong result:
  a purchase history that is not exactly 9 values of 0/1, `eta` outside
  (0, 1], `rho` outside (0, 1), a negative stock, or fewer than one
  household or week.

## Commands

All project commands are in the `Makefile`; run `make help` to list them.
Run them from the repository root with the environment active.

| Command | What it does |
|---|---|
| `make envs` | Create or update the environment and install the package |
| `make check` | Lint with ruff, then run the tests |
| `make test` | Run the tests only |
| `make docs` | Build the API documentation into `docs/` |
| `make serve` | Open the demo notebook in JupyterLab |
| `ruff format .` | Auto-format the code |
| `python scripts/generate_example_data.py` | Regenerate the example dataset |

## Current Status

**Milestone 2 (Sept 27):** The two analytical state-construction functions
(`exposure_index`, `inventory_transition` + `bin_inventory`) are implemented
and tested, including a regression test reproducing the paper's own worked
example at `rho = 0.84`. A synthetic panel generator (`synthetic_panel.py`)
produces data shaped like the real research panel for testing and
demonstration, and `demo_state_construction.ipynb` walks through
both. `ruff check .` and the full `pytest` suite (45 tests) pass cleanly.

**Milestone 3 (Oct 11):** added an environment check (`test_imports.py`) and
documented how to run the tests, what success and failure look like, and the
project's assumptions, limitations, and edge cases.

**Milestone 4 (Nov 1):** added generated API documentation (pdoc), the
expected demo output, and moved the activity reflections to
`paper/reflections.md`.

**Milestone 5 (Nov 15):** added a short `Makefile` as the single command
interface (`make envs`, `make check`, `make test`, `make docs`, `make serve`),
with `make` included in the environment so it also works on Windows.

## Next Step

The forward-simulation engine, planned for Milestone 3 in
`paper/proposal.md` (Section 4), is not implemented yet and is the next
piece of work: iterate the state transitions over a multi-week horizon under
an exposure-increase vs. baseline scenario, driven first by fixed
decision-rule parameters. Its tests will check that the response is zero
when the scenario equals the baseline and that repeated runs on the same
inputs give identical results. Model fitting (the data-driven layer) follows
after that.
