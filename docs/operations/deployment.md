# Deployment

Status: intended single-host demonstrator topology; no deployment performed.

## Components

Serve the built frontend through a reverse proxy; route API requests and SSE to FastAPI. Run PostgreSQL, RabbitMQ, an outbox dispatcher and Celery worker pools with persistent storage. Model/artifact access is through the controlled application/storage interface.

## Configuration

Pin images/dependencies, supply secrets through deployment configuration and set CPU/GPU/concurrency deliberately. Configure TLS/browser session protection, stream buffering/timeouts, health/readiness and storage permissions. Bundle permitted dataset/model assets required for a local demonstration; external inference APIs are not required.

## Release Procedure

Build/test the exact revision, retain artifact manifests, back up current state, apply reviewed migrations under the agreed procedure and verify principal workflows. Define rollback/schema compatibility before a real deployment. Demonstrator authentication/configuration must not be represented as production certification.

## Limits

Compose does not supply automatic failover or clustered reliability. Multi-host scale, private telemetry, organizational identity integration and production hosting require established requirements and authorization. Do not publish or deploy simply because this document exists.
