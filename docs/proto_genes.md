# Chemical proto-genes

The experimental proto-gene layer maps RDKit graph motifs into functional genes for silicon-like proto-life.

Run:

```bash
pip install -e .[chem]
silive rdkit-gene-evaluate "[Si]O[Si]O[Fe]O[Si]"
```

The command prints the normal RDKit scorecard and then a proto-gene summary.

## Proto-gene definitions

| Gene | Evidence | Functional interpretation |
| --- | --- | --- |
| `GENE_SI_TEMPLATE` | `Si-O-Si` motif | template + scaffold stability |
| `GENE_FE_CATALYSIS` | `Fe-O` motif | catalytic center |
| `GENE_NI_CATALYSIS` | `Ni-O` motif | catalytic center |
| `GENE_P_REPAIR` | `P-O` motif | repair + partial templating |
| `GENE_SILOXANE_SHELL` | Si/O rings or dense Si-O network | protective shell/stability |
| `GENE_LABILE_SEPARATION` | fragments, terminal atoms, hetero-oxide bridges | separation handle |

## Output sections

The proto-gene summary reports:

1. detected genes;
2. absent genes;
3. covered functions;
4. missing functions.

Covered functions use the existing Silive proto-life vocabulary:

```text
POL
SEP
SHELL
REPAIR
CAT
```

## Notes

This layer is heuristic. It is not a quantum chemistry or reaction-kinetics model. Its purpose is to make chemical hypotheses explicit enough to compare candidate mineral-polymer motifs before deeper simulation.

Tests in `tests/test_proto_genes.py` are skipped automatically when RDKit is not installed.
