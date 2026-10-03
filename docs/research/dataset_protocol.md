# Dataset Protocol

Status: proposed reproducible protocol; acquisition and partition manifests pending. Freeze choices before evaluation.

## Source and Initial Support

Initial candidate: NASA C-MAPSS. Authority: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data. Treat histories as simulated. Start reproduction on FD001; expanding to FD002/FD003/FD004 requires separately declared/evaluated support. FD001 is an implementation starting point, not a completed support claim.

## Acquisition and Identity

Record source/version/acquisition time, actual file hashes and usage terms. Namespace engine IDs with dataset, subset and train/test source partition. Preserve raw bytes. Validate column schema, engine identity, cycle ordering, duplicate rows, finite values and operating-setting/sensor metadata.

## Partition Proposal

For FD001's supplied training engines, deterministically allocate 70% fit, 15% validation and 15% calibration by engine, using a recorded seed and actual ID manifest. Keep the supplied test partition/labels for final evaluation. Percentages are proposed experimental design choices and must be finalized before training. All windows of one engine stay in its partition.

## Transformations and Targets

Derive training RUL from permitted run-to-failure histories. Decide/record whether a piecewise cap is used, its value and rationale before final evaluation. Fit sensor selection/scaling/operating-condition handling on fit data only. Compare model candidates under the same target/splits. Choose history/window settings with validation data; do not tune against final labels.

## Calibration Caveat

Engine separation prevents leakage but does not itself establish exchangeability of every correlated window or cutoff distribution. Specify the calibration sampling unit and its relation to the final test cutoff before conformal claims. Report actual coverage/width under that protocol and relevant life/regime groups. Do not claim universal conditional coverage.

## Replay and Robustness

Cutoffs expose observations only through the selected cycle. Corrupt inputs through a separately recorded intervention generator; keep clean/missing/imputed provenance. Test labels remain evaluation-only.

## Artifacts

Preserve source hashes, ID manifests, target definitions, fitted transforms, preprocessing code version and processed artifact references. Logistics/task mappings are separately labelled synthetic inputs and do not become engine truth labels.
