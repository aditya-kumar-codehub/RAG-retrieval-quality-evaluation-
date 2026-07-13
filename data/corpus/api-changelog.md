# API Changelog

**v2 launch** — Introduced `/v2` as described in `api-versioning.md`. Renamed the `cust_id` field to `customer_id` across all endpoints for consistency. Deprecated the `legacy_status` field on the customer object in favor of the new `lifecycle_stage` enum.

**Bulk export improvements** — Added CSV as an export format alongside JSON on the `/v2/exports` endpoint (see `data-export.md`). Export jobs now emit an `export.completed` webhook event instead of requiring polling.

**Audit log API** — Added the `/v2/audit-logs` endpoint for Enterprise accounts, described fully in `audit-logs.md`. Previously, audit log data was only viewable in the dashboard.

**Custom domain support** — Added custom domain configuration for Pro and Enterprise tiers, described in `custom-domains.md`. Custom domains were previously an Enterprise-only feature during an earlier beta period; this release expanded availability to Pro.

**Rate limit header changes** — Standardized rate-limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) across all endpoints, replacing several inconsistent legacy header names used in `v1`. See `rate-limits.md` for current header behavior.

Older entries prior to the `v2` launch are archived and available on request from support.
