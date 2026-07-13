# Rollback Procedure

When a production deployment causes a regression, the fastest safe response is almost always a rollback rather than a forward-fix, per the guidance in `deployment-process.md`. Any engineer, not just the on-call engineer, can initiate a rollback, but it must be announced in the `#incidents` channel before executing.

Rollbacks are performed via the `deploy rollback <service> <version>` command in the internal deployment CLI, which reverts the service to the last known-good version recorded automatically before each deploy. A rollback typically completes within 3-5 minutes for stateless services; services with database migrations (see `database-migration-runbook.md`) require additional care, since a code rollback does not automatically reverse a schema migration, and migrations must be designed to be backwards-compatible with the previous code version for at least one deploy cycle.

After a rollback, the engineer who initiated it is responsible for opening a follow-up ticket describing the regression and linking it to the incident, if one was declared per `incident-response.md`. A rollback of a SEV1 or SEV2-triggering deploy still requires a postmortem per `postmortem-process.md`, even though the immediate customer impact has been resolved.

Rolling back does not require the original deploying engineer's approval, though they should be notified as soon as possible.
