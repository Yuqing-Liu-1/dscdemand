---
title: 'My Research Software Title'
authors:
  - name: Your Name
    affiliation: '1'
affiliations:
  - name: Your Institution
    index: 1
---

# Summary

Provide a concise summary of the software and its purpose for a broad, non-specialist audience. Explain what the software does and why it matters in a research context.

# Statement of need

Describe the problem that the software addresses and why it is important. Explain who the intended users are and how the software fits into the broader research landscape.

# State of the field

Briefly describe related software or methods in the field and explain how your work compares to or builds on them. If relevant, explain what gap your project addresses.

# Software design

Describe the main design choices, architecture, or workflow decisions that shape the software. Focus on meaningful trade-offs and why the chosen approach is appropriate for the research problem.

# Research impact

Summarize the current or expected impact of the software. This can include reproducible analyses, adoption by others, or evidence of significance in the research workflow. Keep this specific and realistic rather than promotional.

# Project evolution and lessons learned

Use this section to draft short reflections from each in-class activity. These notes can later be refined into the final report and should connect the course activities to your project.

## Modeling Intro

The `modeling_intro` activity used a small barycentric-triangle script to practice the arc from a working script to a reusable module, and to introduce Git hygiene (`git add -u` instead of `git add .`, commit messages that explain *why*, committing before letting Ruff auto-fix anything) and a basic Ruff workflow (`check` → investigate a warning → `--fix` → `format`, always followed by `git diff` review rather than blind trust). The most useful idea was the "A + P + D = 1" triangle for classifying a project's mix of Analytical, Physical, and Data-Driven components — I used this framing directly in the project proposal's Model Components table (state construction as Analytical, forward simulation as Physical/dynamical-system, CCP/MLE fitting as Data-Driven), so it is already shaping how the semester timeline is staged. Going forward I plan to keep the `git add -u` + reviewed-diff discipline for every milestone, and to revisit the triangle classification if the package's scope shifts.

## Analytical Modeling

Part 1 used SymPy to define a model symbolically rather than numerically and solve it directly (e.g. doubling time for exponential growth, peak/threshold times for a multi-dose caffeine-decay model). Part 2 introduced generating synthetic ("phantom") data from a known model with `generate_dataset.py`, inspecting how the `noise_fraction` parameter changes the observations, and a short code review of the module itself. The most useful takeaway so far is the design of `generate_dataset.py` — explicit input validation that raises a clear `ValueError`, NumPy-style docstrings with `Examples`/`Notes`, and keeping the hidden `truth` separate from the noisy observations — which I plan to follow when writing `demand_propagation`'s own analytical-layer functions, since the project has the same restricted-real-data constraint and will need synthetic inputs with a known ground truth to test against.

## Physical Modeling

Draft a short reflection on what you learned in the physical modeling activities, which methods or tools were most useful, how the work relates to your project, and whether you plan to adopt any of the ideas.

## Data-Driven Modeling

Draft a short reflection on what you learned in the data-driven modeling activities, which methods or tools were most useful, how the work relates to your project, and whether you plan to adopt any of the ideas.

# AI usage disclosure

Describe whether generative AI tools were used in the development of the software, documentation, or manuscript. If no AI tools were used, state that clearly. If they were used, describe the nature of the assistance and how the results were checked.

# Acknowledgements

List any contributors, funding sources, or support that should be acknowledged.

# References

Add references to related software, methods, and relevant literature.
