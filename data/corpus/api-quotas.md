# Per-Endpoint API Quotas

In addition to the overall per-minute rate limit described in `rate-limits.md`, several computationally expensive endpoints have their own stricter quotas that apply regardless of tier:

- **Bulk data export** (`POST /v2/exports`, see `data-export.md`): limited to 10 requests per hour, per account, on every tier including Enterprise.
- **Report generation** (`POST /v2/reports`): limited to 20 requests per hour.
- **Webhook redelivery** (`POST /v2/webhooks/{id}/redeliver`): limited to 50 requests per hour.

These quotas exist independently of your account's general rate limit because the underlying operations consume disproportionate compute relative to a typical read request, and unrestricted concurrent usage could degrade the platform for other customers. Exceeding a per-endpoint quota returns the same `429 rate_limited` error code described in `error-codes.md`, with a `quota_type` field in the response body distinguishing it from a general rate-limit violation.

Enterprise customers who need a higher per-endpoint quota for a specific use case (for example, frequent large data exports) can request a custom quota increase through their account manager; this is negotiated separately from the general custom rate limit mentioned in `rate-limits.md`.
