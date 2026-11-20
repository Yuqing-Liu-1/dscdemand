# Project commands. Run `make help` to list them.
# On Windows, `make` is installed with the conda environment (see README).

ENV = dscdemand
# One BLAS thread: the matrices are small, and many threads can exhaust memory.
export OPENBLAS_NUM_THREADS = 1
DOC_MODULES = dscdemand dscdemand.data dscdemand.states dscdemand.bellman \
	dscdemand.likelihood dscdemand.em dscdemand.counterfactual dscdemand.models \
	dscdemand.models.storable_complementary dscdemand.models.storable \
	dscdemand.models.complementary

.PHONY: help init envs check test docs serve

help:
	@echo make init  - same as make envs
	@echo make envs  - create the conda env, install the package, register the notebook kernel
	@echo make check - lint with ruff and run the tests
	@echo make test  - run the tests only
	@echo make docs  - build the API documentation into docs/
	@echo make serve - open the demo notebook in JupyterLab

init: envs

envs:
	conda env update -n $(ENV) -f environment.yml --solver libmamba --prune
	conda run -n $(ENV) pip install -e .
	conda run -n $(ENV) python -m ipykernel install --user --name $(ENV) --display-name "Python (dscdemand)" --env OPENBLAS_NUM_THREADS 1

check:
	ruff check .
	pytest

test:
	pytest

docs:
	pdoc -d numpy -o docs $(DOC_MODULES)

serve:
	jupyter lab demo.ipynb
