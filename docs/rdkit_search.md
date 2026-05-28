# RDKit candidate search

`silive rdkit-search` ranks a batch of SMILES/SMARTS candidates by their fit as chemical proto-genomes for silicon-like proto-life.

Run:

```bash
pip install -e .[chem]
silive rdkit-search examples/rdkit_candidates.smi --output outputs/rdkit_search.csv --top 20
```

## Input format

The input file is a `.smi` or `.txt` file:

```text
# molecule name
[Si]O[Si] si_o_si_template
[Si]O[Si]O[Fe] si_o_si_fe_catalyst
not_a_valid_smiles invalid_candidate
```

Rules:

- one molecule per line;
- optional name after whitespace;
- empty lines are ignored;
- lines starting with `#` are ignored.

## Pipeline

For every candidate, Silive runs:

1. `evaluate_rdkit_molecule`;
2. `detect_proto_genes`;
3. `evaluate_proto_genome`;
4. `candidate_score` ranking.

## Candidate score

The score combines:

- RDKit molecular validity;
- proto-genome score;
- number of covered minimal functions;
- presence of critical functions `TEMPLATE`, `CATALYZE`, and `PROTECT`;
- penalty for missing critical functions;
- bonus for combined `Si-O-Si` + `Fe-O`/`Ni-O` + `P-O` motifs.

## Output table and CSV

Columns:

| Column | Meaning |
| --- | --- |
| `rank` | ranking by score |
| `name` | candidate name |
| `molecule` | original SMILES/SMARTS |
| `score` | final candidate score |
| `molecular_validity` | RDKit parse validity |
| `covered_functions` | minimal proto-genome functions covered |
| `missing_functions` | missing minimal functions |
| `detected_genes` | detected chemical proto-genes |
| `symbolic_chain` | RDKit graph converted to symbolic chain |
| `viability` | rough viability class |

This search is a heuristic screen, not a claim of real chemical viability.
