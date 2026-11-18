# Project Proposal

By Yuqing Liu

## Summary

This project builds a small, tested Python package, `demand_propagation`, that implements the computational workflow of a dynamic model of cross-category consumer demand. The motivating question is whether a surge in one product's use (hand sanitizer, during COVID-19) creates delayed, downstream demand for a related product (hand lotion) through *usage complementarity*: intensive use of the first product depletes a household-level condition that the second product restores. The package does not aim to produce new economic findings; it takes an existing dynamic-discrete-choice model and turns its analysis steps — building state variables, estimating a choice model, simulating forward in time, and computing summary impulse-response and multiplier statistics — into modular, documented, and independently testable software components with a reproducible environment.

## 1. Research Question / Problem

**Question:** After a household is exposed to more of an upstream product (sanitizer), how does its probability of purchasing a downstream product (lotion) evolve over the following weeks, and how much of that pattern is driven by (a) a direct demand effect versus (b) the household's own inventory dynamics (buying lotion now lowers the odds of buying it again soon)?

**Software problem:** The existing analysis that answers this question lives as a set of ad hoc research scripts. There is no separable, testable implementation of the core computational steps (state construction, model fitting, forward simulation, summary-statistic computation), so the workflow is hard to verify, rerun on new inputs, or hand off to a collaborator. This project's problem is a software-engineering one: convert that workflow into a package that can be installed, tested, and rerun end-to-end from documented inputs to documented outputs.

## 2. Model Components

The underlying model has three computational layers, each of which maps onto one of the modeling approaches used later in this course. Framing them this way also gives the semester timeline in Section 4 a natural structure.

| Layer | What it computes | Model type | Course module it matches |
|---|---|---|---|
| **State construction** | Closed-form transforms: a weighted-average exposure index from purchase history, and a deterministic inventory-stock recursion with a binning/discretization step | **Analytical** — fixed equations, no fitting or numerical simulation | Analytical Modeling (Milestone 2) |
| **Forward simulation** | Iterating the fitted decision rule and the inventory recursion forward in time, under an "exposure increase" scenario and a "no increase" baseline scenario, to trace out a response over a multi-week horizon | **Physical/dynamical-system style** — a discrete-time state-update rule simulated step by step, structurally the same problem as simulating any other discrete dynamical system forward in time | Physical Modeling (Milestone 3) |
| **Model fitting** | A logistic-regression estimate of the purchase probability as a function of the state, plus a second fitting step that folds in the estimated future-value effect | **Data-driven** — parameters are estimated from data, not assumed | Data-Driven Modeling (Milestone 4) |

The final package output — a per-week response curve and two summary multipliers (a "net" one that allows purchases now to be offset by fewer purchases later, and a "gross" one that only counts positive carryover) — is produced by composing these three layers in sequence.

## 3. Software Objective for the Semester

Build and document a `demand_propagation` package that:

1. Exposes independently testable functions for each of the three layers in Section 2.
2. Runs end-to-end on a small synthetic (non-restricted) example dataset shaped like the real data, producing the per-week response curve and multipliers from a single documented command.
3. Has an automated test suite (run with `pytest`) covering normal inputs, at least one edge case, and at least one invalid-input case per public function.
4. Has a reproducible Conda environment, a Makefile-driven workflow (`make help` lists the commands), and documentation sufficient for someone other than the author to run and extend it without guesswork.

This is a realistic, bounded scope: it does not require re-deriving the model or re-running the original restricted-data analysis, only re-implementing its computational steps as reusable, tested software.

## 4. First-Phase Plan and Timeline

The plan is staged to match the course milestones, since each milestone's focus (analytical / physical / data-driven / documentation) lines up with one layer of the model in Section 2.

