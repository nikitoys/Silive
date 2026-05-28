# Symbolic graph layer

The symbolic graph layer preserves RDKit topology instead of collapsing every candidate into a single symbolic chain.

Run:

```bash
pip install -e .[chem]
silive rdkit-graph-evaluate "[Si]O[Si]O[Fe]OP(=O)(O)O[Si]"
```

The command prints:

1. the RDKit scorecard;
2. symbolic graph summary;
3. topology tags;
4. graph properties;
5. main backbone;
6. proto-gene summary;
7. proto-genome evaluation.

## Representation

`SymbolicGraph` contains:

- `nodes`: atoms as symbolic nodes with element, degree, charge, aromaticity, and tags;
- `edges`: bonds with element pairs, bond type, and tags;
- `rings`: RDKit ring atom-index tuples;
- `fragments`: separated molecular fragments;
- `motifs`: RDKit motif counts;
- `main_backbone`: longest Si/O/P/Fe/Ni path on the main fragment;
- `topology_tags`: coarse topology labels;
- `graph_properties`: numerical graph descriptors.

## Topology tags

Possible tags:

| Tag | Meaning |
| --- | --- |
| `linear` | no ring/branch/fragment split detected |
| `branched` | at least one node has degree >= 3 |
| `ring` | RDKit ring detected |
| `network` | dense/ring/branched Si-O topology |
| `fragmented` | more than one fragment |
| `metal_center` | Fe-O or Ni-O bridge present |
| `phosphate_bridge` | P-O bridge present |
| `siloxane_rich` | multiple Si-O bonds |

## Graph properties

| Property | Meaning |
| --- | --- |
| `si_o_bond_count` | number of Si-O bonds |
| `metal_o_bond_count` | number of Fe-O/Ni-O bonds |
| `p_o_bond_count` | number of P-O bonds |
| `ring_count` | number of rings |
| `fragment_count` | number of fragments |
| `branching_score` | fraction of high-degree branch nodes |
| `network_score` | heuristic network density score |
| `backbone_length` | longest Si/O/P/Fe/Ni path length |

## Integration

The proto-gene and proto-genome layers now use symbolic graph information:

- `GENE_SILOXANE_SHELL` uses ring/network topology;
- `GENE_LABILE_SEPARATION` uses fragmented topology, terminal nodes, and hetero-oxide bridges;
- `POLYMERIZE` uses backbone length and network score;
- `PROTECT` uses ring count and network score.

`rdkit-search` CSV output includes topology tags and graph properties so candidate ranking can be inspected without losing graph topology.
