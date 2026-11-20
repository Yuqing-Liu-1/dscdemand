"""
Make the figures and table numbers for paper/paper.md.

Run from the repository root with ``make figures`` (about one minute). Writes
``paper/figures/workflow.png`` and ``paper/figures/results.png`` and prints the
numbers used in the manuscript's tables and text.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from dscdemand import StorableComplementaryModel, load_example, multipliers  # noqa: E402

OUT = Path(__file__).parent / "figures"
SETTINGS = {"eta": 0.6, "rho": 0.8, "unanticipated": ("event",)}

INK = "#1f2933"
MUTED = "#52606d"
FILLS = {"data": "#e3f2fd", "engine": "#f1f5f9", "fit": "#fff4e5", "out": "#e8f5e9"}
EDGES = {"data": "#1e6fb8", "engine": "#52606d", "fit": "#c26a00", "out": "#2e7d32"}


def _box(ax, x, y, w, h, title, body, kind):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            fc=FILLS[kind],
            ec=EDGES[kind],
            lw=1.3,
        )
    )
    ax.text(
        x + w / 2,
        y + h - 0.035,
        title,
        ha="center",
        va="top",
        fontsize=9.5,
        weight="bold",
        color=INK,
        family="monospace",
    )
    ax.text(
        x + w / 2,
        y + h - 0.095,
        body,
        ha="center",
        va="top",
        fontsize=8,
        color=MUTED,
        linespacing=1.35,
    )


def _arrow(ax, start, end, text=None, rad=0.0, text_xy=None):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=11,
            lw=1.1,
            color=MUTED,
            connectionstyle=f"arc3,rad={rad}",
        )
    )
    if text:
        tx, ty = text_xy or ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.025)
        ax.text(
            tx,
            ty,
            text,
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=MUTED,
            style="italic",
        )


def workflow_figure(path: Path) -> None:
    """Package organization: data, shared engine, fitted model, and outputs."""
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set(xlim=(-0.01, 1.01), ylim=(0.08, 1))
    ax.axis("off")

    # Column headers
    for x, label in [
        (0.10, "1. Data"),
        (0.44, "2. Shared engine"),
        (0.86, "3. Results"),
    ]:
        ax.text(
            x,
            0.98,
            label,
            ha="center",
            va="top",
            fontsize=10.5,
            weight="bold",
            color=INK,
        )

    _box(
        ax,
        0.01,
        0.55,
        0.18,
        0.30,
        "PanelDataset",
        "household-week panel\nupstream purchases S\n"
        "downstream purchase d,\nvolume Q, price,\ncovariates",
        "data",
    )
    _box(
        ax,
        0.01,
        0.12,
        0.18,
        0.27,
        "simulate()",
        "synthetic panel from\nknown parameters\n(tests, recovery)",
        "data",
    )

    _box(
        ax,
        0.25,
        0.55,
        0.18,
        0.30,
        "states",
        "stocks\nK' = ηK + S\nξ' = ρξ + dQ\nzero-mass grids,\nMarkov transitions",
        "engine",
    )
    _box(
        ax,
        0.47,
        0.55,
        0.18,
        0.30,
        "bellman",
        "value function\niteration on the\n(K, ξ) grid;\ncontinuation\nvalues EV₀, EV₁",
        "engine",
    )
    _box(
        ax,
        0.25,
        0.12,
        0.18,
        0.27,
        "likelihood",
        "dynamic logit\nP(d=1 | K, ξ, price)\nNFXP maximum\nlikelihood",
        "engine",
    )
    _box(
        ax,
        0.47,
        0.12,
        0.18,
        0.27,
        "em",
        "finite mixture of\nhousehold types;\nposterior type\nprobabilities",
        "engine",
    )

    _box(
        ax,
        0.73,
        0.55,
        0.26,
        0.30,
        "fitted model",
        "params_: utility parameters\npredict_proba(): fit by week\n"
        "policy(): P(buy) on the (K, ξ) grid",
        "fit",
    )
    _box(
        ax,
        0.73,
        0.12,
        0.26,
        0.27,
        "counterfactual",
        "shock_response()\nweek-by-week response\nmultipliers()\ngross, net, offset",
        "out",
    )

    _arrow(ax, (0.19, 0.70), (0.25, 0.70))
    _arrow(ax, (0.43, 0.70), (0.47, 0.70))
    _arrow(ax, (0.56, 0.55), (0.40, 0.39), "inner loop", rad=0.0, text_xy=(0.50, 0.465))
    _arrow(ax, (0.43, 0.255), (0.47, 0.255))
    _arrow(ax, (0.65, 0.30), (0.73, 0.62), "θ̂, π̂", rad=0.0, text_xy=(0.675, 0.47))
    _arrow(ax, (0.86, 0.55), (0.86, 0.39))
    _arrow(ax, (0.10, 0.39), (0.10, 0.55), "same schema", text_xy=(0.155, 0.455))
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def results_figure(model, path: Path) -> dict:
    """Model fit, purchase policy, and shock responses on the example panel."""
    fit = model.predict_proba().groupby("week")[["purchase", "p_buy"]].mean()
    corr = float(np.corrcoef(fit["purchase"], fit["p_buy"])[0, 1])
    policy = model.policy()
    shocks = {"typical shock (2 units)": 2.0, "event-sized shock (4 units)": 4.0}
    responses = {k: model.shock_response(shock=s, weeks=26) for k, s in shocks.items()}

    fig, axes = plt.subplots(
        1, 3, figsize=(13, 3.6), gridspec_kw={"width_ratios": [1.25, 1, 1.1]}
    )
    ax = axes[0]
    ax.axvspan(39.5, 42.5, color="0.9", label="event weeks")
    ax.plot(fit.index, fit["purchase"], color="0.55", lw=1.2, label="observed")
    ax.plot(fit.index, fit["p_buy"], color="#c26a00", lw=1.8, label="model")
    ax.set(
        xlabel="Week",
        ylabel="Purchase rate",
        title=f"(a) Weekly fit (corr = {corr:.2f})",
    )
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    im = ax.imshow(policy.values, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(
        range(policy.shape[1]),
        [f"{v:g}" for v in policy.columns],
        fontsize=7,
        rotation=45,
    )
    ax.set_yticks(range(policy.shape[0]), [f"{v:g}" for v in policy.index], fontsize=7)
    ax.set(
        xlabel="Inventory ξ", ylabel="Exposure K", title="(b) Purchase policy P(buy)"
    )
    fig.colorbar(im, ax=ax, fraction=0.05)

    ax = axes[2]
    ax.axhline(0, color="0.6", lw=0.8)
    for (name, r), color in zip(responses.items(), ["#1e6fb8", "#2e7d32"], strict=True):
        ax.plot(
            r["week"],
            r["response"],
            marker="o",
            ms=2.5,
            lw=1.4,
            color=color,
            label=name,
        )
    ax.set(
        xlabel="Weeks after the shock",
        ylabel="Change in P(buy)",
        title="(c) Response to one extra upstream purchase",
    )
    ax.legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {
        "corr": corr,
        "rmse": float(np.sqrt(((fit["purchase"] - fit["p_buy"]) ** 2).mean())),
        "multipliers": {k: multipliers(r["response"]) for k, r in responses.items()},
    }


def heterogeneity_table() -> None:
    """One-type vs two-type fit on a panel simulated with two household types."""
    two_types = [
        dict(a=1.5, gamma1=0.8, gamma2=0.2, lam=-0.5, alpha=-0.4, event=1.0),
        dict(a=-1.0, gamma1=0.8, gamma2=0.2, lam=-0.5, alpha=-0.4, event=1.0),
    ]
    sim = StorableComplementaryModel(**SETTINGS)
    panel, truth = sim.simulate(
        params=two_types, pi=[0.4, 0.6], n_households=300, n_weeks=60, seed=1
    )
    one = StorableComplementaryModel(**SETTINGS).fit(panel)
    em = StorableComplementaryModel(n_types=2, **SETTINGS).fit(panel)
    n = panel.n_rows
    print("\nTable 2 (two-type panel, 300 households x 60 weeks):")
    for label, m in [("one type", one), ("two types (EM)", em)]:
        k = m.layout_.size + m.layout_.n_types - 1
        print(
            f"  {label:15s} gamma1={m.params_.loc['gamma1'].iloc[0]:.2f} "
            f"lam={[round(v, 2) for v in m.params_.loc['lam']]} "
            f"a={[round(v, 2) for v in m.params_.loc['a']]} "
            f"pi={[round(p, 2) for p in m.pi_]} "
            f"loglik={m.loglik_:.1f} BIC={-2 * m.loglik_ + k * np.log(n):.1f}"
        )
    share = (em.responsibilities_.argmax(axis=1) == truth["types"]).mean()
    print(f"  households classified correctly: {share:.1%}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    workflow_figure(OUT / "workflow.png")
    model = StorableComplementaryModel(**SETTINGS).fit(load_example())
    print("Table / text: estimates on the example panel")
    print(model.params_.round(3).to_string())
    stats = results_figure(model, OUT / "results.png")
    print(f"weekly fit: corr={stats['corr']:.3f} rmse={stats['rmse']:.4f}")
    for name, m in stats["multipliers"].items():
        print(f"  {name}: {m}")
    heterogeneity_table()
    print(f"\nWrote {OUT / 'workflow.png'} and {OUT / 'results.png'}")


if __name__ == "__main__":
    main()
