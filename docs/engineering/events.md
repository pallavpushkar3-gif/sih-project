# Application Events

Status: PostgreSQL-backed job-event replay implemented for the local demonstrator; retention-gap resync and confirmed-prefix ordering are implemented; automatic retention, record scoping and non-job material event families remain pending.

## Purpose

SSE provides one-way progress/material updates. PostgreSQL/job/result retrieval remains authoritative; event delivery is not proof of completion.

## Event Envelope

The implemented job envelope contains `event_id`, `type`, `occurred_at` and the bounded outbox payload with job identity, kind, state and attempt. Stable names currently include queued, running, requeued, cancellation-requested, cancelled, failed and succeeded job states. Assessment, alert, plan and inventory event families remain to be added.

## Delivery and Access

Subscriptions use the same authenticated actor as ordinary routes; production sessions are revalidated every fifteen seconds and an expired/disabled session receives `auth.required` before closure. Explicit demo mode remains available only outside production. It replays confirmed outbox rows after integer `Last-Event-ID`; the browser relies on native EventSource cursor handling and invalidates authoritative job/plan/run/inventory/arrival/alert queries. Planning and scenario screens submit durable jobs and display authoritative attempts/results; a two-second job-query poll is a fallback when stream delivery is delayed. Confirmed-prefix replay stops at the first pending event so parallel publication cannot skip lower IDs. Cursors before retained history, above current history or against empty history receive `resync`; browsers refetch authoritative state. Automatic bounded-retention pruning remains unimplemented. Do not stream unauthorized provenance or private payloads.

## Progress

Progress is optional/indeterminate unless measured. Throttle high-frequency updates and keep payloads bounded. Emit terminal availability only after durable result registration. Proxy configuration must permit streaming and heartbeats.

## Interface Handling

Events invalidate/refetch relevant query data; they should not create independent unvalidated replicas of approved plans. Keep old-view results from replacing a newer selection. Test duplicate/disconnect/replay and access filtering.
