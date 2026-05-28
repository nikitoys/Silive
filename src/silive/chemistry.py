from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import ALL_GENES

CHEMICAL_ALPHABET = frozenset({"Si", "O", "C", "Fe", "Mg", "Al", "H", "S", "P", "N", "Ni"})

PROPERTY_NAMES = ("stability", "template", "catalysis", "repair", "separation")

DEFAULT_BOND_PROPERTIES = {
    "stability": 0.10,
    "template": 0.05,
    "catalysis": 0.05,
    "repair": 0.05,
    "separation": 0.10,
}

BOND_RULES: dict[tuple[str, str], dict[str, float]] = {
    ("Si", "O"): {"stability": 0.92, "template": 0.82, "catalysis": 0.10, "repair": 0.42, "separation": 0.28},
    ("O", "Si"): {"stability": 0.92, "template": 0.82, "catalysis": 0.10, "repair": 0.42, "separation": 0.28},
    ("Fe", "O"): {"stability": 0.62, "template": 0.30, "catalysis": 0.90, "repair": 0.28, "separation": 0.20},
    ("O", "Fe"): {"stability": 0.62, "template": 0.30, "catalysis": 0.90, "repair": 0.28, "separation": 0.20},
    ("Mg", "O"): {"stability": 0.72, "template": 0.45, "catalysis": 0.45, "repair": 0.35, "separation": 0.38},
    ("O", "Mg"): {"stability": 0.72, "template": 0.45, "catalysis": 0.45, "repair": 0.35, "separation": 0.38},
    ("Al", "O"): {"stability": 0.78, "template": 0.55, "catalysis": 0.20, "repair": 0.35, "separation": 0.25},
    ("O", "Al"): {"stability": 0.78, "template": 0.55, "catalysis": 0.20, "repair": 0.35, "separation": 0.25},
    ("Ni", "O"): {"stability": 0.60, "template": 0.28, "catalysis": 0.86, "repair": 0.25, "separation": 0.22},
    ("O", "Ni"): {"stability": 0.60, "template": 0.28, "catalysis": 0.86, "repair": 0.25, "separation": 0.22},
    ("Si", "C"): {"stability": 0.58, "template": 0.38, "catalysis": 0.10, "repair": 0.18, "separation": 0.55},
    ("C", "Si"): {"stability": 0.58, "template": 0.38, "catalysis": 0.10, "repair": 0.18, "separation": 0.55},
    ("C", "O"): {"stability": 0.50, "template": 0.30, "catalysis": 0.15, "repair": 0.15, "separation": 0.50},
    ("O", "C"): {"stability": 0.50, "template": 0.30, "catalysis": 0.15, "repair": 0.15, "separation": 0.50},
    ("Si", "H"): {"stability": 0.35, "template": 0.10, "catalysis": 0.05, "repair": 0.05, "separation": 0.75},
    ("H", "Si"): {"stability": 0.35, "template": 0.10, "catalysis": 0.05, "repair": 0.05, "separation": 0.75},
    ("Si", "S"): {"stability": 0.42, "template": 0.25, "catalysis": 0.28, "repair": 0.12, "separation": 0.62},
    ("S", "Si"): {"stability": 0.42, "template": 0.25, "catalysis": 0.28, "repair": 0.12, "separation": 0.62},
    ("P", "O"): {"stability": 0.70, "template": 0.50, "catalysis": 0.35, "repair": 0.45, "separation": 0.40},
    ("O", "P"): {"stability": 0.70, "template": 0.50, "catalysis": 0.35, "repair": 0.45, "separation": 0.40},
    ("N", "O"): {"stability": 0.45, "template": 0.25, "catalysis": 0.25, "repair": 0.15, "separation": 0.48},
    ("O", "N"): {"stability": 0.45, "template": 0.25, "catalysis": 0.25, "repair": 0.15, "separation": 0.48},
    ("O", "O"): {"stability": 0.18, "template": 0.08, "catalysis": 0.05, "repair": 0.05, "separation": 0.55},
    ("Si", "Si"): {"stability": 0.22, "template": 0.18, "catalysis": 0.05, "repair": 0.08, "separation": 0.45},
    ("Fe", "Fe"): {"stability": 0.20, "template": 0.05, "catalysis": 0.45, "repair": 0.05, "separation": 0.10},
}

FUNCTION_THRESHOLDS = {
    "POL": 0.58,
    "SEP": 0.50,
    "SHELL": 0.70,
    "REPAIR": 0.50,
    "CAT": 0.60,
}

REQUIRED_FUNCTIONS = ("POL", "SEP", "SHELL")
LONG_TERM_FUNCTIONS = ("REPAIR",)


@dataclass(frozen=True, slots=True)
class ChainEvaluation:
    chain: tuple[str, ...]
    properties: dict[str, float]
    function_scores: dict[str, float]
    predicted_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    viability: str
    recommendations: tuple[str, ...]


