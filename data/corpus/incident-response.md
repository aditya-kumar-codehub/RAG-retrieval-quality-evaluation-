# Incident Response

Northwind Cloud classifies incidents into four severity levels:

- **SEV1**: full platform outage or a critical security breach. Page on-call immediately.
- **SEV2**: significant degradation affecting many customers (e.g. elevated error rates, one region down).
- **SEV3**: limited-impact issue affecting a subset of customers or a non-critical feature.
- **SEV4**: minor issue with no immediate customer impact, tracked but not paged.

Any employee who identifies a potential SEV1 or SEV2 can page the on-call engineer directly through PagerDuty, per the rotation described in `on-call-rotation.md`. If the page is not acknowledged within 15 minutes, PagerDuty automatically escalates to the secondary on-call, and then to the engineering lead if still unacknowledged after another 15 minutes.

For SEV1 and SEV2 incidents, the on-call engineer posts an initial status page update within 15 minutes of declaring the incident, per `status-page.md`, and continues updating at least every 30 minutes until resolution.

A written postmortem is required within 5 business days of resolution for every SEV1 and SEV2 incident, following the template and process in `postmortem-process.md`. SEV3 and SEV4 incidents do not require a formal postmortem but should be logged in the incident tracker for trend analysis. Incidents involving data loss additionally trigger the disaster recovery plan described in `disaster-recovery.md`.
