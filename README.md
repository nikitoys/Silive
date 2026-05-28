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
| `POL` | polymerase-like stitching; copy speed x5 |
| `SEP` | separation of copy; separation chance 0.7 |
| `SHELL` | protective shell/matrix; survival chance x2 |
| `REPAIR` | lowers mutation rate |
| `CAT` | catalytic center; stabilizes weak pairs |

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

## Compare gene sets

```bash
silive compare --generations 100 --runs 20
```

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
