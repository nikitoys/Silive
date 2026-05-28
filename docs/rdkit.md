# Experimental RDKit layer

Silive can optionally evaluate a real RDKit molecular graph and bridge it into the existing symbolic chemistry scorecard.

Install the chemistry extra:

```bash
pip install -e .[chem]
```

Run:

```bash
silive rdkit-evaluate "[Si]O[Si]O[Fe]O[Si]"
```

The RDKit layer:

1. tries to parse the input as SMILES, then as SMARTS;
2. extracts atoms, elements, bonds, rings, and fragments;
3. reports `molecular_validity`;
4. counts motifs `Si-O-Si`, `Fe-O`, `Ni-O`, and `P-O`;
5. converts the largest RDKit fragment into a symbolic chain;
6. evaluates that chain with the existing Silive properties: `stability`, `template`, `catalysis`, `repair`, and `separation`;
7. prints the normal symbolic scorecard below the RDKit graph summary.

Tests in `tests/test_rdkit_chemistry.py` are skipped automatically when RDKit is not installed.

The base CI smoke test calls `silive rdkit-evaluate` without installing RDKit and accepts the expected optional-dependency warning. To run the full RDKit tests locally, install the chemistry extra first.
