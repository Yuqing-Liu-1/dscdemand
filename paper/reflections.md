# Reflections

Short reflections from the in-class activities, connecting each one to this
project. They will later be refined into the final report (`paper.md`).

## Modeling Intro

The `modeling_intro` activity used a small barycentric-triangle script to practice the arc from a working script to a reusable module, and to introduce Git hygiene (`git add -u` instead of `git add .`, commit messages that explain *why*, committing before letting Ruff auto-fix anything) and a basic Ruff workflow (`check` → investigate a warning → `--fix` → `format`, always followed by `git diff` review rather than blind trust). The most useful idea was the "A + P + D = 1" triangle for classifying a project's mix of Analytical, Physical, and Data-Driven components — I used this framing directly in the project proposal's Model Components table (state construction as Analytical, forward simulation as Physical/dynamical-system, CCP/MLE fitting as Data-Driven), so it is already shaping how the semester timeline is staged. Going forward I plan to keep the `git add -u` + reviewed-diff discipline for every milestone, and to revisit the triangle classification if the package's scope shifts.

## Analytical Modeling

Part 1 used SymPy to define a model symbolically rather than numerically and solve it directly (e.g. doubling time for exponential growth, peak/threshold times for a multi-dose caffeine-decay model). Part 2 introduced generating synthetic ("phantom") data from a known model with `generate_dataset.py`, inspecting how the `noise_fraction` parameter changes the observations, and a short code review of the module itself. Part 3 turned this around into parameter estimation: recovering `P0` and `r` of a decay model from noisy data by searching a parameter grid. Part 4 moved to multiple regression with `statsmodels`, comparing a full model with a reduced one and checking residual diagnostics.

**What I learned.** An analytical model is most useful as a known truth to test against. In Part 3 the recovered parameters landed within a few percent of the truth, but `P0` and `r` traded off against each other, so the error surface had a shallow valley of nearly equally good fits rather than one sharp minimum, and noise moved `r` more than `P0`.

**Most useful methods and tools.** Synthetic data with a hidden truth kept separate from the noisy observations, and two debugging checks before trusting a fit: make sure the best fit does not sit on the boundary of the search region, and plot the residuals to look for systematic patterns. The design of `generate_dataset.py` (explicit input validation with a clear `ValueError`, NumPy-style docstrings) is the pattern I followed for the package's own functions.

**Connection to my project.** `dscdemand` has the same structure: the real Nielsen panel is restricted, so `StorableComplementaryModel.simulate` generates panels from known parameters, and `test_parameter_recovery` checks that the estimator finds them. The same trade-off problem appears in my model: the intercept `a` and the inventory effect `lam` can partly substitute for each other, which is why building the state grid from data shifts the intercept and attenuates `lam` (listed as a limitation in the README).

**Will I adopt it?** Yes, and I already have: every estimation feature in the package is tested against simulated data with known parameters first, and full vs. reduced model comparison reappears as the one-type vs. two-type comparison by BIC in `demo.ipynb`.

## HPCC, Git, and the Terminal

These sessions connected MSU's HPCC with GitHub and moved me from the HPCC's graphical (GUI) apps, which were all I used before, to working in the terminal. This changed my research workflow and saves a large amount of time. I learned to submit jobs with `sbatch`: my data processing takes about 36 hours, and without a batch job I would have had to keep my own computer running and watch it the whole time. I also learned to `git pull` and `git push` on the HPCC, so my code and data stay consistent between my laptop and the remote jobs. Finally, I learned to create conda environments with the faster `libmamba` solver; I now use it in this project (`conda env create -f environment.yml --solver libmamba`), where it cut environment creation on my machine from about 24 minutes with the classic solver to under 2 minutes.

## Physical Modeling

The module started with an SIR model as a first computational model (a system written as state variables plus rules for moving between states), then moved to the wave equation solved by finite differences (`wave2d.py`), and ended with finite-element software (MFEM and BESFEM), where the main lesson was choosing the method to match the question: ODEs when rates between states matter, PDEs when the system evolves in space, finite elements when the geometry is complex.

