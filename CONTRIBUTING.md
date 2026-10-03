# Contributing

## Shared Context

Read the root intent/scope/design/rules and the relevant specifications. Keep one source of truth for each document/contract. Changes should solve a defined feature or acceptance requirement.

## Branches and Reviews

Use a focused branch such as `feature/maintenance-planner`, `fix/reservation-conflict` or `docs/data-protocol`. Keep changes coherent; coordinate before changing shared contracts or overlapping module ownership. Commit messages state the concrete change. Review through the repository's chosen PR workflow once configured.

## Pull Requests

Explain the problem, resulting behaviour, related requirements, actual verification and material limitations. Call out schema/API changes, generated outputs and scientific assumptions. Do not present screenshots as proof of transaction or numerical correctness. Keep unrun checks explicitly unrun.

## Data and Research

Use only authorized data. Preserve split/transform/model/configuration identities. Keep large bytes in artifact storage, not source control. Record reproduction results including failures and unreplicated claims. Do not retune on final test outcomes without disclosing the protocol change.

## Generated Files and Schema

Generate lockfiles, clients and migrations with the implemented tools. Review migrations before applying; distinguish local setup from real deployments. Generated clients follow the API schema. Never manually create a fake lockfile.

## Verification and Merge

Run relevant automated checks and substantive acceptance cases. Review material domain changes with the responsible teammate. Repository permissions/merge policy will be configured separately; this document does not invent a required number of approvals or authorize external publication.

## Documentation

Update intended behaviour and actual implementation status separately. Significant choices receive a decision record; routine implementation details stay with code/specification. Do not copy the same rule across several files.
