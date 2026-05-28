from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import ALL_GENES

CHEMICAL_ALPHABET = frozenset({"Si", "O", "C", "Fe", "Mg", "Al", "H", "S", "P", "N", "Ni"})
MUTATION_ELEMENTS = ("Si", "O", "C", "Fe", "Mg", "Al", "H", "S", "P", "N", "Ni")

PROPERTY_NAMES = ("stability", "template", "catalysis", "repair", "separation")
ENVIRONMENT_MODIFIED_PROPERTIES = ("stability", "catalysis", "repair", "separation")

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

ENVIRONMENT_MODIFIERS: dict[str, dict[str, float]] = {
    "hydrothermal": {"stability": 0.94, "catalysis": 1.28, "repair": 1.10, "separation": 1.18},
    "dry_hot": {"stability": 0.78, "catalysis": 1.12, "repair": 0.70, "separation": 1.30},
    "acidic": {"stability": 0.72, "catalysis": 1.08, "repair": 0.72, "separation": 1.12},
    "alkaline": {"stability": 1.08, "catalysis": 0.95, "repair": 1.10, "separation": 0.88},
    "cold": {"stability": 1.14, "catalysis": 0.62, "repair": 0.86, "separation": 0.72},
}
SUPPORTED_ENVIRONMENTS = tuple(ENVIRONMENT_MODIFIERS)

FUNCTION_THRESHOLDS = {
    "POL": 0.58,
    "SEP": 0.50,
    "SHELL": 0.70,
    "REPAIR": 0.50,
    "CAT": 0.60,
}

REQUIRED_FUNCTIONS = ("POL", "SEP", "SHELL")
LONG_TERM_FUNCTIONS = ("REPAIR",)
VIABILITY_BONUS = {
    "weak_candidate": 0.0,
    "stable_inert_candidate": 0.8,
    "incomplete_proto_life_candidate": 1.4,
    "proto_life_candidate": 2.2,
    "stable_proto_life_candidate": 3.0,
}


@dataclass(frozen=True, slots=True)
class ChainEvaluation:
    chain: tuple[str, ...]
    environment: str | None
    properties: dict[str, float]
    function_scores: dict[str, float]
    predicted_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    viability: str
    recommendations: tuple[str, ...]
    viability_score: float


@dataclass(frozen=True, slots=True)
class ChainSearchResult:
    evaluation: ChainEvaluation
    source_chain: tuple[str, ...]
    mutation_count: int


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


def validate_environment(environment: str | None) -> str | None:
    if environment is None:
        return None
    if environment not in ENVIRONMENT_MODIFIERS:
        allowed = ", ".join(SUPPORTED_ENVIRONMENTS)
        raise ValueError(f"unknown environment: {environment}. Allowed: {allowed}")
    return environment


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


def apply_environment_modifiers(properties: dict[str, float], environment: str | None) -> dict[str, float]:
    environment = validate_environment(environment)
    if environment is None:
        return dict(properties)

    modifiers = ENVIRONMENT_MODIFIERS[environment]
    adjusted = dict(properties)
    for name in ENVIRONMENT_MODIFIED_PROPERTIES:
        adjusted[name] = round(min(1.0, max(0.0, adjusted[name] * modifiers[name])), 3)
    return adjusted


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


def calculate_viability_score(
    properties: dict[str, float],
    function_scores: dict[str, float],
    functions: tuple[str, ...],
    viability: str,
) -> float:
    required_score = sum(function_scores[name] for name in REQUIRED_FUNCTIONS) / len(REQUIRED_FUNCTIONS)
    long_term_score = function_scores["REPAIR"] * 0.35 + function_scores["CAT"] * 0.20
    property_balance = min(properties.values()) * 0.50
    function_bonus = len(functions) * 0.12
    score = required_score + long_term_score + property_balance + function_bonus + VIABILITY_BONUS[viability]
    return round(score, 3)


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


def evaluate_chain(chain: str | Iterable[str], *, environment: str | None = None) -> ChainEvaluation:
    environment = validate_environment(environment)
    parsed = parse_chain(chain)
    base_properties = average_chain_properties(parsed)
    properties = apply_environment_modifiers(base_properties, environment)
    function_scores = score_functions(properties)
    functions = predicted_functions(function_scores)
    missing = tuple(function for function in (*REQUIRED_FUNCTIONS, *LONG_TERM_FUNCTIONS) if function not in functions)
    viability = classify_viability(functions, function_scores)
    recommendations = build_recommendations(missing)
    viability_score = calculate_viability_score(properties, function_scores, functions, viability)

    return ChainEvaluation(
        chain=parsed,
        environment=environment,
        properties=properties,
        function_scores=function_scores,
        predicted_functions=functions,
        missing_functions=missing,
        viability=viability,
        recommendations=recommendations,
        viability_score=viability_score,
    )


