# dscdemand

**Dynamic Storable–Complementary demand models in Python.**

`dscdemand` estimates forward-looking models of household demand from
household-week panel data. It targets goods that consumers **store** and
goods whose need is created by using a **complementary** product, such as hand
lotion after heavy hand-sanitizer use. Models are fit by nested fixed point
maximum likelihood, allow unobserved household types (EM), and produce the
week-by-week purchase response to a shock.

## Models

| Model | File | Idea | Literature | Status |
|---|---|---|---|---|
| Storable goods | [`storable.py`](dscdemand/models/storable.py) | Stockpiling and consumption from inventory | Erdem, Imai & Keane (2003); Hendel & Nevo (2006) | Planned |
| Complementary goods | [`complementary.py`](dscdemand/models/complementary.py) | Buying one good raises the value of another (tied goods, add-ons) | Hartmann & Nair (2010); Liu, Derdenger & Sun (2018) | Planned |
| Storable + complementary | [`storable_complementary.py`](dscdemand/models/storable_complementary.py) | Upstream purchases build exposure that raises demand for a storable downstream good | This package | **Available** |

All models share one interface (`fit`, `simulate`, `shock_response`) and the
same engine: state construction, Bellman solver, likelihood, and EM.

## Installation

From the repository root (macOS/Linux):

```
make init
conda activate dscdemand
make check
```

**Windows:** `make` comes with the environment, so the first time run:

```
conda env create -f environment.yml --solver libmamba
conda activate dscdemand
pip install -e .
make check
```

## Quick Start

```python
from dscdemand import StorableComplementaryModel, load_example, multipliers

dataset = load_example()
model = StorableComplementaryModel(eta=0.6, rho=0.8, unanticipated=("event",))
model.fit(dataset)

model.params_  # estimated utility parameters
response = model.shock_response(weeks=26)
multipliers(
    response["response"]
)  # {'gross': 0.090, 'net': 0.075, 'offset_ratio': 0.173}
```

One extra upstream purchase raises the probability of buying for a few weeks;
households that bought early then hold inventory and buy less, offsetting
about 17% of the extra demand. [`demo.ipynb`](demo.ipynb) walks through the
same steps (`make serve`).

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
| `make init` | Create or update the environment and install the package |
| `make check` | Lint with ruff, then run the tests |
| `make test` | Run the tests |
| `make docs` | Build the API documentation into `docs/` (open `docs/index.html`) |
| `make serve` | Open the demo notebook in JupyterLab |

## Tests

`make test` runs the suite in [`dscdemand/tests/`](dscdemand/tests/); success
ends with `41 passed`. It checks the environment, data validation, stocks and
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
