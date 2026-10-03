# ADR 0002 — Operational Records and Artifact Storage

Status: accepted design, implementation pending.

## Context

Approvals, reservations and provenance require transactional relationships. Numerical arrays, weights and traces may be large and immutable. One storage form need not serve both workloads.

## Decision

Use PostgreSQL for operational records/versions and an artifact interface for large immutable bytes. Initially use a persistent mounted directory with hashes/manifests; register usable references after durable storage. Keep split versions even when excluded from Git. Archive database and artifact references coherently.

## Alternatives

MongoDB is credible but less direct for the chosen relational reservation model. SQLite suits embedded use. DuckDB may complement research analytics. A separate time-series store/object-storage service is deferred until measured needs justify it.

## Consequences

Cross-store atomicity is not automatic. Reconcile incomplete/orphaned bytes and keep registered references immutable/resolvable. Queries and storage thresholds require workload measurement.

## Validation/Revisit

Verify traceability, concurrent reservations, correction history, artifact integrity and a representative restore. Revisit storage implementation for multi-host access, retention or measured analytical/ingestion pressure.
