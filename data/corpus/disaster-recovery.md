# Disaster Recovery Plan

Northwind Cloud's disaster recovery plan targets a Recovery Time Objective (RTO) of 4 hours and a Recovery Point Objective (RPO) of 15 minutes for all customer-facing production systems. This means that in a full regional outage, service should be restored within 4 hours, and at most 15 minutes of data should be at risk of loss.

Production databases replicate continuously to a secondary AWS region, with the continuous backup and point-in-time recovery capability described in `database-migration-runbook.md` providing the underlying mechanism. A full regional failover is a manual decision made by the engineering lead in coordination with the incident commander, following the severity classification in `incident-response.md` — a regional outage is, by definition, at minimum a SEV1.

Disaster recovery drills are conducted quarterly, simulating a full regional failover in a non-production environment to validate that the documented RTO and RPO targets are actually achievable, not just theoretical. Drill results and any gaps identified are documented and tracked to resolution using the same action-item process described in `postmortem-process.md`.

Any incident that actually triggers disaster recovery procedures — as opposed to a drill — always requires a full postmortem, regardless of how quickly it was resolved.