**What I learned.** A model is a translation of a system into states, rates, and update rules, and its assumptions matter as much as its equations. The most complicated model is not automatically the right one.

**Most useful methods and tools.** The SIR way of thinking, and the comparison between a compartment model (track how many units are in each state) and an agent-based model (simulate each unit). Discretization was the other key idea: a grid makes a continuous problem solvable, at the cost of resolution error.

**Connection to my project.** My demand model is a state-and-rules model of the same kind. Each household has two stocks, exposure `K` and inventory `xi`, that follow update rules (`K' = eta*K + S`, `xi' = rho*xi + Q`), and the purchase decision moves households between states. The package uses both views from the SIR discussion: `shock_response` pushes the *distribution* of households over the state grid forward in time, like a compartment model, while `simulate` draws individual households, like an agent-based model. Discretizing the stocks into bins is the same trade-off as a simulation grid, and it is why the README lists grid resolution as a limitation.

**Will I adopt it?** Yes. The counterfactuals are already computed as a forward simulation of the state distribution, and a natural next step is to check how results change with the number of bins, the same way one checks a simulation against grid refinement.

## Data-Driven Modeling (Nov 3–12, 2026)

The unit moved from summary statistics (weather data from the Open-Meteo API), to classical machine learning with scikit-learn (supervised vs. unsupervised learning, train/test splits, overfitting, comparing every model against a simple baseline), to bounded AutoML searches with TPOT, run as Slurm job arrays on the HPCC with one record per random seed.

**Which data-driven component could help my project?** Classical machine learning, specifically logistic regression, which is already the planned data-driven layer in `paper/proposal.md`. It estimates the weekly probability of buying lotion from the state variables (sanitizer exposure index, inventory bin, price). This answers a question the other components cannot: the analytical layer only builds the states, and the forward simulation needs a decision rule, but only fitting gives that rule's coefficients from data instead of assuming them. Summary statistics are still useful as the baseline. AutoML does not fit the main goal: the simulation needs interpretable coefficients (the exposure effect and the inventory effect), and a TPOT pipeline chosen for predictive score does not provide them. At most it could show how much predictive accuracy a flexible model would add.

**Do I have enough data to trust it?** The committed synthetic example has 18,000 household-weeks (300 households x 60 weeks) and the model needs only a few features (exposure, inventory, price, an event indicator), so the model is small enough to estimate; the real Nielsen panel is much larger. Rows from the same household are not independent (inventory and the purchase lags carry over from week to week), so I would split train and test by household, with all weeks of a household in one split, to avoid leakage. The model must beat two baselines: always predicting the overall purchase rate, and a model with inventory but no exposure term. Only beating the second one shows that exposure adds information.

**What evidence would I need, and what would a teammate need?** Because the synthetic data is generated from known parameters, the first piece of evidence is parameter recovery: the fitted coefficients should land close to the true values, checked by an automated test (now `test_parameter_recovery` in `dscdemand/tests/test_models.py`). The second is a better held-out log-loss than both baselines. A teammate needs only the repository: `make init`, `make check`, and the fixed seed in `StorableComplementaryModel.simulate`. The hardest property is **Reproducible** on the real data, because the Nielsen panel is restricted and cannot be shared. My concrete step is to keep the synthetic generator on exactly the same column schema as the real panel, so every fitting step can be rerun and tested publicly, and to document the real-data run separately.

**Update (Nov 20).** The data-driven layer ended up as a dynamic logit rather than a static logistic regression: the purchase probability is still a logit, but it includes each household's continuation value from the Bellman equation and is estimated by nested fixed point maximum likelihood. The evidence plan above carried over unchanged: parameter recovery on synthetic data is tested, and `demo.ipynb` compares predicted with observed weekly purchase rates.

**Partner question I could not yet answer:** *(to add after sharing this entry with a partner)*
