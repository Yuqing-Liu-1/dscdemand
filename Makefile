# Project commands. Run `make help` to list them.
# On Windows, `make` is installed with the conda environment (see README).

ENV = demand_propagation
DOC_MODULES = demand_propagation demand_propagation.state demand_propagation.synthetic_panel demand_propagation.simulate

.PHONY: help init envs check test docs serve

help:
	@echo make init  - same as make envs
	@echo make envs  - create or update the conda environment and install the package
	@echo make check - lint with ruff and run the tests
	@echo make test  - run the tests only
	@echo make docs  - build the API documentation into docs/
	@echo make serve - open the demo notebook in JupyterLab

init: envs

envs:
	conda env update -n $(ENV) -f environment.yml --solver libmamba --prune
	conda run -n $(ENV) pip install -e .

check:
	ruff check .
	pytest

test:
	pytest

docs:
	pdoc -d numpy -o docs $(DOC_MODULES)

serve:
	jupyter lab demo.ipynb
