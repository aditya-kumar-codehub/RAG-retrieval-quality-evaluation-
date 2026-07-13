# Status Page and Incident Notifications

Northwind Cloud's public status page is at `https://status.northwindcloud.com`. It displays real-time operational status for each major subsystem (API, dashboard, webhooks, billing) and a history of past incidents.

You can subscribe to status updates via email or by connecting a Slack workspace, which posts incident updates directly to a channel of your choosing. Subscriptions are configured per-user, not per-account, so each team member who wants notifications must subscribe individually.

When an internal incident is declared using the process in `incident-response.md`, the on-call engineer is responsible for posting an initial status page update within 15 minutes of declaring a SEV1 or SEV2 incident. Updates are posted at least every 30 minutes thereafter until resolution. SEV3 and SEV4 incidents are not posted to the public status page by default, since they typically have no customer-visible impact.

The status page is hosted on separate infrastructure from the main Northwind Cloud platform specifically so that it remains available even during a full platform outage.
