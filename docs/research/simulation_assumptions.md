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
