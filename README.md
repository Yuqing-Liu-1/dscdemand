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

- `paper/` — `proposal.md` (this project's proposal) and `paper.md` (JOSS-style manuscript, filled in later).
- `demand_propagation/` — the Python package; currently the starter template functions and tests, to be replaced by the state-construction, simulation, and fitting modules described above.
- `scripts/` — supporting scripts (e.g. `rename_package.py`, already run to rename the starter package to `demand_propagation`).
- `environment.yml` — Conda environment and dependencies.
- `makefile` — documented workflow commands (see below).
- `pyproject.toml` — tool configuration for pytest, ruff, and mypy.
- `00_START_HERE.ipynb` — walkthrough notebook from the course software template.

A `data/` directory (synthetic/example inputs only — no restricted data) will
be added once the state-construction functions exist to consume it.

## Data Availability

The empirical application uses restricted Nielsen consumer purchase data
that cannot be distributed with this repository. The project will use small
synthetic or non-confidential example inputs, shaped like the real data, to
demonstrate and test the computational workflow.

## Environment and Installation

The project environment is defined in `environment.yml`. The starter test
suite has been verified directly with `pytest -v` (17 tests passing) inside
an activated environment. The `makefile` provides the intended convenience
commands (`make init`, `make check`, etc.) for a reproducible workflow, but
`make init` itself has not yet been validated end-to-end — see the note
below — so treat it as the planned entry point rather than a confirmed one
for now.

Run `make help` for the full list of commands (`lint`, `format`, `test`,
`type`, `docs`, `check`, `check-full`, `clean`). The repository is based on
the CMSE 802 Scientific Software Starter Template.

**Known gap:** `environment.yml` creates the environment at `./envs`, while
`makefile`'s `init` target passes `--prefix=./.envs` (extra dot). The
Makefile also uses Unix shell commands (`rm`, `find`) that are not
guaranteed to work from `cmd.exe`/PowerShell without a POSIX-compatible
shell. This will be fixed and `make init && make check` validated end-to-end
by Milestone 2.

## Current Status

**Milestone 1 (Sept 13):** Repository scaffold, proposal, and Conda
environment are in place. The starter package has been renamed
`mypackage` → `demand_propagation` (via `scripts/rename_package.py`); the
package currently still contains the template's placeholder functions and
tests, which will be replaced starting with the next milestone.

## Next Step

**By Milestone 2 (Sept 27):** implement and test the two analytical
state-construction functions — the sanitizer-exposure index (weighted
average over the past nine weeks) and the lotion-inventory transition
(deterministic depreciation-plus-purchase recursion, with a discretization
step into inventory bins). These are the first components in the planned
workflow (Section 4 of `paper/proposal.md`) and have no dependency on model
fitting, so they are the natural starting point.
