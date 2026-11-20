# JOSS Software Review Card

## Project Information

- Reviewer: Yuqing Liu
- Date: 2026-11-18
- JOSS paper title: *Choice-Learn: Large-scale choice modeling for operational contexts through the lens of machine learning* (Auriau, Aouad, Désir, Malherbe; JOSS 9(101), 6899, 2024)
- Paper URL or DOI: https://doi.org/10.21105/joss.06899
- Repository URL: https://github.com/artefactory/choice-learn
- Release, tag, or commit reviewed: commit `9af332f` on `main` (v1.3.3 + 14 commits, 2026-11-16)

## Paper Snapshot

Choice-Learn is a Python package for estimating discrete choice models, which predict which alternative a person picks from a set (for example, a transport mode or a product), and for using those models in assortment and pricing decisions. It is aimed at both academic researchers and industry practitioners who work with large choice datasets. Its main contribution is a single TensorFlow-based library that combines memory-efficient data handling (`FeaturesStorage`), traditional logit models, neural-network choice models, custom utility specifications, and downstream optimization tools, which the paper shows are not all available together in Biogeme, PyLogit, or Torch-Choice.

## First-Use Evidence

Choose one bounded first-use path: installation, documented example, tutorial, test, or demonstration workflow.

- README or documentation path followed: README → *Installation* (`make install`, which runs `bin/install_with_conda.sh`) → *Getting Started*, first tutorial: `notebooks/introduction/1_introductive_example.ipynb`.
- Command(s), steps, or materials used (Windows 11, Anaconda, conda 23.7):
  1. `make install` could not be run as written. Tested from both PowerShell and Git Bash: `make` is not installed on Windows. Running the same target with a `make.exe` borrowed from another conda environment still failed. From PowerShell, `bash` resolved to the WSL launcher, which errored. From Git Bash, the script started (and asks an interactive y/n), but `conda` is not on Git Bash's PATH, so its first step (`conda create`) would fail. The venv alternative (`USE_CONDA=false`) uses `python3` and `venv/bin/activate`, which are Linux/macOS conventions.
  2. Ran the script's steps by hand: `conda create -n choice-learn python=3.10 -y --override-channels -c defaults`. The `--override-channels -c defaults` flags were my addition: without them, conda ran out of memory loading the conda-forge index.
  3. `pip install -r requirements-developer.txt`. Skipped the script's Jupyter-kernel, notebook, and pre-commit steps.
  4. Executed notebook 1 top to bottom (`jupyter nbconvert --to notebook --execute`, output written to a separate copy).
- Expected result: the notebook runs, fits a Multinomial Logit on a 3-customer, 3-product toy dataset, and reproduces the outputs saved in the notebook. Saved outputs: price coefficient −0.377, promotion coefficient 40.98, average negative log-likelihood 1.001363e-05, and a probability of about 0.99999 for each chosen item.
- Observed result: the notebook ran without errors in about 27 seconds. The negative log-likelihood (1.001363e-05) and the predicted probabilities matched the saved outputs. The coefficients did not match: price −51.33 instead of −0.377, promotion 3947.79 instead of 40.98, with similarly large intercepts.
- Outcome:
  - [ ] Completed as documented
  - [x] Completed with minor inference
  - [ ] Blocked or unclear

If blocked or unclear, describe the specific step and what information would have helped:

Before the working path, two documented routes were blocked on Windows. (1) `pip install choice-learn` in a virtual environment built from base Anaconda Python installed successfully, but `import tensorflow` failed with "DLL initialization failed" (TensorFlow 2.21 and 2.19.1). Base Anaconda ships an older C++ runtime (`msvcp140.dll` 14.27); the fresh conda environment includes 14.44, and TensorFlow loaded there. Confirmed with a controlled test: in a rebuilt pip venv with the same failure, loading Windows' newer `msvcp140.dll` (14.50) before `import tensorflow` made the import succeed. (2) `make install` needs `make`, a bash shell, and conda available inside that shell. On Windows it works only after several setup steps the README never mentions (installing make, using Git Bash, initializing conda for bash). The README mentions only an Apple M1/M2 issue and never mentions Windows. What would have helped: a "tested platforms / known issues" note with the plain commands Windows users should run instead of `make install` (for example, "on Windows, create a fresh conda environment and run these commands").

## SPRRL Observations

Mark one rating for each category and provide one concise piece of evidence.

