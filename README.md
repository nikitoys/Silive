# Silive

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

## Run tests

```bash
pytest
```

## What to test first

1. Can `POL + SEP + SHELL` maintain a sequence?
2. How much mutation can the code survive without `REPAIR`?
3. Does `POL` become useless without `SEP`?
4. When does `CAT` help stabilize otherwise bad chemistry?
5. Which gene knockout causes extinction first?
