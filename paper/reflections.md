# Reflections

Short reflections from the in-class activities and how each one connects to
my project. The short versions are in the "Project evolution and lessons
learned" section of `paper.md`.

## Modeling Intro

In this first module we took a small barycentric-triangle script and turned it into a reusable module. Along the way we practiced Git and Ruff. Two habits stuck with me: using `git add -u` instead of `git add .` so I don't commit random files, and committing before running `ruff --fix` so I can look at the diff and see exactly what Ruff changed.

The idea I used most was the "A + P + D = 1" triangle, where you describe a project as a mix of Analytical, Physical, and Data-Driven parts. I used it to organize my proposal: building the states is the analytical part, simulating forward is the physical part, and fitting the model to data is the data-driven part. I still use this split when I explain the package to other people.

## Analytical Modeling

Part 1 used SymPy to solve models symbolically, for example the doubling time of exponential growth and the peak time in a caffeine-decay model. In Part 2 we generated fake ("phantom") data from a known model with `generate_dataset.py` and looked at how noise changes it. Part 3 went the other way: given noisy data, find the parameters `P0` and `r` of a decay model by searching over a grid. Part 4 was multiple regression with `statsmodels`, comparing a full model with a reduced one.

**What I learned.** Part 3 was the most interesting to me. Our estimates were within a few percent of the true values, but `P0` and `r` could trade off against each other: a bit more of one and a bit more of the other gave almost the same fit. So instead of one clear best point there was a long, flat valley, and noise moved `r` around more than `P0`.

**Most useful methods and tools.** Two simple checks before trusting a fit: make sure the best point is not on the edge of the search grid, and plot the residuals to see if there is a pattern. I also liked how `generate_dataset.py` was written, with clear error messages for bad inputs and docstrings with examples, and I tried to write my own functions the same way.

**Connection to my project.** My real data (the Nielsen panel) can't be shared, so I need fake data with known answers too. That is what `simulate` does in my package, and `test_parameter_recovery` checks that the estimator gets the true values back. I also ran into the same trade-off problem: in my model the intercept `a` and the inventory effect `lam` can partly make up for each other, which is one reason the estimates move when the state grid is built from data.

**Will I use this later?** Yes. Testing an estimator on simulated data before using it on real data is now the first thing I do. The full vs. reduced comparison from Part 4 also came back in my demo, where I compare a one-type and a two-type model with BIC.

## HPCC, Git, and the Terminal

These sessions connected MSU's HPCC with GitHub and moved me from the HPCC's graphical (GUI) apps, which were all I used before, to working in the terminal. This changed my research workflow and saves a large amount of time. I learned to submit jobs with `sbatch`: my data processing takes about 36 hours, and without a batch job I would have had to keep my own computer running and watch it the whole time. I also learned to `git pull` and `git push` on the HPCC, so my code and data stay consistent between my laptop and the remote jobs. Finally, I learned to create conda environments with the faster `libmamba` solver; I now use it in this project (`conda env create -f environment.yml --solver libmamba`), where it cut environment creation on my machine from about 24 minutes with the classic solver to under 2 minutes.

## Physical Modeling

We started with an SIR model, then solved the wave equation with finite differences (`wave2d.py`), and ended with finite-element software (MFEM and BESFEM). A big message of the module was to pick the method that fits the question: ODEs when rates between states matter, PDEs when things change over space, and finite elements when the geometry is complicated.

**What I learned.** A model is basically states plus rules for how things move between them, and the assumptions matter as much as the equations. A more complicated model is not always a better one.

**Most useful methods and tools.** The SIR way of thinking, and the discussion about compartment models (count how many people are in each state) versus agent-based models (simulate each person). I also thought about discretization: a grid makes the problem solvable, but you lose some accuracy depending on how fine the grid is.

**Connection to my project.** My demand model is actually the same kind of model. Each household has two stocks, exposure `K` and inventory `xi`, with simple update rules (`K' = eta*K + S`, `xi' = rho*xi + Q`), and buying moves a household from one state to another. My package even has both versions from the SIR discussion: `shock_response` moves the share of households in each state forward over time, like a compartment model, and `simulate` simulates each household, like an agent-based model. I also discretize the stocks into bins, so I have the same grid trade-off.

**Will I use this later?** Probably yes. One thing I haven't done yet is check how much my results change when I use more bins. That would be like checking a simulation on a finer grid.

## Data-Driven Modeling (Nov 3–12, 2026)

This unit went from summary statistics (weather data from the Open-Meteo API), to machine learning with scikit-learn (train/test splits, overfitting, always comparing to a simple baseline), to AutoML with TPOT, which we ran as Slurm job arrays on the HPCC.

**Which data-driven component could help my project?** At the time I thought logistic regression, since my proposal already planned to predict the weekly probability of buying lotion from exposure, inventory, and price. The other parts of my project can't give me these coefficients; only fitting to data can. I don't think AutoML fits my project well, because I need coefficients I can interpret (the exposure effect and the inventory effect), not just the pipeline with the best prediction score. It could still be useful to see how much better a flexible model predicts.

**Do I have enough data to trust it?** The synthetic example has 18,000 household-weeks (300 households x 60 weeks) and the model only has a few features, so that should be enough, and the real Nielsen panel is much bigger. One thing I had to think about is that weeks from the same household are not independent, because inventory carries over from week to week. So I would split train and test by household, not by row. The model should beat two baselines: always predicting the average purchase rate, and a model with inventory but no exposure. Beating the second one is what would show that exposure really adds something.

**What evidence would I need, and what would a teammate need?** First, parameter recovery: on simulated data the estimates should be close to the true values, which is now checked by `test_parameter_recovery`. Second, a better held-out log-loss than the baselines. A teammate only needs the repository: `make init`, `make check`, and the fixed seed in `simulate`. The hardest of the five properties for me is **Reproducible**, because the Nielsen data are restricted and can't be shared. My plan is to keep the synthetic data in exactly the same format as the real panel, so everything except the real-data run can be repeated by anyone.

**Update (Nov 20).** In the end I used a dynamic logit instead of a plain logistic regression. It is still a logit for the probability of buying, but it also includes the value of waiting (from the Bellman equation), and it is estimated by nested fixed point maximum likelihood. The plan for evidence stayed the same: parameter recovery is tested, and the demo compares predicted and observed weekly purchase rates.