| Date | Milestone | Deliverable for this project |
|---|---|---|
| **Sept 13** (Milestone 1, today) | Proposal + initial repo | This proposal; renamed `demand_propagation` package skeleton; environment and Makefile in place (current state, see README). *(Update: the template Makefile was removed on Oct 6 and replaced on Nov 15 by a short project Makefile; see README.)* |
| **Sept 27** (Milestone 2) | Analytical prototype | Working, tested functions for the exposure-index construction and the inventory-transition/binning step (the two closed-form pieces). |
| **Oct 11** (Milestone 3) | Testing & validation baseline | A forward-simulation function that iterates the state transitions over a fixed horizon under an exposure-increase vs. baseline scenario, initially driven by fixed or hand-calibrated decision-rule parameters (not yet the fitted model), plus tests that check basic dynamical properties (e.g., the response decays once exposure is removed, and runs are deterministic/reproducible given fixed inputs). |
| **Oct 25** (Milestone 4) | Documentation & reproducibility pass | Data-driven layer: the logistic-regression fitting step and the future-value offset step, plus wiring the simulation engine from Milestone 3 to consume the *fitted* decision rule instead of fixed parameters; synthetic example inputs and a documented data schema; README/docs updated to match the finished workflow. |
| **Nov 8** (Milestone 5a) | Systems & automation | A short `Makefile` as the project command interface (`make envs`, `make check`, `make test`, `make docs`, `make serve`) for setup, lint and test checks, documentation, and the demo. |
| **Nov 22** (Milestone 5b) | Release candidate | Frozen public API for the package, finalized docs, a fresh clone can go from the README setup steps (`conda env create`, `pip install -e .`) to reproduced example output with no undocumented steps. |
| **Dec 6** (Milestone 6) | Final submission | Completed `paper/paper.md` (JOSS-style), presentation materials. |

## 5. Testing and Validation Approach

- **Unit tests (`pytest`):** each public function in `demand_propagation` gets tests for known values, at least one edge case, and at least one invalid-input case, following the pattern already established in `demand_propagation/tests/test_state.py` and `demand_propagation/tests/test_synthetic_panel.py`.
- **Property/regression checks on the dynamical layer:** the forward-simulation output should satisfy simple invariants that are cheap to check automatically — e.g., the simulated response is zero when the exposure scenario equals the baseline scenario, the response is deterministic across repeated runs on the same inputs, and the inventory recursion never leaves the valid discretized range.
- **Output-level sanity check:** on the synthetic example data, the simulated per-week response curve should qualitatively match the shape reported in the underlying research (rising, peaking within the first several weeks, then decaying) — used as a build/sanity check on the software, not as a statistical claim about the synthetic data.
- **Code quality gates:** `ruff` (lint) and the `pytest` suite, run together with `make check`.

## 6. Success Metric

The project is successful if, at the end of the semester, a fresh clone of the repository can:

1. Follow the README setup steps (`conda env create`, `pip install -e .`) and then run `ruff check .` and `pytest` with zero lint errors and zero test failures.
2. Run the documented example workflow on the included synthetic input data and produce the per-week response curve and both multipliers without any manual/undocumented steps.
3. Show at least one test per public function in the package (normal case + edge case + invalid-input case), matching the pattern already in the test suite.

These are binary, checkable conditions rather than a claim about the statistical significance of any result — consistent with the goal of this project being the software, not new empirical findings.

## 7. Anticipated Challenges

- **Restricted data.** The empirical application uses Nielsen consumer panel data that cannot be redistributed. The package will therefore ship with small synthetic example inputs that have the same shape/schema as the real data, so the workflow can be demonstrated and tested publicly.
- **Coupling between layers.** The three layers in Section 2 are not fully independent — forward simulation ultimately needs the fitted model, and the fitted model needs the constructed states. The plan addresses this with a staged build order rather than requiring all three at once: state construction first (Milestone 2), then a simulation engine built and tested against fixed/hand-calibrated decision-rule parameters (Milestone 3, so the simulation logic itself can be validated independently), then the data-driven fitting step, at which point the simulation engine is reconnected to consume the fitted decision rule instead of the fixed placeholder (Milestone 4). Keeping the simulation engine's interface to the decision rule stable across this swap is what makes the staged order work.
- **Scope control.** The original research contains additional robustness checks (placebo categories, alternative depreciation-rate calibrations, alternative category pairs) that are valuable empirically but not necessary to demonstrate the core software workflow. These will be treated as optional stretch goals after the core pipeline in Section 4 is working and tested.

## 8. Expected Outcomes

A modular, documented, and tested `demand_propagation` package that reproduces the core computational pipeline (state construction → forward simulation → estimation → summary statistics) of the structural model, runnable end-to-end on shareable synthetic inputs. The repository will include: reusable Python functions organized by layer, an automated test suite, a reproducible environment, example inputs, and documentation describing how to run and extend the workflow.
