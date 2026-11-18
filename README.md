# Dynamic Cross-Category Demand Propagation

`demand_propagation` is a small, tested Python package for a dynamic model of
cross-category consumer demand. The motivating question: does a surge in hand
sanitizer use (as during COVID-19) cause delayed, downstream demand for hand
lotion, because heavy use of one product creates a need that the other
restores?

The package turns the research workflow into reusable, testable steps. It runs
entirely on synthetic data, so it checks the software, not economic findings.
See [`paper/proposal.md`](paper/proposal.md) for the full proposal.

## What It Does

| Layer | Module | What it computes | Status |
|---|---|---|---|
| State construction | `state.py` | Sanitizer-exposure index; lotion-inventory stock and its bins | Done |
| Synthetic data | `synthetic_panel.py` | Household-week panel with the real panel's columns, from known parameters | Done |
| Forward simulation | `simulate.py` | Weekly lotion-purchase response to an extra sanitizer purchase; gross and net multipliers | Done (fixed coefficients) |
| Model fitting | — | Estimate the decision-rule coefficients from data | Not started |

## Installation

Requires [conda](https://docs.conda.io/). From the repository root
(macOS/Linux):

```
make init
conda activate demand_propagation
make check
```

`make init` creates the conda environment and installs the package with
`pip install -e .`. `make check` should end with `58 passed`.

**Windows:** `make` is not preinstalled, but the environment includes it. The
first time, run the commands that `make init` runs, then use `make`:

```
conda env create -f environment.yml --solver libmamba
conda activate demand_propagation
pip install -e .
make check
```

If conda does not recognize `--solver libmamba`, run `conda update -n base conda`
first.

## Quick Start

```
make serve
```

This opens `demo.ipynb` in JupyterLab. Choose **Kernel → Restart Kernel and
Run All Cells**. The notebook explains each step: the exposure index, the
inventory stock (reproducing the paper's worked example at `rho = 0.84`), a
synthetic panel, and the forward simulation. If you open the notebook another
way (an already running Jupyter, or VS Code), select the `demand_propagation`
environment as the kernel.

Expected result of the simulation step (500 households, 26 weeks, seed 0):
the response is 0 in week 0, about `0.097` in week 1, fades over the next
weeks, and turns slightly negative around weeks 5–14 as households that
bought early hold more inventory. The multipliers are:

```
{'gross': 0.185315317596, 'net': 0.149830004288}
```

## Commands

Run from the repository root with the environment active (`make help` lists
them):

| Command | What it does |
|---|---|
| `make init` / `make envs` | Create or update the environment and install the package |
| `make check` | Lint with ruff, then run the tests |
| `make test` | Run the tests only |
| `make docs` | Build the API documentation into `docs/`; open `docs/index.html` |
| `make serve` | Open the demo notebook in JupyterLab |

`python scripts/generate_example_data.py` regenerates the example dataset.

## Testing

`make test` (or `pytest`) runs every `test_*` function in
`demand_propagation/tests/`. Success ends with `58 passed`; a failure names the
test and the line that failed.

- `test_imports.py` — numpy, pandas, and the package import. If this fails,
  the environment is not set up; fix that first.
- `test_state.py` — known values (including the paper's worked example),
  bin boundaries, and invalid inputs.
- `test_synthetic_panel.py` — shape, columns, reproducibility from a seed,
  and invalid inputs.
- `test_simulate.py` — zero response without a shock or without spillover
  (`alpha = 0`), identical results for identical inputs, a positive response
  in the week after the shock, net never above gross, and invalid inputs.

## Assumptions and Limitations

- **Synthetic data only.** The research uses restricted Nielsen Consumer Panel
  data, which is not included anywhere in this repository. The generator uses
  the same column schema.
- **Fixed decision rule.** Purchases follow
  `Pr(buy) = logistic(alpha * exposure - lam * inventory_bin)` with
  `alpha = 1.5`, `lam = 0.6`. The rule has no intercept, so the baseline weekly
  purchase probability is 50%, higher than realistic. These coefficients are
  assumed, not estimated.
- **Simplified dynamics.** Unlike the full research model, households do not
  plan ahead (no Bellman equation) and are all the same type.
- **Monte Carlo noise.** The simulation averages simulated households, so
  late weeks show small random wiggles around zero; more households reduce
  them.
- **State conventions.** Weeks before the start of the data count as "no
  purchase"; a stock on a bin boundary (0.5, 1.5, 2.5) goes to the higher bin.
  Invalid inputs raise `ValueError`.

## Repository Structure

```
demand_propagation/   package: state.py, synthetic_panel.py, simulate.py, tests/
demo.ipynb            walkthrough of the whole workflow
scripts/              generate_example_data.py
data/example/         synthetic_panel.csv (50 households x 20 weeks, no real data)
paper/                proposal.md, paper.md (JOSS-style manuscript), reflections.md
Makefile              project commands
environment.yml       conda environment
pyproject.toml        package metadata; pytest and ruff settings
AGENTS.md, CLAUDE.md, guides/   guidance for AI coding assistants
```

## Course Milestones

| Milestone | Where to find it |
|---|---|
| 2 – Analytical prototype | `state.py`, `synthetic_panel.py`, their tests |
| 3 – Testing and validation | [Testing](#testing), [Assumptions and Limitations](#assumptions-and-limitations) |
| 4 – Documentation | This README, `make docs`, `demo.ipynb` |
| 5 – Systems and automation | `Makefile` ([Commands](#commands)) |
| Reflections | [`paper/reflections.md`](paper/reflections.md) |

## Next Steps

Estimate the decision-rule coefficients (`alpha`, `lam`) from data with a
logistic regression, check that it recovers the known values from synthetic
data, and run the forward simulation with the fitted coefficients.