def mutate_chain(
    chain: tuple[str, ...],
    rng: random.Random,
    *,
    elements: tuple[str, ...] = MUTATION_ELEMENTS,
    max_length: int = 16,
) -> tuple[str, ...]:
    operation = rng.choice(("replace", "insert", "delete"))
    mutated = list(chain)

    if operation == "replace" or len(mutated) <= 2:
        index = rng.randrange(len(mutated))
        choices = [element for element in elements if element != mutated[index]]
        mutated[index] = rng.choice(choices)
    elif operation == "insert" and len(mutated) < max_length:
        index = rng.randrange(len(mutated) + 1)
        mutated.insert(index, rng.choice(elements))
    else:
        index = rng.randrange(len(mutated))
        del mutated[index]

    if len(mutated) < 2:
        return chain
    return tuple(mutated)


def search_chains(
    seed_chain: str | Iterable[str],
    *,
    rounds: int = 500,
    top_n: int = 10,
    seed: int | None = None,
    max_length: int = 16,
    environment: str | None = None,
) -> list[ChainSearchResult]:
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    environment = validate_environment(environment)
    rng = random.Random(seed)
    source = parse_chain(seed_chain)
    seen: set[tuple[str, ...]] = set()
    candidates: list[ChainSearchResult] = []
    current = source

    for mutation_count in range(rounds + 1):
        if current not in seen:
            seen.add(current)
            candidates.append(
                ChainSearchResult(
                    evaluation=evaluate_chain(current, environment=environment),
                    source_chain=source,
                    mutation_count=mutation_count,
                )
            )
        current = mutate_chain(current, rng, max_length=max_length)

    candidates.sort(
        key=lambda result: (
            result.evaluation.viability_score,
            len(result.evaluation.predicted_functions),
            result.evaluation.properties["stability"],
        ),
        reverse=True,
    )
    return candidates[:top_n]


def write_chain_search_csv(results: list[ChainSearchResult], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "chain",
        "environment",
        "viability_score",
        "viability",
        "predicted_functions",
        "missing_functions",
        "stability",
        "template",
        "catalysis",
        "repair",
        "separation",
        "POL",
        "SEP",
        "SHELL",
        "REPAIR",
        "CAT",
        "mutation_count",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, result in enumerate(results, start=1):
            evaluation = result.evaluation
            writer.writerow(
                {
                    "rank": rank,
                    "chain": "-".join(evaluation.chain),
                    "environment": evaluation.environment or "none",
                    "viability_score": evaluation.viability_score,
                    "viability": evaluation.viability,
                    "predicted_functions": "+".join(evaluation.predicted_functions),
                    "missing_functions": "+".join(evaluation.missing_functions),
                    "stability": evaluation.properties["stability"],
                    "template": evaluation.properties["template"],
                    "catalysis": evaluation.properties["catalysis"],
                    "repair": evaluation.properties["repair"],
                    "separation": evaluation.properties["separation"],
                    "POL": evaluation.function_scores["POL"],
                    "SEP": evaluation.function_scores["SEP"],
                    "SHELL": evaluation.function_scores["SHELL"],
                    "REPAIR": evaluation.function_scores["REPAIR"],
                    "CAT": evaluation.function_scores["CAT"],
                    "mutation_count": result.mutation_count,
                }
            )


def format_search_results(results: list[ChainSearchResult]) -> str:
    lines = ["rank | score | environment | viability | functions | chain"]
    lines.append("--- | ---: | --- | --- | --- | ---")
    for rank, result in enumerate(results, start=1):
        evaluation = result.evaluation
        functions = "+".join(evaluation.predicted_functions) if evaluation.predicted_functions else "none"
        lines.append(
            f"{rank} | {evaluation.viability_score:.3f} | {evaluation.environment or 'none'} | "
            f"{evaluation.viability} | {functions} | {'-'.join(evaluation.chain)}"
        )
    return "\n".join(lines)


def format_scorecard(evaluation: ChainEvaluation) -> str:
    lines = [
        f"chain: {'-'.join(evaluation.chain)}",
        f"environment: {evaluation.environment or 'none'}",
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
        f"viability score: {evaluation.viability_score:.3f}",
    ])

    if evaluation.recommendations:
        lines.extend(["", "recommendations:"])
        for item in evaluation.recommendations:
            lines.append(f"  - {item}")

    return "\n".join(lines)
