# Evaluation Protocol

Status: metrics/procedure drafted; final numerical quality/performance budgets remain to be frozen before their test evaluations. These unresolved budgets block corresponding release claims.

## Common Rules

Record revision, environment, dataset/split/target/manifests, model/configuration and seeds. Use identical candidate comparison inputs and preserve failures. Define sampling, aggregations and repeated-run procedure before final test inspection. Distinguish validation tuning from final evaluation.

## Prediction

Compare engineered classical regression/boosting and a sequence candidate. Report MAE, RMSE and a defined asymmetric late-prediction score. Specify whether aggregation is engine-level final-cutoff or trajectory-level; do not compare incompatible protocols. Report relevant life-stage/regime results and sample counts. Final acceptable error/late-prediction bounds require a recorded decision.

## Uncertainty

Record nominal interval level, calibration sampling unit, empirical coverage and width. Compare before/after calibration where applicable. Avoid apparent coverage gained by uselessly wide intervals: freeze both coverage tolerance and width criterion. Groups with insufficient sample support are disclosed. No interval-to-individual-failure-probability conversion.

## Alerts

Compare single-threshold and selected stability policies on common histories. Define the reference event, detection window and false-alert counting unit. Report warning lead time, misses, false alerts and recommendation changes. Freeze budgets and allowed tradeoffs before test evaluation.

## Scheduling

Define task instance families, hard constraints, granularity and objective. Compare the selected solver to a simple policy on the same instances/settings. Report validation failures, solver status, feasible objective, bounds/gap when meaningful, runtime and replanning changes. Zero hard-constraint violations in usable output is mandatory; quality/runtime budgets remain to be set.

## Simulation

Use analytically understandable reference cases first. Compare policies with matched scenario definitions and a documented common-input/random-stream design where applicable. Report aircraft-time availability/downtime, queue waits, stockouts, unplanned groundings and useful-life penalties only when supported. Specify replications and variability calculation; retain per-run results. Benefits are measured, not required invented percentages.

## Robustness

Define random missing values, contiguous outages, noise and regime interventions. Compare simple imputation/masks against advanced candidates if used. Report errors, interval coverage and withholding rates under each intervention, rather than hiding excluded inputs.

## Interface/System Performance

Declare actual target hardware/browser, data sizes, visible-chart sizes, users/concurrent jobs and retention assumptions. Measure relevant p95/p99 API/interaction latency, queue wait, memory/CPU and errors while jobs run. Freeze budgets before interpreting acceptance. Do not infer project throughput from generic framework benchmarks.

## Final Decisions

Register metric definitions, budgets and support boundary as a versioned evaluation configuration. Choose the model/policy from actual valid results; the best baseline may win. Any inspected-test retuning requires disclosed new evaluation status and limits on subsequent claims.