def parse_chain(chain: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(chain, str):
        parts = tuple(part.strip() for part in chain.replace(" ", "").split("-") if part.strip())
    else:
        parts = tuple(chain)

    if len(parts) < 2:
        raise ValueError("chain must contain at least two elements")

    unknown = [part for part in parts if part not in CHEMICAL_ALPHABET]
    if unknown:
        allowed = ", ".join(sorted(CHEMICAL_ALPHABET))
        raise ValueError(f"unknown element(s): {', '.join(unknown)}. Allowed: {allowed}")

    return parts


def bond_properties(left: str, right: str) -> dict[str, float]:
    rule = BOND_RULES.get((left, right), DEFAULT_BOND_PROPERTIES)
    return {name: float(rule.get(name, DEFAULT_BOND_PROPERTIES[name])) for name in PROPERTY_NAMES}


def average_chain_properties(chain: tuple[str, ...]) -> dict[str, float]:
    totals = {name: 0.0 for name in PROPERTY_NAMES}
    bonds = list(zip(chain, chain[1:]))

    for left, right in bonds:
        props = bond_properties(left, right)
        for name in PROPERTY_NAMES:
            totals[name] += props[name]

    return {name: round(totals[name] / len(bonds), 3) for name in PROPERTY_NAMES}


def score_functions(properties: dict[str, float]) -> dict[str, float]:
    pol_score = properties["template"] * 0.70 + properties["catalysis"] * 0.30
    sep_score = properties["separation"]
    shell_score = properties["stability"]
    repair_score = properties["repair"] * 0.75 + properties["template"] * 0.25
    cat_score = properties["catalysis"]

    return {
        "POL": round(pol_score, 3),
        "SEP": round(sep_score, 3),
        "SHELL": round(shell_score, 3),
        "REPAIR": round(repair_score, 3),
        "CAT": round(cat_score, 3),
    }


def predicted_functions(function_scores: dict[str, float]) -> tuple[str, ...]:
    return tuple(
        gene
        for gene in ALL_GENES
        if function_scores.get(gene, 0.0) >= FUNCTION_THRESHOLDS[gene]
    )


def classify_viability(functions: tuple[str, ...], function_scores: dict[str, float]) -> str:
    function_set = set(functions)
    required_present = all(function in function_set for function in REQUIRED_FUNCTIONS)

    if required_present and "REPAIR" in function_set:
        return "stable_proto_life_candidate"
    if required_present:
        return "proto_life_candidate"
    if function_scores["SHELL"] >= 0.70 and (function_scores["POL"] >= 0.45 or function_scores["CAT"] >= 0.60):
        return "incomplete_proto_life_candidate"
    if function_scores["SHELL"] >= 0.70:
        return "stable_inert_candidate"
    return "weak_candidate"


def build_recommendations(missing_functions: tuple[str, ...]) -> tuple[str, ...]:
    recommendations = []
    if "POL" in missing_functions:
        recommendations.append("increase template/catalytic patterning, e.g. more alternating Si-O units or catalytic metal-oxygen sites")
    if "SEP" in missing_functions:
        recommendations.append("add controlled weak links or flexible separators, e.g. Si-C, Si-S, C-O, or terminal H-like units")
    if "SHELL" in missing_functions:
        recommendations.append("increase stable scaffold content, especially alternating Si-O, Al-O, Mg-O, or P-O motifs")
    if "REPAIR" in missing_functions:
        recommendations.append("increase defect-correction potential, e.g. add P-O, Mg-O, or repeated template-like motifs")
    if "CAT" in missing_functions:
        recommendations.append("add catalytic metal centers, e.g. Fe-O or Ni-O motifs")
    return tuple(recommendations)


def evaluate_chain(chain: str | Iterable[str]) -> ChainEvaluation:
    parsed = parse_chain(chain)
    properties = average_chain_properties(parsed)
    function_scores = score_functions(properties)
    functions = predicted_functions(function_scores)
    missing = tuple(function for function in (*REQUIRED_FUNCTIONS, *LONG_TERM_FUNCTIONS) if function not in functions)
    viability = classify_viability(functions, function_scores)
    recommendations = build_recommendations(missing)

    return ChainEvaluation(
        chain=parsed,
        properties=properties,
        function_scores=function_scores,
        predicted_functions=functions,
        missing_functions=missing,
        viability=viability,
        recommendations=recommendations,
    )


def format_scorecard(evaluation: ChainEvaluation) -> str:
    lines = [
        f"chain: {'-'.join(evaluation.chain)}",
        "",
        "properties:",
    ]
    for name in PROPERTY_NAMES:
        lines.append(f"  {name}: {evaluation.properties[name]:.3f}")

    lines.extend(["", "function scores:"])
    for gene in ALL_GENES:
        threshold = FUNCTION_THRESHOLDS[gene]
        status = "yes" if gene in evaluation.predicted_functions else "no"
        lines.append(f"  {gene}: {evaluation.function_scores[gene]:.3f} / {threshold:.2f} -> {status}")

    lines.extend([
        "",
        "predicted functions: " + (" + ".join(evaluation.predicted_functions) if evaluation.predicted_functions else "none"),
        "missing functions: " + (", ".join(evaluation.missing_functions) if evaluation.missing_functions else "none"),
        f"viability: {evaluation.viability}",
    ])

    if evaluation.recommendations:
        lines.extend(["", "recommendations:"])
        for item in evaluation.recommendations:
            lines.append(f"  - {item}")

    return "\n".join(lines)
