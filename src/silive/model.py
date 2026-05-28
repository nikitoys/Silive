from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

ALPHABET = ("A", "B", "C", "D")

PAIR_STABILITY: dict[tuple[str, str], float] = {
    ("A", "B"): 0.90,
    ("B", "A"): 0.90,
    ("A", "C"): 0.60,
    ("C", "A"): 0.60,
    ("B", "C"): 0.50,
    ("C", "B"): 0.50,
    ("A", "D"): 0.20,
    ("D", "A"): 0.20,
    ("C", "D"): 0.30,
    ("D", "C"): 0.30,
    ("B", "D"): 0.25,
    ("D", "B"): 0.25,
}

ALL_GENES = ("POL", "SEP", "SHELL", "REPAIR", "CAT")
TARGET_SEQUENCE = "ABABAB"


@dataclass(slots=True)
class SimulationConfig:
    generations: int = 100
    population_limit: int = 100
    start_population: int = 10
    start_sequence: str = TARGET_SEQUENCE
    start_genes: frozenset[str] = frozenset({"POL", "SEP", "SHELL"})
    base_mutation_rate: float = 0.08
    gene_mutation_rate: float = 0.03
    seed: int | None = None


@dataclass(slots=True)
class ProtoLife:
    sequence: str
    genes: set[str] = field(default_factory=set)
    energy: float = 10.0
    alive: bool = True
    base_mutation_rate: float = 0.08
    gene_mutation_rate: float = 0.03

    def pair_stability(self, left: str, right: str) -> float:
        base = PAIR_STABILITY.get((left, right), 0.10)
        if "CAT" in self.genes and base < 0.50:
            base += 0.20
        return min(base, 1.0)

    def stability(self) -> float:
        if len(self.sequence) < 2:
            return 0.0
        values = [
            self.pair_stability(left, right)
            for left, right in zip(self.sequence, self.sequence[1:])
        ]
        return sum(values) / len(values)

    def survival_chance(self) -> float:
        chance = self.stability()
        if "SHELL" in self.genes:
            chance *= 2.0
        return min(chance, 0.98)

    def copy_speed(self) -> float:
        return 5.0 if "POL" in self.genes else 1.0

    def separation_chance(self) -> float:
        return 0.70 if "SEP" in self.genes else 0.15

    def mutation_rate(self) -> float:
        rate = self.base_mutation_rate
        if "REPAIR" in self.genes:
            rate *= 0.35
        return rate

    def copy_probability(self) -> float:
        return min(0.10 * self.copy_speed(), 0.90)

    def mutate_symbol(self, symbol: str, rng: random.Random) -> str:
        if rng.random() < self.mutation_rate():
            return rng.choice(ALPHABET)
        return symbol

    def mutate_genes(self, rng: random.Random) -> set[str]:
        new_genes = set(self.genes)
        if rng.random() < self.gene_mutation_rate:
            gene = rng.choice(ALL_GENES)
            if gene in new_genes:
                new_genes.remove(gene)
            else:
                new_genes.add(gene)
        return new_genes

    def copy(self, rng: random.Random) -> ProtoLife | None:
        if rng.random() > self.copy_probability():
            return None
        if rng.random() > self.separation_chance():
            return None

        child_sequence = "".join(self.mutate_symbol(symbol, rng) for symbol in self.sequence)
        child = ProtoLife(
            sequence=child_sequence,
            genes=self.mutate_genes(rng),
            energy=5.0,
            base_mutation_rate=self.base_mutation_rate,
            gene_mutation_rate=self.gene_mutation_rate,
        )
        self.energy -= 3.0
        return child

    def step(self, rng: random.Random) -> None:
        if not self.alive:
            return

        if rng.random() > self.survival_chance():
            self.alive = False
            return

        self.energy -= 1.0
        self.energy += self.stability() * 2.0

        if "CAT" in self.genes:
            self.energy += 0.5

        if self.energy <= 0:
            self.alive = False

    def fitness(self, target: str = TARGET_SEQUENCE) -> float:
        matches = sum(1 for current, expected in zip(self.sequence, target) if current == expected)
        score = 0.0
        score += matches * 3.0
        score += self.stability() * 10.0
        score += self.energy
        score -= len(self.genes) * 0.5
        return score


