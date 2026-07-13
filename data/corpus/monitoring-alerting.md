# Monitoring and Alerting

Northwind Cloud uses Datadog for metrics, logs, and dashboards, and PagerDuty for alert routing and on-call paging, integrated with the rotation described in `on-call-rotation.md`. Every production service emits standard metrics for request rate, error rate, and latency (p50, p95, p99).

Default alert thresholds are: p99 latency above 500ms for 5 consecutive minutes, error rate above 1% for 5 consecutive minutes, or any 5xx spike exceeding 50 errors per minute. Crossing any of these thresholds pages the on-call engineer directly and, if sustained for more than 15 minutes without acknowledgment, auto-escalates per the process in `incident-response.md`.

Database replication lag is monitored separately, with a warning threshold at 10 seconds and a paging threshold at 60 seconds, since sustained lag can affect the correctness of the read replicas used by reporting and export features (`data-export.md`). Large backfill jobs described in `database-migration-runbook.md` are explicitly throttled to avoid crossing this threshold.

Dashboards are reviewed weekly in an engineering sync to catch slow degradations that don't cross an alerting threshold but represent a negative trend, such as gradually increasing baseline latency.
