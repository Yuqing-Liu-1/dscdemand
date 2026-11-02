# Reflections

Short reflections from the in-class activities, connecting each one to this
project. They will later be refined into the final report (`paper.md`).

## Modeling Intro

The `modeling_intro` activity used a small barycentric-triangle script to practice the arc from a working script to a reusable module, and to introduce Git hygiene (`git add -u` instead of `git add .`, commit messages that explain *why*, committing before letting Ruff auto-fix anything) and a basic Ruff workflow (`check` → investigate a warning → `--fix` → `format`, always followed by `git diff` review rather than blind trust). The most useful idea was the "A + P + D = 1" triangle for classifying a project's mix of Analytical, Physical, and Data-Driven components — I used this framing directly in the project proposal's Model Components table (state construction as Analytical, forward simulation as Physical/dynamical-system, CCP/MLE fitting as Data-Driven), so it is already shaping how the semester timeline is staged. Going forward I plan to keep the `git add -u` + reviewed-diff discipline for every milestone, and to revisit the triangle classification if the package's scope shifts.

## Analytical Modeling

Part 1 used SymPy to define a model symbolically rather than numerically and solve it directly (e.g. doubling time for exponential growth, peak/threshold times for a multi-dose caffeine-decay model). Part 2 introduced generating synthetic ("phantom") data from a known model with `generate_dataset.py`, inspecting how the `noise_fraction` parameter changes the observations, and a short code review of the module itself. The most useful takeaway so far is the design of `generate_dataset.py` — explicit input validation that raises a clear `ValueError`, NumPy-style docstrings with `Examples`/`Notes`, and keeping the hidden `truth` separate from the noisy observations — which I plan to follow when writing `demand_propagation`'s own analytical-layer functions, since the project has the same restricted-real-data constraint and will need synthetic inputs with a known ground truth to test against.

## HPCC, Git, and the Terminal

These sessions connected MSU's HPCC with GitHub and moved me from the HPCC's graphical (GUI) apps, which were all I used before, to working in the terminal. This changed my research workflow and saves a large amount of time. I learned to submit jobs with `sbatch`: my data processing takes about 36 hours, and without a batch job I would have had to keep my own computer running and watch it the whole time. I also learned to `git pull` and `git push` on the HPCC, so my code and data stay consistent between my laptop and the remote jobs. Finally, I learned to create conda environments with the faster `libmamba` solver; I now use it in this project (`conda env create -f environment.yml --solver libmamba`), where it cut environment creation on my machine from about 24 minutes with the classic solver to under 2 minutes.
