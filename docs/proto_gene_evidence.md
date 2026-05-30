# Proto-gene evidence framework

Silive treats proto-gene evidence as reproducible computational evidence inside the current symbolic model. It is not proof of real chemistry, real biology, or laboratory feasibility.

## Working definition

A proto-gene inside Silive is a motif or topology pattern that repeatedly maps to a modeled function under the current scoring assumptions. The evidence is model-local:

- a candidate has a detectable motif or graph feature;
- the motif maps to one or more modeled functions;
- the function is retained under model perturbations or symbolic lineage-like variants;
- the candidate scores above simple null controls;
- ablation of the supporting feature reduces the claimed function or score.

The current evidence model version is `proto-gene-evidence-v0.1`.

## Evidence levels

`MOTIF_HIT` means the detector found a motif such as `Si-O-Si`, `Fe-O`, `Ni-O`, `P-O`, ring/network protection, or fragmented/terminal separation evidence. This is only a detected feature.

`FUNCTIONAL_CANDIDATE` means the motif hit also contributes to modeled proto-life functions such as `TEMPLATE`, `POLYMERIZE`, `CATALYZE`, `SEPARATE`, `PROTECT`, or `REPAIR`.

`LINEAGE_RETAINED` means the candidate keeps modeled gene/function evidence under the evidence layer's symbolic null/retention checks. This is a computational retention signal, not reproduction in a physical system.

`ROBUST_LEAD` means the candidate is a strong model-local lead: it has functional coverage, retains evidence, and is enriched over null controls under the configured run. It is still only a computational lead.

`NONE` means no meaningful proto-gene evidence was found by this evidence layer.

## Motif hit vs candidate vs strong lead

A motif hit is a local detector event. It can be a single repeated bridge, metal-oxide motif, phosphate-like bridge, ring/network tag, fragment tag, or terminal handle.

A proto-gene candidate is a motif hit that contributes to at least one modeled function and survives comparison against the expectation corpus.

A strong or robust lead is a proto-gene candidate that also shows enrichment over shuffled null variants and does not depend entirely on an unrelated feature group in ablation.

## Computational scope

This framework tests consistency inside Silive:

- expected model behavior versus observed detector output;
- precision/recall-like metrics for genes and functions;
- false positives and false negatives;
- null model enrichment;
- ablation sensitivity;
- reproducibility with fixed seeds.

It does not validate real chemical synthesis, kinetics, thermodynamics, biological inheritance, or experimental feasibility.

## Safety boundary

Silive is computational only. Do not add synthesis protocols, wet-lab procedures, quantities, temperatures, pressures, timings, apparatus settings, or operational experimental instructions. Any chemistry-like interpretation in this framework is a heuristic/model assumption.
