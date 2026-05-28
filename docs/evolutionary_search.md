# Evolutionary RDKit/symbolic search

The evolutionary search is an abstract computational search over RDKit/symbolic motif candidates.

Its goal is to explore motif-level variants, apply abstract reaction opportunities, and select candidates by `candidate_score` and `genome_score`.

## Run

```bash
pip install -e .[chem]
silive rdkit-evolve examples/rdkit_candidates.smi \
  --generations 20 \
  --population-size 30 \
  --elite-size 5 \
  --output-dir outputs/evolution \
  --seed 42
```

The input file is optional. Without it, Silive starts from a small default set of Si/O, Fe/O, Ni/O, and P/O motif candidates.

## Search loop

For each generation:

1. keep the top elite candidates;
2. mutate motif strings with symbolic operators;
3. optionally apply the best abstract reaction opportunity;
4. evaluate via RDKit candidate search/proto-genome scoring;
5. sort by `candidate_score` and `genome_score`;
6. save history.

## Mutation operators

| Operator | Meaning |
| --- | --- |
| `add_si_o_unit` | add a Si-O unit to the scaffold |
| `add_fe_o_center` | add an Fe-O center |
| `add_ni_o_center` | add a Ni-O center |
| `add_p_o_bridge` | add a phosphate-like P-O bridge |
| `close_si_o_ring_symbolically` | replace candidate with a symbolic Si/O ring candidate |
| `split_labile_bridge` | add a separated symbolic fragment |
| `duplicate_si_o_segment` | duplicate a Si-O-Si segment |
| `remove_weak_terminal_group` | remove a simple terminal group when present |

## Outputs

The command writes:

| File | Meaning |
| --- | --- |
| `evolution_history.csv` | all candidates retained at each generation |
| `final_population.csv` | final ranked population |
| `best_candidate.txt` | readable best-candidate report |
| `summary.json` | run metadata and best score |

`best_candidate.txt` includes molecule/symbolic description, scores, detected genes, covered/missing functions, topology tags, applied reactions/mutations, and interpretation.

## Scope

This layer searches symbolic motif space. Mutations and reaction applications are computational abstractions used to guide hypothesis generation and compare motif families.
