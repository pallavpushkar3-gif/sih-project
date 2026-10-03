# ADR 0003 — Durable Jobs and Accepted Results

Status: accepted design, implementation pending.

## Context

Predictions, optimization and simulations can outlive a web request. Broker delivery, database writes and artifact storage do not form one transaction.

## Decision

Use PostgreSQL job/attempt state and an outbox, Celery/RabbitMQ dispatch, separate workers and conditional result acceptance. Expect duplicate delivery. Persist artifacts/result state before success events. Use idempotency and current-attempt checks for accepted effects.

## Alternatives

In-process tasks are inadequate as the durable long-computation foundation. Redis is a credible broker alternative. A database-only queue would require explicit leasing/retry machinery. A replay-stream platform has no established role in current dispatch.

## Consequences

No exactly-once execution claim. Cancellation/retry races and orphaned artifacts need explicit rules and tests. Shared scientific/application packages avoid duplicated business logic across processes.

## Validation/Revisit

Interrupt dispatch/API/workers; repeat messages; cancel during completion; submit stale results. Confirm authoritative state and no duplicated material commitments. Revisit messaging topology only for demonstrated requirements.
