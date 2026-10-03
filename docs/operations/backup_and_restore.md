# Backup and Restore

## Data to Preserve

PostgreSQL operational history/job state, registered artifact bytes/manifests, immutable split versions, permitted source references and deployment configuration metadata. Store actual secrets through the appropriate protected mechanism, not ordinary research archives.

## Consistency

Database and artifact snapshots must preserve resolvable references. Document the point-in-time boundary and any pause/reconciliation needed. Broker messages are dispatch signals; database job state remains authoritative. Do not equate copying a database with preserving trained models.

## Restore Procedure

Restore into an isolated environment; verify schema/version, artifact hashes and relationships; reconcile incomplete/orphaned jobs; establish compatible code/configuration; recover eligible attempts under the job policy. Verify representative record retrieval, assessment/evidence linkage and reservations before treating the restore as usable.

## Verification

Retain an actual restore record with revisions, manifests and outcomes. Retention schedule, storage location, recovery budgets and encryption are deployment decisions pending actual requirements. Do not claim a recovery time without measuring it.
