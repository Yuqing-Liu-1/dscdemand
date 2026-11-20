# dscdemand

**Dynamic Storable–Complementary demand models in Python.**

`dscdemand` estimates forward-looking models of household demand from
household-week panel data. It targets goods that consumers **store** and
goods whose need is created by using a **complementary** product, such as hand
lotion after heavy hand-sanitizer use. Models are fit by nested fixed point
maximum likelihood, allow unobserved household types (EM), and produce the
week-by-week purchase response to a shock.

## Getting Started

The full workflow from a fresh clone takes about 10 minutes. You need
[git](https://git-scm.com/) and [conda](https://docs.conda.io/en/latest/miniconda.html)
(Miniconda or Anaconda). On Windows, run the commands in the **Anaconda
Prompt**.

**1. Get the code**

```
git clone https://github.com/Yuqing-Liu-1/Demand_propagation.git dscdemand
cd dscdemand
```

**2. Install** the environment, the package, and the Jupyter kernel.

macOS/Linux:

```
make init
conda activate dscdemand
```

Windows (`make` is installed with the environment, so the first time run):

```
conda env create -f environment.yml --solver libmamba
conda activate dscdemand
pip install -e .
python -m ipykernel install --user --name dscdemand --display-name "Python (dscdemand)" --env OPENBLAS_NUM_THREADS 1
```

**3. Check** that everything works:

```
make check
```

Expected: `All checks passed!` from ruff, then the tests end with
`43 passed`.

**4. Run the demo.** Open [`demo.ipynb`](demo.ipynb) (`make serve` opens it in
JupyterLab, or open it in VS Code), select the kernel **Python (dscdemand)**,
and run all cells (about a minute). Your results should match the outputs
saved in the notebook. If the first cell fails with
`ModuleNotFoundError: dscdemand`, the wrong kernel is selected.

**5. Read the API documentation:** `make docs`, then open `docs/index.html`.

**6. Read the paper:** [`paper/paper.md`](paper/paper.md) is the JOSS-style
manuscript; [`paper/reflections.md`](paper/reflections.md) holds the
reflections from each course module.

| Notebook | What it shows |
|---|---|
| [`demo.ipynb`](demo.ipynb) | A complete analysis in eight steps: data, model, estimation, model fit, purchase policy, stockpiling vs. heterogeneity (EM), and the week-by-week response to an upstream shock |

The demo answers three questions: does buying the upstream good raise
demand for the downstream good (spillover)? Does holding inventory lower it,
and does that survive once households are allowed to differ? And how does
one extra upstream purchase play out over the following weeks?

## Models

| Model | File | Idea | Literature | Status |
|---|---|---|---|---|
| Storable goods | [`storable.py`](dscdemand/models/storable.py) | Stockpiling and consumption from inventory | Erdem, Imai & Keane (2003); Hendel & Nevo (2006) | Planned |
| Complementary goods | [`complementary.py`](dscdemand/models/complementary.py) | Buying one good raises the value of another (tied goods, add-ons) | Hartmann & Nair (2010); Liu, Derdenger & Sun (2018) | Planned |
| Storable + complementary | [`storable_complementary.py`](dscdemand/models/storable_complementary.py) | Upstream purchases build exposure that raises demand for a storable downstream good | This package | **Available** |

All models share one interface (`fit`, `simulate`, `shock_response`) and the
same engine: state construction, Bellman solver, likelihood, and EM.

## Quick Start

```python
from dscdemand import StorableComplementaryModel, load_example, multipliers

dataset = load_example()
model = StorableComplementaryModel(eta=0.6, rho=0.8, unanticipated=("event",))
model.fit(dataset)

model.params_  # utility parameters: spillover (gamma), stockpiling (lam), ...
model.predict_proba()  # predicted purchase probability for every household-week
model.policy()  # probability of buying at each exposure x inventory state
response = model.shock_response(shock=2.0, weeks=26)
multipliers(
    response["response"]
)  # {'gross': 0.090, 'net': 0.075, 'offset_ratio': 0.173}
```

On the example data, recent upstream purchases raise the probability of
buying (`gamma1 > 0`) and inventory lowers it (`lam < 0`). One extra
upstream purchase raises demand for a few weeks; households that bought
early then hold inventory and buy less, offsetting about 17% of the extra
demand. `StorableComplementaryModel(..., n_types=2)` adds unobserved
household types estimated by EM. [`demo.ipynb`](demo.ipynb) walks through the
same steps with explanations.

To use your own data, map its columns:

```python
from dscdemand import PanelDataset

dataset = PanelDataset(
    df,
    household="hh_id",
    week="week",
    upstream="sanitizer_qty",
    purchase="bought_lotion",
    volume="lotion_oz",
    price="lotion_price",
    covariates=("event",),
)
```

## Data

[`data/synthetic_panel.csv`](data/synthetic_panel.csv) is randomly generated
(300 households x 60 weeks) and contains no real data.

## Commands

| Command | What it does |
|---|---|
| `make help` | List the commands |
| `make init` | Same as `make envs` |
| `make envs` | Create or update the environment, install the package, and register the **Python (dscdemand)** kernel |
| `make check` | Lint with ruff, then run the tests |
| `make test` | Run the tests |
| `make docs` | Build the API documentation into `docs/` (open `docs/index.html`) |
| `make serve` | Open the demo notebook in JupyterLab |

## Tests

`make test` runs the suite in [`dscdemand/tests/`](dscdemand/tests/); success
ends with `43 passed`. It checks the environment, data validation, stocks and
transitions, the Bellman fixed point, recovery of known parameters from
simulated data, a zero response to a zero shock, and that EM never lowers the
likelihood.

## Limitations

- Stock retention rates (`eta`, `rho`) and the discount factor (`beta`) are
  fixed, not estimated.
- States are discretized. Grids built from data shift the intercept and
  attenuate the inventory effect relative to the true model.
- Purchase volume is drawn after the buy decision, not chosen jointly.
- Price and covariates enter current utility only; the continuation value is
  solved at reference values.

## Repository Structure

```
dscdemand/
  data.py            PanelDataset, load_example
  states.py          exposure and inventory stocks, grids, transitions
  bellman.py         value-function iteration
  likelihood.py      NFXP log-likelihood
  em.py              EM for unobserved types
  counterfactual.py  shock response and multipliers
  models/            storable, complementary, storable_complementary
  tests/
data/                synthetic example panel
demo.ipynb           getting-started notebook
paper/               JOSS manuscript, proposal, reflections
environment.yml      conda environment
Makefile             project commands (make help)
pyproject.toml       package metadata, ruff and pytest settings
```

## Citation and License

A JOSS-style manuscript is in [`paper/paper.md`](paper/paper.md). Released
under the [MIT License](LICENSE).

## References

- Erdem, T., Imai, S., & Keane, M. P. (2003). Brand and quantity choice
  dynamics under price uncertainty. *Quantitative Marketing and Economics*.
- Hendel, I., & Nevo, A. (2006). Measuring the implications of sales and
  consumer inventory behavior. *Econometrica*.
- Hartmann, W. R., & Nair, H. S. (2010). Retail competition and the dynamics
  of demand for tied goods. *Marketing Science*.
- Rust, J. (1987). Optimal replacement of GMC bus engines. *Econometrica*.
- Arcidiacono, P., & Jones, J. B. (2003). Finite mixture distributions,
  sequential likelihood and the EM algorithm. *Econometrica*.
