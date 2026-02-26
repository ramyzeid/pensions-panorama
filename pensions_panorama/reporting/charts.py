"""Chart generation using matplotlib.

Standard charts per country
---------------------------
1. gross_vs_net_rr    – Gross vs net replacement rates by earnings multiple
2. gross_vs_net_pl    – Gross vs net pension levels (% AW)
3. component_breakdown – Stacked bar of gross pension components by earnings multiple
4. pension_wealth      – Gross vs net pension wealth (× AW)

All charts are saved as PNG at 150 dpi (configurable).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from pensions_panorama.model.pension_engine import PensionResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Styling defaults
# ---------------------------------------------------------------------------
_STYLE: dict = {
    "figure.figsize": (9, 5),
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
}

_COLORS = {
    "gross": "#1f77b4",
    "net": "#ff7f0e",
    "aw_line": "#aaaaaa",
}

_COMPONENT_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
]


def _pct(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))


def _apply_style() -> None:
    for k, v in _STYLE.items():
        try:
            plt.rcParams[k] = v
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Individual chart functions
# ---------------------------------------------------------------------------

def plot_replacement_rates(
    results: list[PensionResult],
    country_name: str,
    out_dir: Path,
    filename: str = "replacement_rates.png",
    dpi: int = 150,
) -> Path:
    """Plot gross and net replacement rates by earnings multiple."""
    _apply_style()
    multiples = [r.earnings_multiple for r in results]
    gross_rr = [r.gross_replacement_rate for r in results]
    net_rr = [r.net_replacement_rate for r in results]

    fig, ax = plt.subplots()
    ax.plot(multiples, gross_rr, marker="o", label="Gross RR", color=_COLORS["gross"])
    ax.plot(multiples, net_rr, marker="s", linestyle="--", label="Net RR", color=_COLORS["net"])
    ax.axhline(1.0, color=_COLORS["aw_line"], linestyle=":", linewidth=1, label="100%")
    ax.set_xlabel("Individual earnings (× average wage)")
    ax.set_ylabel("Replacement rate")
    ax.set_title(f"{country_name} – Gross and Net Replacement Rates")
    _pct(ax)
    ax.legend(frameon=False)
    ax.set_xticks(multiples)
    fig.tight_layout()

    out_path = out_dir / filename
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def plot_pension_levels(
    results: list[PensionResult],
    country_name: str,
    out_dir: Path,
    filename: str = "pension_levels.png",
    dpi: int = 150,
) -> Path:
    """Plot gross and net pension levels (as % of average wage) by earnings multiple."""
    _apply_style()
    multiples = [r.earnings_multiple for r in results]
    gross_pl = [r.gross_pension_level for r in results]
    net_pl = [r.net_pension_level for r in results]

    fig, ax = plt.subplots()
    ax.plot(multiples, gross_pl, marker="o", label="Gross pension level", color=_COLORS["gross"])
    ax.plot(multiples, net_pl, marker="s", linestyle="--", label="Net pension level",
            color=_COLORS["net"])
    ax.axhline(1.0, color=_COLORS["aw_line"], linestyle=":", linewidth=1, label="100% AW")
    ax.set_xlabel("Individual earnings (× average wage)")
    ax.set_ylabel("Pension level (% average wage)")
    ax.set_title(f"{country_name} – Gross and Net Pension Levels")
    _pct(ax)
    ax.legend(frameon=False)
    ax.set_xticks(multiples)
    fig.tight_layout()

    out_path = out_dir / filename
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def plot_component_breakdown(
    results: list[PensionResult],
    country_name: str,
    out_dir: Path,
    filename: str = "component_breakdown.png",
    dpi: int = 150,
) -> Path:
    """Stacked bar chart of gross pension components by earnings multiple."""
    _apply_style()
    if not results or not results[0].component_breakdown:
        logger.warning("No component breakdown data to plot.")
        return out_dir / filename

    multiples = [r.earnings_multiple for r in results]
    scheme_ids = list(results[0].component_breakdown.keys())
    data: dict[str, list[float]] = {sid: [] for sid in scheme_ids}
    for r in results:
        for sid in scheme_ids:
            data[sid].append(r.component_breakdown.get(sid, 0.0))

    df = pd.DataFrame(data, index=multiples)
    # Normalise to % of average wage
    avg_w = results[0].average_wage
    if avg_w > 0:
        df = df / avg_w

    fig, ax = plt.subplots()
    bottom = [0.0] * len(multiples)
    x = range(len(multiples))
    for i, sid in enumerate(scheme_ids):
        vals = df[sid].tolist()
        color = _COMPONENT_PALETTE[i % len(_COMPONENT_PALETTE)]
        ax.bar(x, vals, bottom=bottom, label=sid, color=color)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{m:.2f}×AW" for m in multiples])
    ax.set_ylabel("Gross pension level (% AW)")
    ax.set_title(f"{country_name} – Gross Pension by Component")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()

    out_path = out_dir / filename
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


def plot_pension_wealth(
    results: list[PensionResult],
    country_name: str,
    out_dir: Path,
    filename: str = "pension_wealth.png",
    dpi: int = 150,
) -> Path:
    """Plot gross and net pension wealth (× average wage) by earnings multiple."""
    _apply_style()
    multiples = [r.earnings_multiple for r in results]
    gross_pw = [r.gross_pension_wealth for r in results]
    net_pw = [r.net_pension_wealth for r in results]

    fig, ax = plt.subplots()
    ax.plot(multiples, gross_pw, marker="o", label="Gross pension wealth", color=_COLORS["gross"])
    ax.plot(multiples, net_pw, marker="s", linestyle="--", label="Net pension wealth",
            color=_COLORS["net"])
    ax.set_xlabel("Individual earnings (× average wage)")
    ax.set_ylabel("Pension wealth (× average wage)")
    ax.set_title(f"{country_name} – Pension Wealth")
    ax.legend(frameon=False)
    ax.set_xticks(multiples)
    fig.tight_layout()

    out_path = out_dir / filename
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Cross-country comparative chart
# ---------------------------------------------------------------------------

def plot_cross_country_comparison(
    summary_df: pd.DataFrame,
    metric: str,
    metric_label: str,
    earnings_multiple: float,
    out_dir: Path,
    filename: str | None = None,
    dpi: int = 150,
) -> Path:
    """Horizontal bar chart comparing one metric across countries.

    Parameters
    ----------
    summary_df:
        DataFrame with columns ``iso3``, ``country_name``, and the ``metric`` column.
    metric:
        Column name in summary_df to plot.
    metric_label:
        Human-readable axis label.
    earnings_multiple:
        The earnings multiple this represents (for the title).
    """
    _apply_style()
    df = summary_df.dropna(subset=[metric]).sort_values(metric)
    labels = df["country_name"].tolist() if "country_name" in df.columns else df["iso3"].tolist()
    values = df[metric].tolist()

    fig_h = max(4, len(labels) * 0.45)
    fig, ax = plt.subplots(figsize=(9, fig_h))
    ax.barh(labels, values, color=_COLORS["gross"])
    ax.set_xlabel(metric_label)
    ax.set_title(
        f"Cross-country: {metric_label} at {earnings_multiple:.2f}×AW"
    )
    if "rate" in metric or "level" in metric or "replacement" in metric:
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
    ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()

    if filename is None:
        filename = f"cross_country_{metric}_{earnings_multiple:.2f}xaw.png"
    out_path = out_dir / filename
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Convenience: generate all standard charts for one country
# ---------------------------------------------------------------------------

def generate_all_charts(
    results: list[PensionResult],
    country_name: str,
    out_dir: Path,
    dpi: int = 150,
) -> dict[str, Path]:
    """Generate all four standard charts and return a dict of name → path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    return {
        "replacement_rates": plot_replacement_rates(results, country_name, out_dir, dpi=dpi),
        "pension_levels": plot_pension_levels(results, country_name, out_dir, dpi=dpi),
        "component_breakdown": plot_component_breakdown(results, country_name, out_dir, dpi=dpi),
        "pension_wealth": plot_pension_wealth(results, country_name, out_dir, dpi=dpi),
    }
