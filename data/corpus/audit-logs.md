# Audit Logs

Audit logs record every sensitive action taken on a Northwind Cloud account: API key creation and rotation, permission changes, SSO login events, data exports, and configuration changes. Audit logs are an Enterprise-tier feature (see `pricing-tiers.md`) and are automatically enabled whenever SSO is configured, per `sso-saml.md`.

Each audit log entry records the actor (user or API key), the action taken, a timestamp, the source IP address, and a before/after diff for configuration changes. Entries are immutable once written.

Audit logs follow the same retention window as general account data, described in `data-retention.md`, unless a custom audit log retention period — up to 7 years — is negotiated separately in the Enterprise contract. This is common for customers in regulated industries who need a longer audit trail than their general data retention policy requires.

Audit log entries can be viewed in the dashboard or pulled via the `/v2/audit-logs` API endpoint, and can be included in a bulk export as described in `data-export.md`. Access to the audit log endpoint itself is a sensitive action and is, appropriately, also recorded in the audit log.
