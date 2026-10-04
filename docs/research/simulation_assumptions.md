# Simulation Assumptions

Status: required assumption schema; scenario values supplied through validated fixtures/configuration and not claimed as real fleet measurements.

## Required Scenario Fields

Define fleet/component mappings, initial availability/health, horizon/time unit, usage schedule, task deadlines/durations, qualification/capacity calendars, stock/arrivals, maintenance effectiveness, failure/degradation sampling and baseline/candidate policy versions.

## Calendar Conversion

Life predictions are cycles. A scenario maps cycles to calendar usage through an explicit schedule. Do not assume every day consumes the same cycles unless the fixture deliberately states that assumption.

## Maintenance Effect

Specify whether simulated work replaces/reset a component, partially restores condition or changes no degradation state. Public run-to-failure histories do not establish repair-effect transitions. No assumption is a learned fact unless appropriate data validates it.

## Availability and Metrics

Define available, grounded, waiting and maintenance states, and any excluded time. A primary candidate metric is available aircraft-time divided by total eligible aircraft-time over the horizon; finalize denominator/state treatment per scenario. This is scenario availability, not readiness/airworthiness.

## Uncertainty

Distinguish evaluated prediction uncertainty from invented logistics distributions. A prediction interval alone does not supply a full failure-time distribution. If sampling requires a distribution, justify/calibrate it or use explicitly labelled sensitivity scenarios. Record dependencies/correlation assumptions and seeds/random-stream handling.

## Comparison

Match fleet/horizon/usage and scenario versions across policies. Preserve event traces/reference cases and report poor outcomes. Store the exact assumption manifest with every run.

## Exact-plan replay — 2026-10-05

The new comparison consumes the full saved plan/input snapshot/assignments and SHA-256 identity. Its FIFO baseline has the same task release/deadline/precedence, aircraft, crew/bay calendars, qualification, capacity, stock/expected-delivery and fixed-work constraints. Planned starts, resource waits and completions are SimPy events; expected deliveries are included in the trace and are assumed to occur at recorded times. Each released maintenance task grounds its mapped aircraft until completion or the observation horizon; overlapping intervals count once per aircraft. The denominator is the aircraft represented by input tasks × recorded horizon, not the entire operational fleet. Waiting tasks remain grounded at the horizon.

Declared duration, +25% and +50% overrun cases are deterministic sensitivity assumptions, not probabilities. Overruns can violate planned resource windows/deadlines; these are reported, not authorized as overtime. Cancelled/delayed deliveries or changed work require a new explicit proposal/comparison; this replay does not forecast future replanning. No failure-time distribution, maintenance reset effectiveness or airworthiness is inferred; cost remains null. Negative/zero/worse differences are retained. Existing parts-ready comparison is a separate logistics sensitivity, not the optimized-plan result.
