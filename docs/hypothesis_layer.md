# Hypothesis report layer

`silive hypothesis-report` reads RDKit search, reaction search, and evolutionary search outputs and writes a linked Markdown report for hypothesis triage.

Run:

```bash
silive hypothesis-report outputs/evolution --output outputs/hypotheses.md
```

By default the command expects:

- `outputs/rdkit_search.csv`;
- `outputs/reaction_search.csv`;
- `outputs/evolution/final_population.csv`;
- `outputs/evolution/best_candidate.txt`;
- `outputs/evolution/summary.json`.

Use `--rdkit-search-csv` or `--reaction-search-csv` to override the inferred CSV paths.

The report summarizes:

- top motif families and detected proto-genes;
- recurring bottlenecks and missing functions;
- promising topology classes;
- reaction opportunities and newly suggested functions;
- material classes to compare;
- environmental variables to compare;
- candidate leads and source rows/files for traceability.
