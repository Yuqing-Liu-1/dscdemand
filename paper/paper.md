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
date: 20 November 2026
bibliography: paper.bib
---

# Summary

For a storable good, a purchase is not a use: a household that buys hand
lotion may be restocking rather than using more. This makes it hard to tell
from purchase records alone whether buying one product, such as hand
sanitizer, creates real demand for another product whose need it creates,
such as hand lotion. `dscdemand` is a Python package that separates these
forces with a forward-looking (dynamic) model of household purchases. Each
week a household decides whether to buy, given two stocks built from its own
history: **exposure** from recent purchases of the upstream good, and
**inventory** of the downstream good. From a household-week panel the
package estimates how much exposure raises demand (the spillover), how much
inventory lowers it (stockpiling), and whether households differ in ways
that would otherwise be mistaken for either effect. It then simulates how
demand evolves week by week after a shock to upstream purchases.

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
organization, and applied economics who work with consumer panel data, which
are often restricted; the package therefore ships a simulator that produces
shareable panels with the same schema and known parameters.

# State of the field

\autoref{tab:field} compares `dscdemand` with related open-source software.
General discrete choice libraries such as Choice-Learn
[@auriau2024choicelearn] estimate static models of choice among alternatives.
Dynamic discrete choice software is organized around estimators or specific
applications: EconIRL [@econirl] implements nested fixed point, conditional
choice probability, and inverse reinforcement learning estimators for tabular
dynamic problems, and respy [@respy] targets finite-horizon models of labor
supply and schooling. `dscdemand` is complementary to these: it is organized
around consumer demand, with the inventory and cross-category exposure states,
purchase volumes, prices, and counterfactuals that marketing and policy
questions require already built in.

: Related open-source software. \label{tab:field}

| Package | Choice setting | Estimation | Built-in demand states |
|---|---|---|---|
| Choice-Learn | static choice among alternatives | maximum likelihood, incl. latent classes | none |
| respy | dynamic, finite horizon (labor, schooling) | likelihood, simulated moments | none |
| EconIRL | dynamic, generic tabular problems | NFXP, CCP, inverse RL | none |
| `dscdemand` | dynamic, infinite horizon (household purchases) | NFXP, EM over household types | inventory, cross-category exposure |

# Software design

\autoref{fig:workflow} shows the organization. A `PanelDataset` validates a
household-week panel and maps its columns to model roles (upstream purchases,
downstream purchase and volume, price, and covariates). A shared engine then
does the work that every model in the package needs:

- `states` builds the exposure stock $K_{t+1} = \eta K_t + S_t$ and the
  inventory stock $\xi_{t+1} = \rho\,\xi_t + d_t Q_t$, discretizes them with a
  separate zero bin, and forms their Markov transitions;
- `bellman` solves the household's dynamic program by value-function
  iteration on the $(K, \xi)$ grid;
- `likelihood` scores observed choices with the resulting dynamic logit, so
  parameters are estimated by nested fixed point maximum likelihood
  [@rust1987];
- `em` fits a finite mixture of household types with the EM algorithm
  [@arcidiaconojones2003];
- `counterfactual` pushes the distribution of households over states forward
  under a shocked and a baseline scenario that differ only in the shock, so a
  zero shock gives exactly zero response.

![Organization of `dscdemand`. Data enter as a `PanelDataset`, either real or
simulated with known parameters; a shared engine estimates the model; the
fitted model reports parameters, fit, the purchase policy, and
counterfactual responses. \label{fig:workflow}](figures/workflow.png)

The available model, `StorableComplementaryModel`, sets the flow utility of
buying to
$u_1 = a + f(K) + \lambda \xi + \alpha\,\text{price} + \sum_j b_j x_j$,
with $f$ piecewise linear (slopes $\gamma_1$ and $\gamma_2$ below and above a
kink), and lets selected parameters vary by type. Covariates marked as
unanticipated, such as a sudden event, are left out of households'
expectations. A complete analysis takes a few lines:

```python
from dscdemand import StorableComplementaryModel, load_example

model = StorableComplementaryModel(
    eta=0.6, rho=0.8, n_types=1, unanticipated=("event",)
)
model.fit(load_example())
model.params_  # spillover gamma, stockpiling lam, ...
model.predict_proba()  # fitted purchase probabilities
model.policy()  # P(buy) on the (K, xi) grid
model.shock_response(shock=2.0, weeks=26)
```

