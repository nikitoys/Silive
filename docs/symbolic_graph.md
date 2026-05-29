# Symbolic graph layer

The symbolic graph layer preserves RDKit topology instead of collapsing every candidate into a single symbolic chain.

Run:

```bash
pip install -e .[chem]
silive rdkit-graph-evaluate "[Si]O[Si]O[Fe]OP(=O)(O)O[Si]"
silive rdkit-graph-evaluate "[Si]O[Si]O[Fe]OP(=O)(O)O[Si]" --json-output outputs/symbolic_graph.json
silive rdkit-graph-diff "[Si]O[Si]" "[Si]O[Fe]OP(=O)(O)O[Si]" --json-output outputs/symbolic_graph_diff.json
```

The command prints a human-readable report, and `--json-output` also writes the symbolic graph in a machine-readable JSON schema. The command prints:

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
- `main_backbone`: diameter-like Si/O/P/Fe/Ni path on the main fragment;
- `topology_tags`: coarse topology labels;
- `graph_properties`: numerical graph descriptors.


## JSON serialization

Every graph object exposes `to_dict()` and `to_json()` helpers, with module-level `symbolic_graph_to_dict()`, `symbolic_graph_to_json()`, and `write_symbolic_graph_json()` wrappers for callers that prefer functions. The JSON payload includes `schema_version: 1`, nodes, edges, rings, fragments, motif counts, the main backbone, topology tags, and graph properties. Tuples are emitted as JSON arrays so downstream tools can consume the output directly.

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
| `labile_bridge_candidate` | metal-oxide or phosphate bridge candidate present |
| `siloxane_rich` | multiple Si-O bonds |

## Graph properties

| Property | Meaning |
| --- | --- |
| `si_o_bond_count` | number of Si-O bonds |
| `metal_o_bond_count` | number of Fe-O/Ni-O bonds |
| `p_o_bond_count` | number of P-O bonds |
| `siloxane_bridge_count` | number of explicitly classified Si-O siloxane bridges |
| `metal_oxide_bridge_count` | number of explicitly classified Fe-O/Ni-O bridges |
| `phosphate_bridge_count` | number of explicitly classified P-O bridges |
| `labile_bridge_candidate_count` | number of bridge candidates treated as labile/separation handles |
| `ring_count` | number of rings |
| `fragment_count` | number of fragments |
| `branching_score` | fraction of high-degree branch nodes |
| `network_score` | heuristic network density score |
| `backbone_length` | diameter-like Si/O/P/Fe/Ni backbone path length |


## Graph diff

`rdkit-graph-diff` compares a parent candidate with a mutated child candidate. The compact diff reports added/removed/unchanged topology tags, deltas for bridge counts, backbone length, fragment count, fragment-signature changes, and changed motif counts. Use `--json-output` to save the same diff payload as JSON for evolutionary search reports or downstream analysis.

## Integration

The proto-gene and proto-genome layers now use symbolic graph information:

- `GENE_SILOXANE_SHELL` uses ring/network topology;
- `GENE_LABILE_SEPARATION` uses fragmented topology, terminal nodes, and hetero-oxide bridges;
- `POLYMERIZE` uses backbone length and network score;
- `PROTECT` uses ring count and network score.

`rdkit-search` CSV output includes topology tags and graph properties so candidate ranking can be inspected without losing graph topology.
