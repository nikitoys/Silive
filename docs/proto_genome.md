# Minimal chemical proto-genome

The proto-genome layer evaluates whether detected chemical proto-genes cover a minimal functional set for silicon-like proto-life.

Run:

```bash
pip install -e .[chem]
silive rdkit-genome-evaluate "[Si]O[Si]O[Fe]O[Si]"
```

The command prints:

1. RDKit graph scorecard;
2. detected proto-genes;
3. minimal proto-genome coverage;
4. missing functions;
5. bottlenecks;
6. recommendations;
7. final `genome_score`.

## Minimal functions

| Function | Meaning |
| --- | --- |
| `TEMPLATE` | storage/copying of structure |
| `POLYMERIZE` | chain or network growth |
| `CATALYZE` | catalytic center |
| `SEPARATE` | separation of copy or fragment |
| `PROTECT` | shell, matrix, or persistence |
| `REPAIR` | correction or stabilization of defects |

## Coverage rules

| Rule | Covered function |
| --- | --- |
| `GENE_SI_TEMPLATE` present | `TEMPLATE` |
| long Si-O chain or dense Si-O network | `POLYMERIZE` |
| `GENE_FE_CATALYSIS` or `GENE_NI_CATALYSIS` present | `CATALYZE` |
| `GENE_P_REPAIR` present | `REPAIR` |
| Si-O rings or dense Si-O network | `PROTECT` |
| fragments, terminal atoms, or labile handles | `SEPARATE` |

## Recommendations

The evaluator emits simple design hints when functions are missing:

- missing `REPAIR` -> add P-O / phosphate-like bridge;
- missing `CATALYZE` -> add Fe-O or Ni-O center;
- missing `PROTECT` -> add Si-O ring/network;
- missing `SEPARATE` -> add labile bridge or terminal handle;
- missing `TEMPLATE` -> add repeated Si-O-Si motifs;
- missing `POLYMERIZE` -> extend or connect the Si-O scaffold.

## Scope

This is a heuristic design-space filter, not proof of chemical viability. It helps rank and debug candidate motifs before deeper graph, reaction, or wet-lab modeling.
