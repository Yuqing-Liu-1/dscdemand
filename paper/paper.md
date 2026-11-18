---
title: 'demand_propagation: A Tested Python Workflow for Dynamic Cross-Category Demand'
authors:
  - name: Yuqing Liu
    affiliation: '1'
affiliations:
  - name: Department of Agricultural, Food and Resources Economics, Michigan State University
    index: 1
bibliography: paper.bib
---

# Summary

`demand_propagation` is a small Python package that turns the computational
steps of a dynamic model of consumer demand into reusable, tested functions.
The motivating question is whether a surge in the use of one product (hand
sanitizer during COVID-19) creates delayed demand for a related product (hand
lotion), because heavy use of the first creates a need that the second
restores. The package builds the model's state variables from purchase
histories, generates synthetic household-week data, and simulates how lotion
purchases respond week by week to an extra sanitizer purchase, summarizing
the response with a gross and a net multiplier.

# Statement of need

The research behind this package studies restricted Nielsen Consumer Panel
data with a dynamic discrete choice model, and its analysis started as a set
of research scripts. Those steps were hard to check, rerun on new inputs, or
hand to a collaborator, and the data cannot be shared. `demand_propagation`
separates the core steps into documented functions, tests each one, and runs
on synthetic data with the same column schema as the real panel. Its intended
users are researchers who need to verify, reproduce, or extend this kind of
cross-category demand analysis without access to the restricted data.

# State of the field

Dynamic discrete choice models of consumer purchases build on the nested fixed
point approach of @rust1987 and on conditional-choice-probability methods
[@hotzmiller1993]. Consumer inventory behavior for storable goods is modeled in
@hendelnevo2006. Implementations of such models are usually written for one
study and data set, without separate tests for each step. This package does
not introduce a new estimator. Its contribution is a small, tested, and
documented implementation of the state construction and forward simulation
for a two-category exposure-and-inventory setting, built on NumPy
[@harris2020numpy] and pandas [@mckinney2010pandas].

# Software design

The package follows the three layers of the model:

- **State construction** (`state.py`): closed-form functions for the
  9-week, geometrically weighted sanitizer-exposure index and for the
  lotion-inventory stock, which depreciates each week and is grouped into
  bins. One test reproduces the worked example from the underlying paper.
- **Synthetic data** (`synthetic_panel.py`): generates a panel with the real
  panel's columns from known parameters, returned as a `truth` dictionary, so
  later estimation can be checked against known values.
- **Forward simulation** (`simulate.py`): simulates households under a
  baseline and a shocked scenario that share the same random draws. Because
  the draws are shared, the weekly response comes only from the shock: it is
  exactly zero when the scenarios match, and identical inputs always give
  identical results. Both properties are tested.

The main trade-off is simplicity over completeness. The research model solves
a Bellman equation and estimates household types; this package uses a fixed
logistic decision rule instead, so each step stays small enough to test and
runs in under a second on a laptop. A `Makefile` provides one command each for
setup, checks, documentation, and the demo notebook.

# Research impact

On synthetic data with the default settings, an extra sanitizer purchase
raises the weekly lotion-purchase probability by about 0.10 in the following
week. The effect fades, and later weeks turn slightly negative as households
that bought early hold more inventory. This gives a gross multiplier of 0.185
and a net multiplier of 0.150 extra lotion purchases per household over 26
weeks. These numbers check the software, not the economics. The package's
value is that the research workflow's core steps can now be tested, rerun,
and shared without the restricted data. The next step is a data-driven layer
that estimates the decision-rule coefficients and checks that it recovers the
known synthetic values.

# Project evolution and lessons learned

Reflections from each in-class activity are kept in
[`reflections.md`](reflections.md).

# AI usage disclosure

Generative AI (Anthropic's Claude, through Claude Code) was used to help write
and revise code, tests, documentation, and this manuscript, and to debug the
development environment. The author reviewed all changes, and the code is
checked by the automated test suite (`make check`).

# Acknowledgements

This project was developed for CMSE 802 at Michigan State University.

# References
