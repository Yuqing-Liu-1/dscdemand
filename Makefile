# Project commands. Run `make help` to list them.
# On Windows, `make` is installed with the conda environment (see README).

ENV = dscdemand
# One BLAS thread: the matrices are small, and many threads can exhaust memory.
export OPENBLAS_NUM_THREADS = 1
# Run tools inside the environment: directly if it is already active,
# otherwise through `conda run`, so the commands work without `conda activate`.
RUN = $(if $(filter $(ENV),$(CONDA_DEFAULT_ENV)),,conda run --no-capture-output -n $(ENV))
DOC_MODULES = dscdemand dscdemand.data dscdemand.states dscdemand.bellman \
	dscdemand.likelihood dscdemand.em dscdemand.counterfactual dscdemand.models \
	dscdemand.models.storable_complementary dscdemand.models.storable \
	dscdemand.models.complementary

.PHONY: help init envs check test docs serve figures

help:
	@echo make init  - same as make envs
	@echo make envs  - create the conda env, install the package, register the notebook kernel
	@echo make check - lint with ruff and run the tests
	@echo make test  - run the tests only
	@echo make docs  - build the API documentation into docs/
	@echo make serve - open the demo notebook in JupyterLab
	@echo make figures - rebuild the figures in paper/figures/ for paper.md

init: envs

envs:
	conda env update -n $(ENV) -f environment.yml --solver libmamba --prune
	conda run -n $(ENV) pip install -e .
	conda run -n $(ENV) python -m ipykernel install --user --name $(ENV) --display-name "Python (dscdemand)" --env OPENBLAS_NUM_THREADS 1

check:
	$(RUN) ruff check .
	$(RUN) pytest

test:
	$(RUN) pytest

docs:
	$(RUN) pdoc -d numpy -o docs $(DOC_MODULES)

serve:
	$(RUN) jupyter lab demo.ipynb

figures:
	$(RUN) python paper/make_figures.py
