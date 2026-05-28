# Experimental reaction simulator

The reaction simulator is an abstract transition model over RDKit/symbolic graph candidates. It is not a wet-lab synthesis procedure and does not claim that a reaction is chemically feasible.

Its purpose is to ask: if a candidate gained or lost certain motifs, which proto-life functions would likely improve or degrade?

## Single candidate

```bash
pip install -e .[chem]
silive rdkit-reaction-simulate "[Si]O[Si]O[Fe]O[Si]" --top 10
```

Output includes:

- source `genome_score`;
- ranked reaction opportunities;
- expected score delta;
- new functions;
- risks;
- symbolic product description.

## Batch search

```bash
silive rdkit-reaction-search examples/rdkit_candidates.smi --output outputs/reaction_search.csv --top 20
```

CSV columns:

| Column | Meaning |
| --- | --- |
| `rank` | ranking by expected delta score |
| `name` | candidate name |
| `molecule` | source SMILES/SMARTS |
| `reaction_id` | reaction rule identifier |
| `reaction_name` | human-readable reaction name |
| `before_score` | source proto-genome score |
| `after_score` | expected score after abstract transition |
| `delta_score` | expected score change |
| `new_functions` | functions newly covered by the transition |
| `risks` | heuristic risks introduced by the transition |
| `product_symbolic_description` | symbolic product description, not a real SMILES |

## Reaction rules

| Rule | Meaning |
| --- | --- |
| `RXN_SIO_GROWTH` | extend Si-O backbone |
| `RXN_SIO_BRANCH` | branch Si-O network |
| `RXN_FE_CENTER_ADD` | add Fe-O catalytic center |
| `RXN_NI_CENTER_ADD` | add Ni-O catalytic center |
| `RXN_P_REPAIR_BRIDGE` | add phosphate-like repair bridge |
| `RXN_LABILE_BREAK` | split a labile bridge / separation |
| `RXN_RING_CLOSURE` | form Si/O ring |
| `RXN_FRAGMENT_REJOIN` | reconnect fragments through Si-O bridge |

## Scope

The simulator works on motifs, graph tags, proto-gene coverage, and proto-genome score. It intentionally avoids experimental conditions, quantities, temperatures, procedures, or synthesis instructions.
