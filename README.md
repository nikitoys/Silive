# Silive

![CI](https://github.com/nikitoys/Silive/actions/workflows/ci.yml/badge.svg)

**Silive** is a small Python sandbox for testing a Level 1 chemical-logical model of silicon-like proto-life.

The model is intentionally simple: it does not simulate atoms directly. Instead, it treats a proto-organism as a symbolic sequence plus a set of functional genes that modify probabilities.

## Level 1 idea

A sequence such as `ABABAB` represents a proto-code or mineral-polymer template.

Pair stability controls whether the structure survives:

| Pair | Stability |
| --- | ---: |
| A-B / B-A | 0.90 |
| A-C / C-A | 0.60 |
| B-C / C-B | 0.50 |
| A-D / D-A | 0.20 |
| C-D / D-C | 0.30 |
| B-D / D-B | 0.25 |

Genes are probability modifiers:

| Gene | Meaning |
| --- | --- |
| `POL` | polymerase-like stitching; copy speed x5, but copying costs extra energy |
| `SEP` | separation of copy; separation chance 0.7 |
| `SHELL` | protective shell/matrix; adds a configurable survival bonus |
| `REPAIR` | lowers mutation rate |
| `CAT` | catalytic center; slightly stabilizes weak pairs |

## Level 2 symbolic chemistry

Level 2 evaluates concrete symbolic element chains against the proto-life functions used by the Level 1 simulator.

Example:

```bash
silive evaluate-chain "Si-O-Si-O-Fe-O-Si"
```

The evaluator parses the chain, scores symbolic bond properties, maps those properties to proto-life functions, and prints a scorecard.

Scored properties:

| Property | Meaning |
| --- | --- |
| `stability` | scaffold persistence |
| `template` | ability to act as a repeatable copying pattern |
| `catalysis` | catalytic-center potential |
| `repair` | defect-correction potential |
| `separation` | ability to separate a copy without destroying the template |

Function mapping:

| Function | Main source |
| --- | --- |
| `POL` | template + catalysis |
| `SEP` | separation |
| `SHELL` | stability |
| `REPAIR` | repair + template |
| `CAT` | catalysis |

The scorecard also shows missing functions and a rough viability class such as `weak_candidate`, `incomplete_proto_life_candidate`, `proto_life_candidate`, or `stable_proto_life_candidate`.

## Search symbolic chains

`silive search-chain` mutates a seed chain, evaluates every candidate with the same Level 2 scorecard, sorts by `viability_score`, prints the top candidates, and writes a CSV table.

```bash
silive search-chain \
  --seed "Si-O-Si-O-Fe-O-Si" \
  --rounds 1000 \
  --top 20 \
  --random-seed 42 \
  --output outputs/chain_search.csv
```

The CSV includes each candidate chain, viability score, predicted functions, missing functions, symbolic properties, function scores, and mutation count.

## Simulate a symbolic chain

`silive chain-simulate` bridges Level 2 and Level 1. It evaluates a concrete symbolic chain, converts its predicted functions into Level 1 genes, runs repeated simulations, and reports aggregate survival/code preservation metrics.

```bash
silive chain-simulate "Si-O-Si-O-Fe-O-Si" \
  --generations 100 \
  --runs 30 \
  --seed 42
```

Output metrics:

| Metric | Meaning |
| --- | --- |
| `survival_rate` | fraction of runs that did not go extinct |
| `code_preservation_rate` | average fraction of final organisms that still match the start sequence |
| `avg_final_population` | average population at the final generation |
| `avg_final_stability` | average final Level 1 sequence stability |
| `avg_best_fitness` | average best final fitness |

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

For plotting only:

```bash
pip install -e .[plot]
```

## Run one simulation

```bash
silive simulate --generations 100 --population-limit 100 --genes POL SEP SHELL REPAIR
```

You can also tune mutation and shell strength:

```bash
silive simulate \
  --genes POL SEP SHELL REPAIR \
  --mutation-rate 0.12 \
  --shell-bonus 0.20 \
  --seed 42
```

## Compare gene sets

```bash
silive compare --generations 100 --runs 20
```

## Build a phase map

`silive sweep` scans a grid of mutation rates and shell survival bonuses. It writes a CSV table with survival, code preservation, final population, stability, fitness, and a rough zone label.

```bash
silive sweep \
  --mutation-start 0.00 \
  --mutation-stop 0.30 \
  --mutation-steps 16 \
  --shell-start 0.00 \
  --shell-stop 0.40 \
  --shell-steps 16 \
  --genes POL SEP SHELL REPAIR \
  --runs 30 \
  --generations 100 \
  --output phase_map.csv
```

CSV columns:

| Column | Meaning |
| --- | --- |
| `mutation_rate` | base sequence mutation rate |
| `shell_bonus` | extra survival chance from `SHELL` |
| `survival_rate` | fraction of runs that did not go extinct |
| `code_preservation_rate` | fraction of final organisms still matching the start sequence |
| `avg_final_population` | average final population size |
| `avg_final_stability` | average final pair stability |
| `avg_best_fitness` | average best fitness at the end |
| `zone` | rough classification: `dead`, `unstable`, `drifting`, `proto_life`, or `stable_life` |

## Plot a phase map

```bash
silive plot phase_map.csv \
  --metric survival_rate \
  --output survival_rate.png
```

Supported metrics:

```text
survival_rate
code_preservation_rate
avg_final_population
avg_final_stability
avg_best_fitness
```

## Run the visual lab

`silive lab` runs a sweep and creates default heatmaps in one command.

```bash
silive lab \
  --mutation-steps 16 \
  --shell-steps 16 \
  --runs 30 \
  --generations 100 \
  --output-dir outputs
```

Outputs:

```text
outputs/phase_map.csv
outputs/survival_rate.png
outputs/code_preservation_rate.png
```

## Study the REPAIR gene

`silive repair-study` compares `POL + SEP + SHELL` against `POL + SEP + SHELL + REPAIR` and writes CSV files with the delta in survival, code preservation, stability, fitness, and zone classification.

```bash
silive repair-study \
  --mutation-steps 16 \
  --shell-steps 16 \
  --runs 30 \
  --generations 100 \
  --output-dir outputs/repair_study
```

Outputs:

```text
outputs/repair_study/without_repair.csv
outputs/repair_study/with_repair.csv
outputs/repair_study/repair_delta.csv
outputs/repair_study/repair_summary.txt
```

## Run tests

```bash
pytest
```

## Continuous integration

GitHub Actions runs tests on Python 3.10, 3.11, and 3.12. It also runs small `silive evaluate-chain`, `silive search-chain`, `silive chain-simulate`, `silive lab`, and `silive repair-study` smoke tests and uploads the generated outputs as workflow artifacts.

## What to test first

1. Can `POL + SEP + SHELL` maintain a sequence?
2. How much mutation can the code survive without `REPAIR`?
3. Does `POL` become useless without `SEP`?
4. When does `CAT` help stabilize otherwise bad chemistry?
5. Which gene knockout causes extinction first?
6. Which concrete symbolic chains cover the missing functions?
7. Do high-scoring symbolic chains actually survive in Level 1 simulation?