| Category | Strong | Partial | Gap observed | Evidence |
| --- | --- | --- | --- | --- |
| Safe | [ ] | [x] | [ ] | MIT license, `bandit` security scanning, and every bundled dataset cites its source; but neither the README nor the paper states modeling assumptions or appropriate-use limits (the README's "no limitation of usage" refers only to the license). |
| Portable | [ ] | [ ] | [x] | `make install` failed on Windows from both PowerShell and Git Bash (no `make`; bash-only script; conda not on Git Bash's PATH); CI runs only on `ubuntu-latest`; `requirements-complete.txt`, described as a "fully predetermined and working environment," pins `tensorflow==2.11.0`, while the package requires `>=2.18`. |
| Reproducible | [ ] | [x] | [ ] | Notebook 1 ran in about 27 seconds and matched the saved loss and probabilities exactly; the coefficients differed by about 100x with no explanation, and the README usage example shows no expected output. |
| Robust | [x] | [ ] | [ ] | 41 test files (252 test functions) under `tests/`; CI runs pytest with coverage on Python 3.10–3.13; pre-commit with ruff. (Inspected, not run.) |
| Literate | [x] | [ ] | [ ] | The JOSS paper compares features with Biogeme, PyLogit, and Torch-Choice; one README table links every model to an example notebook, a Colab button, its source paper, and API docs. Minor issues: the contact link is not a `mailto:`, references [17] and [18] share one wrong URL, and two models have empty doc links. |

## Review Reflection

### Two practices worth learning from

1. **One table that links each feature to its example, paper, and docs.** In the README model table, every model row points to a runnable notebook, a Colab button, the original paper, and its API reference, so a user can go from "which model?" to "running example" in one click.
2. **Tutorial notebooks with saved outputs.** Because notebook 1 keeps its outputs, I could compare my run against the authors' results without guessing what success looks like.

### One improvement opportunity

Describe an observed issue, its likely impact on a prospective user or collaborator, and one concrete improvement:

**Issue:** the README's first installation command, `make install`, does not work on Windows as written. Windows has no `make`; the target calls a bash script; and that script expects `conda` (or `python3` and `venv/bin/activate`) to be available in a Unix-style shell. I confirmed this from both PowerShell and Git Bash. The README never mentions Windows (its only platform note is for Apple M1/M2), and CI tests only on Ubuntu. **Impact:** a Windows user, which is common among applied researchers, fails at the very first step and has to reverse-engineer the script to find the real commands, which some users would not attempt. The dependencies are also spread across `requirements.txt`, `requirements-developer.txt`, `requirements-complete.txt`, `pyproject.toml`, and `poetry.lock`, and these disagree (for example, TensorFlow 2.11 in one versus `>=2.18` in others). What finally worked was simply a fresh conda environment, which also fixed the TensorFlow DLL error by bringing a newer C++ runtime. **Concrete improvement:** provide one conda `environment.yml` as the single source of truth for the environment, listing `make` itself, so that one command (`conda env create -f environment.yml`) gives every platform the same working environment and the Makefile then works on Windows too; also add a short "Windows" note to the README and, ideally, a Windows runner to the CI matrix.

A secondary observation: in notebook 1, the coefficients differed from the saved outputs by about 100x while the loss and probabilities matched exactly. This is expected for a tiny, perfectly predicted toy dataset, but the notebook does not say which outputs should match.

## Apply This to Your Project

Name one practice you will apply, adapt, or intentionally avoid in your own release candidate.

- Practice: **apply and strengthen** a single `environment.yml` paired with the Makefile, and **intentionally avoid** an install that depends on tools the user may not have. My project already has one `environment.yml` that lists Python, `make`, and every dependency, so `conda env create -f environment.yml` installs `make` inside the environment on Windows too, and the Makefile works everywhere after that one step. The Makefile recipes call conda, pip, pytest, and ruff directly, with no bash scripts and no interactive prompts. The remaining gap: `environment.yml` does not pin versions (`numpy`, `pandas` are unpinned), so a future install could differ from the environment that produced my expected output, which is the same kind of drift as Choice-Learn's stale requirements file.
- Concrete next action: before the release candidate, (1) pin the key versions in `environment.yml` to the ones I tested (`python=3.12`, `numpy=2.5`, `pandas=3.0`); (2) do a clean test on Windows: fresh clone → `conda env create -f environment.yml` → `pip install -e .` → `make check` (expect `58 passed`) → `make serve` and run the demo; (3) note the tested platform in the README.
- SPRRL dimension(s) strengthened: Portable, Reproducible.

## Day 23 Presentation Prompt

Prepare a two-minute presentation:

1. **Project and problem:** Choice-Learn (JOSS 2024) helps researchers model choices: which option a person picks, like train versus car. My project also models household purchase decisions.
2. **Strength:** one README table links every model to a ready-to-run notebook, its paper, and its docs; the notebooks keep their outputs, so I could compare my results with the authors'.
3. **Improvement opportunity:** setup on Windows. `make install` is the README's one-command install, but Windows has no `make` and the script behind it is written for macOS/Linux; dependencies are spread across several requirements files that disagree. What finally worked was a fresh conda environment.
4. **Transfer:** that is what an environment file gives you. My project has one `environment.yml` that includes `make` itself, so the Makefile works on Windows after one setup command. Before the release candidate, I'll pin the key versions in it and test a fresh setup on Windows.
