# Secrets Management

All secrets used by engineering systems — database credentials, third-party API keys, signing keys used for webhooks (see `webhooks.md`) — are stored in HashiCorp Vault. Secrets must never be committed to source control, shared in chat, or stored in plaintext configuration files, per the general security requirements in `security-policy.md`.

Secrets are rotated automatically every 90 days for supported integrations, and rotation is manually triggered immediately for any secret suspected of exposure, regardless of the normal schedule. Applications fetch secrets from Vault at startup and cache them in memory only; secrets are never written to disk on application servers.

Access to Vault is granted per-service via short-lived tokens issued through the CI/CD pipeline (see `deployment-process.md`); individual engineers do not have standing access to production secrets and instead use a break-glass procedure requiring approval from the on-call engineering lead, which is fully logged and reviewed weekly, similar in spirit to the access review process in `access-control-runbook.md`.

Feature flags that gate sensitive functionality (per `deployment-process.md`) are configured through a separate system from Vault, but the API keys used to modify flag state in production are themselves stored in and rotated through Vault.