Storable-only and complementary-only models are planned on the same
interface. The design trades generality for transparency: states are
discretized and the stock retention rates and discount factor are fixed,
which keeps each step small enough to test. The 43 automated tests check the
Bellman fixed point, recovery of known parameters from simulated data, a zero
response to a zero shock, and that EM never lowers the likelihood. The package
builds on NumPy [@harris2020numpy], pandas [@mckinney2010pandas], and SciPy
[@virtanen2020scipy].

# Research impact

The storable-complementary model was developed for research on whether the
COVID-19 surge in hand sanitizer purchases created delayed demand for hand
lotion, using restricted consumer panel data. `dscdemand` turns that analysis
into a reusable workflow that can be run and checked on shareable data. The
illustration below uses the included synthetic panel (300 households over 60
weeks, with a three-week surge in upstream purchases), generated with known
parameters; all figures are reproduced by `make figures`.

**Spillover and stockpiling.** The estimates recover the signs and
magnitudes of the true model: exposure raises the value of buying
($\hat\gamma_1 = 0.62$, true 0.8) and inventory lowers it
($\hat\lambda = -2.02$, true $-2.5$). The model reproduces the weekly
purchase rate, including the jump during the surge
(\autoref{fig:results}a), and the implied purchase policy rises with exposure
and falls with inventory (\autoref{fig:results}b).

**Stockpiling or heterogeneity?** Frequent buyers both buy more and hold more
inventory, so ignoring differences between households biases both effects.
\autoref{tab:types} fits a panel simulated with two household types: the
one-type model understates the spillover and the inventory effect, while EM
recovers the type shares, assigns 98% of households to their true type, and
is strongly preferred by BIC. On real data, this comparison tests whether an
apparent own-history effect is genuine.

: One-type and two-type fits of a panel simulated with two household types
(300 households, 60 weeks; true $\gamma_1 = 0.8$, $\lambda = -0.5$, type
shares 0.4 and 0.6). \label{tab:types}

| Model | $\hat\gamma_1$ | $\hat\lambda$ by type | Type shares | Log-likelihood | BIC |
|---|---|---|---|---|---|
| One type | 0.43 | $-0.14$ | 1.00 | $-6593.0$ | 13244.8 |
| Two types (EM) | 0.63 | $-0.65$, $-0.32$ | 0.42, 0.58 | $-6309.0$ | 12706.2 |

**Dynamics.** After one extra upstream purchase, the probability of buying
rises at once and fades over about ten weeks; it then turns slightly
negative as households that bought early hold more inventory
(\autoref{fig:results}c). Summing the weekly responses, 17% of the extra
purchases from a typical shock are offset later, and the effect per unit of
shock is smaller for an event-sized shock, because the spillover flattens
above the kink. Because the data interface is general, the same workflow
applies to other pairs of related categories.

![Results on the synthetic example panel. (a) Observed and predicted weekly
purchase rates; the shaded weeks are the upstream surge. (b) Estimated
probability of buying by exposure $K$ and inventory $\xi$. (c) Change in the
probability of buying after one extra upstream purchase of typical (2 units)
and event-sized (4 units) magnitude. \label{fig:results}](figures/results.png)

# Project evolution and lessons learned

Full reflections from each course module are kept in
[`reflections.md`](reflections.md).

## Modeling Intro

Classifying the project by its Analytical, Physical, and Data-Driven parts
shaped the package layout: state construction is analytical, the
counterfactual is a forward simulation, and estimation is data driven. The
module also set the working habits used throughout: small reviewed commits
and Ruff checks before every change.

## Analytical Modeling

Recovering parameters from synthetic data with a known truth showed that two
parameters can trade off along a valley of equally good fits. The same issue
appears here between the intercept and the inventory effect, and the same
remedy is used: every estimator is first tested on data simulated from known
parameters (`test_parameter_recovery`).

## Physical Modeling

Viewing a system as states plus update rules maps directly onto this model:
exposure and inventory are stocks with linear update rules. The counterfactual
pushes the distribution of households over states forward like a compartment
model, while `simulate` draws individual households like an agent-based model.
Discretizing the stocks carries the usual grid-resolution trade-off.

## Data-Driven Modeling

The data-driven layer became a dynamic logit estimated by maximum likelihood
rather than a predictive model chosen by AutoML, because the counterfactuals
need interpretable spillover and inventory effects. Trust rests on parameter
recovery, a weekly comparison of predicted and observed purchase rates, and
fully reproducible synthetic data, since the research data are restricted.

# AI usage disclosure

Generative AI (Anthropic's Claude, through Claude Code) was used to help write
and revise code, tests, documentation, and this manuscript, and to adapt the
author's research code into a general package. The author reviewed all
changes, and the code is checked by the automated test suite (`make check`).

# Acknowledgements

This project was developed for CMSE 802 at Michigan State University.

# References
