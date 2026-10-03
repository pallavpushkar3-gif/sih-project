# Coding Agent Instructions

## Project and Status

PS 26249 is a maintenance decision demonstrator. Documentation is drafted; do not assume application code, dependencies or commands exist. Inspect the actual workspace before making implementation claims.

## Required Context

Read `intent.md`, `scope.md`, `design.md` and `rule.md` before substantive implementation. For a feature, read its specification and acceptance criteria. For scientific work, read dataset/evaluation/assumption protocols. For jobs/approval, read the corresponding engineering contracts. `rule.md` is the canonical project rule source.

## Repository Boundaries

- Browser code: `apps/web/`.
- Shared installable Python application: `backend/src/fleet_maintenance/`.
- API calls services; science modules calculate; persistence owns transactional storage.
- Worker processes import shared code instead of maintaining parallel implementations.
- Scripts are entry points, not a second application.
- Preserve existing unrelated work and user changes.

## Implementation Workflow

Inspect relevant files and implemented dependency configuration. Work within authorized scope; make coherent, reviewable changes. Do not create empty source modules merely to match a planned tree. Update corresponding documentation/contracts when behaviour changes. Keep source/test status truthful.

For changes requiring schema/client generation, use the implemented tools, review their outputs and include the relevant changes. Do not fabricate generated files or hand-edit generated client code.

## Commands

Discover verified commands from `README.md`, `Makefile`, `package.json`, `backend/pyproject.toml` and CI configuration. They are pending until implemented. Do not claim a guessed command is runnable or a check passed without executing it. Explain unavailable checks and blockers.

## Verification

Run checks appropriate to the change and retain failures/limitations. High-value checks include engine leakage, transformation parity, units, hard constraints, stock concurrency, stale approval and job recovery. A scientific experiment needs input/split/configuration provenance and an honest reproduction entry.

## Boundaries on Claims and Actions

No invented accuracy, saved downtime or aircraft clearance. Distinguish synthetic logistics and simulated projections. Do not interpret this file as authorization to contact people, publish, deploy or access private operational data. Follow the user's explicit authorization and applicable tool policies; do not introduce unnecessary confirmation for routine reversible implementation.

## Reporting

State what changed, why, what was actually verified and any material remaining blocker. Distinguish implemented behaviour from intended future work.
