---
title: 'dscdemand: Dynamic demand models for storable and complementary goods in Python'
tags:
  - Python
  - dynamic discrete choice
  - consumer demand
  - storable goods
  - complementary goods
authors:
  - name: Yuqing Liu
    affiliation: '1'
affiliations:
  - name: Department of Agricultural, Food, and Resource Economics, Michigan State University
    index: 1
bibliography: paper.bib
---

# Summary

`dscdemand` estimates forward-looking models of household demand from
household-week panel data. It focuses on two features of everyday consumer
goods that static demand models miss. Goods are **storable**, so a purchase
today lowers the need to buy next week. Goods are **complementary in use**:
heavy use of one product, such as hand sanitizer, creates a need that another
product, such as hand lotion, restores. The package fits these models by
nested fixed point maximum likelihood [@rust1987], allows discrete unobserved
household types through the EM algorithm [@arcidiaconojones2003], and reports
the week-by-week purchase response to a shock, summarized by a gross and a net
multiplier. Users bring their own data as a `pandas` DataFrame; all models
share one interface (`fit`, `simulate`, `shock_response`).

# Statement of need

Dynamic models of storable goods are standard in marketing and industrial
organization [@erdemimaikeane2003; @hendelnevo2006], and dynamic models of
complementary goods study tied goods and add-ons [@hartmannnair2010;
@liuetal2018]. Yet researchers usually re-implement the Bellman solver, the
likelihood, the treatment of unobserved types, and the counterfactual
simulation for each study. Replication files, where available, are scripts for
one paper rather than reusable tools, and the Archive of Empirical Dynamic
Programming [@aedp] catalogs such studies but provides little runnable code
for them. `dscdemand` gives these models a tested, documented implementation
that runs on any household-week panel, and adds a model that combines
storability with usage complementarity, a case the existing literature covers
little. Its intended users are researchers in marketing, industrial
organization, and applied economics who work with consumer panel data.

# State of the field

General discrete choice libraries such as Choice-Learn
[@auriau2024choicelearn] estimate static models. Dynamic discrete choice
software is organized around estimators or specific applications: EconIRL
[@econirl] implements many estimators, including nested fixed point and
conditional choice probability methods, for tabular dynamic problems and
inverse reinforcement learning, and respy [@respy] targets finite-horizon
models of labor supply and schooling. `dscdemand` is complementary to these:
it is organized around consumer demand models (inventory, cross-category
exposure, purchase volume, and price) and the counterfactuals that marketing
and policy questions require.

# Software design

The package separates **models** from a shared **engine**:

- `data.PanelDataset` validates a household-week panel and maps its columns to
  model roles (upstream purchases, downstream purchase and volume, price, and
  covariates).
- `states` builds the exposure stock $K_{t+1} = \eta K_t + S_t$ and the
  inventory stock $\xi_{t+1} = \rho\,\xi_t + d_t Q_t$, discretizes them with a
  separate zero bin, and forms their Markov transitions.
- `bellman`, `likelihood`, and `em` solve the dynamic program by
  value-function iteration, score observed choices, and fit finite mixtures of
  household types.
- `counterfactual` pushes the distribution of households over states forward
  under a shocked and a baseline scenario that differ only in the shock, so a
  zero shock gives exactly zero response.

The available model, `StorableComplementaryModel`, sets the flow utility of
buying to
$u_1 = a + f(K) + \lambda \xi + \alpha\,\text{price} + \sum_j b_j x_j$,
with $f$ piecewise linear, and lets selected parameters vary by type.
Covariates marked as unanticipated (for example, a sudden event) are excluded
from households' expectations. Storable-only and complementary-only models are
planned on the same interface. The design trades generality for transparency:
states are discretized and the stock retention rates and discount factor are
fixed, which keeps each estimation step small enough to test. Tests check the
Bellman fixed point, recovery of known parameters from simulated data, a zero
response to a zero shock, and that EM never lowers the likelihood. The package
builds on NumPy [@harris2020numpy], pandas [@mckinney2010pandas], and SciPy
[@virtanen2020scipy].

# Research impact

The storable-complementary model was developed for research on whether the
COVID-19 surge in hand sanitizer use created delayed demand for hand lotion,
using restricted consumer panel data. `dscdemand` makes that analysis
reusable: on the included synthetic panel, one extra upstream purchase raises
the weekly purchase probability by about 0.03, and about 17% of the extra
demand is later offset as households draw down inventory. Because the data
interface is general, the same workflow applies to other pairs of related
categories.

# Project evolution and lessons learned

Reflections from each in-class activity are kept in
[`reflections.md`](reflections.md).

# AI usage disclosure

Generative AI (Anthropic's Claude, through Claude Code) was used to help write
and revise code, tests, documentation, and this manuscript, and to adapt the
author's research code into a general package. The author reviewed all
changes, and the code is checked by the automated test suite (`make check`).

# Acknowledgements

This project was developed for CMSE 802 at Michigan State University.

# References