def _make_initial_population(config: SimulationConfig) -> list[ProtoLife]:
    return [
        ProtoLife(
            sequence=config.start_sequence,
            genes=set(config.start_genes),
            energy=10.0,
            base_mutation_rate=config.base_mutation_rate,
            gene_mutation_rate=config.gene_mutation_rate,
        )
        for _ in range(config.start_population)
    ]


def _summarize_generation(generation: int, population: list[ProtoLife]) -> dict:
    best = population[0]
    gene_counter: Counter[str] = Counter()
    seq_counter: Counter[str] = Counter()

    for organism in population:
        gene_counter.update(organism.genes)
        seq_counter[organism.sequence] += 1

    avg_stability = sum(o.stability() for o in population) / len(population)
    avg_energy = sum(o.energy for o in population) / len(population)

    return {
        "generation": generation,
        "population": len(population),
        "best_sequence": best.sequence,
        "best_genes": tuple(sorted(best.genes)),
        "best_fitness": round(best.fitness(), 3),
        "avg_stability": round(avg_stability, 3),
        "avg_energy": round(avg_energy, 3),
        "genes": dict(gene_counter),
        "top_sequences": seq_counter.most_common(3),
    }


def simulate(config: SimulationConfig | None = None) -> tuple[list[ProtoLife], list[dict]]:
    config = config or SimulationConfig()
    rng = random.Random(config.seed)
    population = _make_initial_population(config)
    history: list[dict] = []

    for generation in range(config.generations):
        new_population: list[ProtoLife] = []

        for organism in population:
            organism.step(rng)
            if organism.alive:
                new_population.append(organism)
                child = organism.copy(rng)
                if child is not None:
                    new_population.append(child)

        if not new_population:
            history.append(
                {
                    "generation": generation,
                    "population": 0,
                    "extinct": True,
                }
            )
            return [], history

        new_population.sort(key=lambda organism: organism.fitness(), reverse=True)
        population = new_population[: config.population_limit]
        history.append(_summarize_generation(generation, population))

    return population, history


def compare_gene_sets(
    gene_sets: Iterable[set[str] | frozenset[str]],
    *,
    generations: int = 100,
    runs: int = 20,
    seed: int | None = None,
    base_mutation_rate: float = 0.08,
) -> list[dict]:
    rng = random.Random(seed)
    results: list[dict] = []

    for genes in gene_sets:
        survival_count = 0
        final_populations: list[int] = []
        final_stabilities: list[float] = []
        final_fitnesses: list[float] = []

        for _ in range(runs):
            run_seed = rng.randrange(0, 2**32)
            population, history = simulate(
                SimulationConfig(
                    generations=generations,
                    start_genes=frozenset(genes),
                    base_mutation_rate=base_mutation_rate,
                    seed=run_seed,
                )
            )
            final_record = history[-1]
            final_populations.append(final_record["population"])

            if population:
                survival_count += 1
                final_stabilities.append(final_record["avg_stability"])
                final_fitnesses.append(final_record["best_fitness"])
            else:
                final_stabilities.append(0.0)
                final_fitnesses.append(0.0)

        results.append(
            {
                "genes": tuple(sorted(genes)),
                "runs": runs,
                "survival_rate": round(survival_count / runs, 3),
                "avg_final_population": round(sum(final_populations) / runs, 3),
                "avg_final_stability": round(sum(final_stabilities) / runs, 3),
                "avg_best_fitness": round(sum(final_fitnesses) / runs, 3),
            }
        )

    results.sort(key=lambda row: (row["survival_rate"], row["avg_best_fitness"]), reverse=True)
    return results
