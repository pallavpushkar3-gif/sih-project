# Dataset Protocol

Status: FD001 acquisition, identity, split and target protocol frozen for validation-v1; final test remains uninspected by model-selection code.

## Source and Initial Support

Initial candidate: NASA C-MAPSS. Authority: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data. Treat histories as simulated. Validation-v1 uses FD001 only; expanding to FD002/FD003/FD004 requires separately declared/evaluated support. FD001 acquisition is not by itself a completed prediction-support claim.

## Acquisition and Identity

The official NASA PCoE archive was acquired on 2026-10-04 using `scripts/fetch_dataset.py`. Actual hashes are recorded in `data/sources.yaml` and the ignored local `data/raw/cmapss/manifest.json`. The NASA portal lists the license as not specified. Engine identities are namespaced by dataset, subset and source partition. The loader validates the 26-column schema, integer identities/cycles, consecutive per-engine ordering and finite values.

## Partition Proposal

FD001's 100 supplied training engines are deterministically allocated 70% fit, 15% validation and 15% calibration by engine using seed 26249. The exact identities are retained in the ignored processed manifest. The supplied 100-engine test partition and RUL labels are reserved for final evaluation and are not loaded by model-selection commands. All windows of one engine stay in its partition.

## Transformations and Targets

Derive training RUL from permitted run-to-failure histories and cap the modelling target at 125 cycles for validation-v1. This is a modelling convention for early-life saturation, not a physical life limit. Require 30 observed cycles; engineered and sequence candidates use a 30-cycle history. Fit feature selection/scaling on fit engines only. Candidate validation and calibration sample one cutoff per held-out engine with seed 26249; final supplied test labels remain unavailable to tuning code.

## Calibration Caveat

Engine separation prevents leakage but does not itself establish exchangeability of every correlated window or cutoff distribution. Specify the calibration sampling unit and its relation to the final test cutoff before conformal claims. Report actual coverage/width under that protocol and relevant life/regime groups. Do not claim universal conditional coverage.

## Replay and Robustness

Cutoffs expose observations only through the selected cycle. Corrupt inputs through a separately recorded intervention generator; keep clean/missing/imputed provenance. Test labels remain evaluation-only.

## Artifacts

Preserve source hashes, ID manifests, target definitions, fitted transforms, preprocessing code version and processed artifact references. Logistics/task mappings are separately labelled synthetic inputs and do not become engine truth labels.
