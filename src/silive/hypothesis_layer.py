from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class HypothesisReportInputs:
    evolution_dir: Path
    output: Path
    rdkit_search_csv: Path
    reaction_search_csv: Path
    final_population_csv: Path
    best_candidate_txt: Path
    summary_json: Path


def default_hypothesis_inputs(
    evolution_dir: str | Path,
    output: str | Path,
    *,
    rdkit_search_csv: str | Path | None = None,
    reaction_search_csv: str | Path | None = None,
) -> HypothesisReportInputs:
    evolution_path = Path(evolution_dir)
    base_dir = evolution_path.parent
    return HypothesisReportInputs(
        evolution_dir=evolution_path,
        output=Path(output),
        rdkit_search_csv=Path(rdkit_search_csv) if rdkit_search_csv is not None else base_dir / "rdkit_search.csv",
        reaction_search_csv=Path(reaction_search_csv) if reaction_search_csv is not None else base_dir / "reaction_search.csv",
        final_population_csv=evolution_path / "final_population.csv",
        best_candidate_txt=evolution_path / "best_candidate.txt",
        summary_json=evolution_path / "summary.json",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _split_values(value: str) -> list[str]:
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def _count_field(rows: Iterable[dict[str, str]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(_split_values(row.get(field, "")))
    return counts


def _top_lines(counts: Counter[str], *, limit: int = 8) -> list[str]:
    if not counts:
        return ["- none observed"]
    return [f"- {name}: {count}" for name, count in counts.most_common(limit)]


def _source_link(path: Path, label: str) -> str:
    return f"- `{label}`: `{path}`" + ("" if path.exists() else " (missing)")


def _top_rows(rows: list[dict[str, str]], score_field: str, *, limit: int = 5) -> list[dict[str, str]]:
    def key(row: dict[str, str]) -> float:
        try:
            return float(row.get(score_field, "0") or 0)
        except ValueError:
            return 0.0

    return sorted(rows, key=key, reverse=True)[:limit]


def _candidate_lines(rows: list[dict[str, str]], *, limit: int = 5) -> list[str]:
    visible = _top_rows(rows, "score", limit=limit)
    if not visible:
        visible = _top_rows(rows, "candidate_score", limit=limit)
    if not visible:
        return ["- none observed"]
    lines: list[str] = []
    for row in visible:
        name = row.get("name") or row.get("candidate_id") or "candidate"
        molecule = row.get("molecule", "unknown")
        score = row.get("score") or row.get("candidate_score") or "0.000"
        viability = row.get("viability", "unknown")
        source = row.get("rank") or row.get("generation") or "?"
        lines.append(f"- {name}: score={score}; viability={viability}; molecule=`{molecule}`; source_row={source}")
    return lines


def _reaction_lines(rows: list[dict[str, str]], *, limit: int = 5) -> list[str]:
    visible = _top_rows(rows, "delta_score", limit=limit)
    if not visible:
        return ["- none observed"]
    lines: list[str] = []
    for row in visible:
        reaction = row.get("reaction_id", "reaction")
        name = row.get("name", "candidate")
        delta = row.get("delta_score", "0.000")
        new_functions = row.get("new_functions", "") or "none"
        lines.append(f"- {reaction} on {name}: delta={delta}; new_functions={new_functions}; source_row={row.get('rank', '?')}")
    return lines


def _material_classes(topology_counts: Counter[str], gene_counts: Counter[str]) -> list[str]:
    suggestions: list[str] = []
    if topology_counts.get("siloxane_rich") or gene_counts.get("GENE_SI_TEMPLATE"):
        suggestions.append("- Siloxane-rich Si/O scaffolds")
    if topology_counts.get("metal_center") or gene_counts.get("GENE_FE_CATALYSIS") or gene_counts.get("GENE_NI_CATALYSIS"):
        suggestions.append("- Fe/Ni oxide catalytic centers")
    if topology_counts.get("phosphate_bridge") or gene_counts.get("GENE_P_REPAIR"):
        suggestions.append("- Phosphate-bridged repair motifs")
    if topology_counts.get("fragmented") or topology_counts.get("labile_bridge_candidate"):
        suggestions.append("- Labile fragmented mineral assemblies")
    return suggestions or ["- none inferred"]


def _environment_variables(missing_counts: Counter[str], reaction_risks: Counter[str]) -> list[str]:
    variables = ["- hydration / drying cycle", "- pH and phosphate availability", "- redox state and Fe/Ni availability"]
    if missing_counts.get("PROTECT"):
        variables.append("- abrasion / UV stress for protection testing")
    if missing_counts.get("SEPARATE") or reaction_risks:
        variables.append("- mechanical fragmentation and rejoining rate")
    return variables


def build_hypothesis_report(inputs: HypothesisReportInputs) -> str:
    rdkit_rows = _read_csv(inputs.rdkit_search_csv)
    reaction_rows = _read_csv(inputs.reaction_search_csv)
    final_rows = _read_csv(inputs.final_population_csv)
    summary = _read_json(inputs.summary_json)
    best_text = _read_text(inputs.best_candidate_txt)

    candidate_rows = [*rdkit_rows, *final_rows]
    gene_counts = _count_field(candidate_rows, "detected_genes")
    topology_counts = _count_field(candidate_rows, "topology_tags")
    missing_counts = _count_field(candidate_rows, "missing_functions")
    risk_counts = _count_field(candidate_rows, "risk_flags") + _count_field(reaction_rows, "risks")
    reaction_function_counts = _count_field(reaction_rows, "new_functions")

    lines = [
        "# Silive hypothesis report",
        "",
        "## Source files",
        _source_link(inputs.rdkit_search_csv, "rdkit_search_csv"),
        _source_link(inputs.reaction_search_csv, "reaction_search_csv"),
        _source_link(inputs.final_population_csv, "final_population_csv"),
        _source_link(inputs.best_candidate_txt, "best_candidate_txt"),
        _source_link(inputs.summary_json, "summary_json"),
        "",
        "## Run summary",
        f"- best_candidate_id: {summary.get('best_candidate_id', 'unknown')}",
        f"- best_candidate_score: {summary.get('best_candidate_score', 'unknown')}",
        f"- best_viability: {summary.get('best_viability', 'unknown')}",
        "",
        "## Top motif families",
        *_top_lines(gene_counts),
        "",
        "## Promising topology classes",
        *_top_lines(topology_counts),
        "",
        "## Recurring bottlenecks and missing functions",
        *_top_lines(missing_counts),
        "",
        "## Reaction opportunities",
        *_reaction_lines(reaction_rows),
        "",
        "## Candidate leads",
        *_candidate_lines(candidate_rows),
        "",
        "## Risk and validation flags",
        *_top_lines(risk_counts),
        "",
        "## Missing functions suggested by reactions",
        *_top_lines(reaction_function_counts),
        "",
        "## Material classes to compare",
        *_material_classes(topology_counts, gene_counts),
        "",
        "## Environmental variables to compare",
        *_environment_variables(missing_counts, risk_counts),
        "",
        "## Best candidate excerpt",
    ]
    if best_text:
        lines.extend(["```text", best_text.strip(), "```"])
    else:
        lines.append("- none observed")
    lines.append("")
    return "\n".join(lines)


def write_hypothesis_report(inputs: HypothesisReportInputs) -> str:
    report = build_hypothesis_report(inputs)
    inputs.output.parent.mkdir(parents=True, exist_ok=True)
    inputs.output.write_text(report, encoding="utf-8")
    return report
