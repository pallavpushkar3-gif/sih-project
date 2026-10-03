# Application Events

## Purpose

SSE provides one-way progress/material updates. PostgreSQL/job/result retrieval remains authoritative; event delivery is not proof of completion.

## Event Envelope

Define `event_id`, `type`, `occurred_at`, relevant record/job identity and version, correlation ID and a small payload. Use stable event names for assessment availability, alert change, proposal availability, plan commitment, inventory change and job state/progress. Final names are generated into shared contracts once implemented.

## Delivery and Access

Authorize subscriptions and filter records by the same access rules as ordinary retrieval. Replay with `Last-Event-ID` or the implemented equivalent. Deduplicate client processing by ID/version. Define bounded retention; if the cursor cannot be resumed, emit a resync indication and refetch authoritative state. Do not stream unauthorized provenance or private payloads.

## Progress

Progress is optional/indeterminate unless measured. Throttle high-frequency updates and keep payloads bounded. Emit terminal availability only after durable result registration. Proxy configuration must permit streaming and heartbeats.

## Interface Handling

Events invalidate/refetch relevant query data; they should not create independent unvalidated replicas of approved plans. Keep old-view results from replacing a newer selection. Test duplicate/disconnect/replay and access filtering.
