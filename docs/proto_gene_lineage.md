# Proto-gene lineage search

The proto-gene lineage layer searches for heritable silicon/mineral-like motif candidates in a computational, symbolic model.

It asks whether a candidate motif can:

1. store a template-like structural pattern;
2. produce child-like variants through abstract graph transitions;
3. separate a child fragment or copy-like motif;
4. retain functional coverage across generations.

This is a simulator and reporting layer. It does not describe laboratory operations.

## Run RDKit mode

```bash
pip install -e .[chem]
silive proto-gene-search examples/rdkit_candidates.smi \
  --mode rdkit \
  --generations 10 \
  --population-size 20 \
  --runs 10 \
  --environment hydrothermal \
  --output-dir outputs/proto_gene_search \
  --seed 42
```

## Run symbolic chain mode

```bash
silive proto-gene-search \
  --mode chain \
  --seed-chain "Si-O-Si-O-Fe-O-Si" \
  --rounds 200 \
  --generations 10 \
  --output-dir outputs/proto_gene_search \
  --seed 42
```

Chain mode works without RDKit. RDKit mode uses the existing parsing, symbolic graph, proto-gene, proto-genome, reaction opportunity, and mutation helpers.

## Metrics

| Metric | Meaning |
| --- | --- |
| `template_score` | template-like evidence from symbolic properties, Si-O-Si motifs, backbone length, and Si/O topology |
| `copyability_score` | ability to preserve and extend a copy-like motif in the abstract model |
| `separation_score` | evidence for child-fragment separation from separation properties, fragments, terminal nodes, and labile-break opportunities |
| `survival_score` | structural persistence from stability, protection coverage, shell/network/ring evidence, and chain simulation survival when available |
| `function_retention_rate` | fraction of parent functions retained by child candidates |
| `lineage_depth` | deepest consecutive retained lineage above the configured retention threshold |
| `proto_gene_score` | weighted ranking score combining the metrics above |

Default score weights:

| Component | Weight |
| --- | ---: |
| template | 0.22 |
| copyability | 0.20 |
| separation | 0.18 |
| survival | 0.18 |
| function retention | 0.17 |
| lineage depth | 0.05 |

## Outputs

The command writes:

| File | Meaning |
| --- | --- |
| `proto_gene_candidates.csv` | ranked final candidates with scores, topology tags, functions, validity, and lineage depth |
| `lineage_history.csv` | parent/child transitions, retained/lost/new functions, event labels, and score deltas |
| `proto_gene_summary.json` | run config, thresholds, score weights, aggregate retention stats, and safety scope |
| `best_proto_gene.json` | machine-readable best candidate |
| `proto_gene_report.md` | readable report with limitations and safety boundaries |

## Safety and scope

Silive is a computational symbolic simulator. It does not provide synthesis protocols, lab parameters, quantities, temperatures, pressures, timings, or operational experimental instructions.

The lineage events are abstract graph/motif transitions for ranking and hypothesis generation. They are not real reaction procedures, synthesis routes, or validation of experimental feasibility.

Known limitations:

- heuristic graph/motif model, not kinetic, thermodynamic, quantum, or laboratory validation;
- RDKit parsing is a convenience layer and may reject useful symbolic motifs;
- lineage events are computational abstractions, not real synthesis routes;
- `proto_gene_score` is a ranking heuristic, not evidence of life or experimental feasibility;
- environments are symbolic modifiers, not physical operating conditions.
