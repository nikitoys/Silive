from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

SUPPORTED_METRICS = (
    "survival_rate",
    "code_preservation_rate",
    "avg_final_population",
    "avg_final_stability",
    "avg_best_fitness",
)


@dataclass(frozen=True, slots=True)
class PhaseGrid:
    mutation_rates: list[float]
    shell_bonuses: list[float]
    values: list[list[float]]


def read_phase_map(csv_path: str | Path) -> list[dict]:
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        for key in (
            "mutation_rate",
            "shell_bonus",
            "survival_rate",
            "code_preservation_rate",
            "avg_final_population",
            "avg_final_stability",
            "avg_best_fitness",
        ):
            if key in row and row[key] != "":
                row[key] = float(row[key])
        for key in ("runs", "generations"):
            if key in row and row[key] != "":
                row[key] = int(float(row[key]))

    return rows


def make_phase_grid(rows: Sequence[dict], metric: str) -> PhaseGrid:
    if metric not in SUPPORTED_METRICS:
        raise ValueError(f"unsupported metric: {metric}")
    if not rows:
        raise ValueError("phase map is empty")

    mutation_rates = sorted({float(row["mutation_rate"]) for row in rows})
    shell_bonuses = sorted({float(row["shell_bonus"]) for row in rows})
    index = {
        (float(row["mutation_rate"]), float(row["shell_bonus"])): float(row[metric])
        for row in rows
    }

    values = [
        [index.get((mutation_rate, shell_bonus), float("nan")) for mutation_rate in mutation_rates]
        for shell_bonus in shell_bonuses
    ]

    return PhaseGrid(
        mutation_rates=mutation_rates,
        shell_bonuses=shell_bonuses,
        values=values,
    )


def plot_phase_map(
    csv_path: str | Path,
    output_path: str | Path,
    *,
    metric: str = "survival_rate",
    title: str | None = None,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError(
            "matplotlib is required for plotting. Install with: pip install -e .[plot]"
        ) from error

    rows = read_phase_map(csv_path)
    grid = make_phase_grid(rows, metric)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    image = ax.imshow(
        grid.values,
        origin="lower",
        aspect="auto",
        extent=(
            min(grid.mutation_rates),
            max(grid.mutation_rates),
            min(grid.shell_bonuses),
            max(grid.shell_bonuses),
        ),
    )
    ax.set_xlabel("mutation_rate")
    ax.set_ylabel("shell_bonus")
    ax.set_title(title or metric)
    fig.colorbar(image, ax=ax, label=metric)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def write_multiple_plots(
    csv_path: str | Path,
    output_dir: str | Path,
    metrics: Iterable[str] = ("survival_rate", "code_preservation_rate"),
) -> list[Path]:
    paths: list[Path] = []
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for metric in metrics:
        path = output / f"{metric}.png"
        plot_phase_map(csv_path, path, metric=metric)
        paths.append(path)

    return paths
