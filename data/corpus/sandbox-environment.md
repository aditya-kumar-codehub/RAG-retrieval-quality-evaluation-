# Sandbox Environment

Northwind Cloud provides a sandbox environment at `https://sandbox.northwindcloud.com` for testing integrations without affecting production data or incurring real charges. The sandbox is available on every pricing tier, including Free.

Sandbox requests use test API keys, which are prefixed `sk_test_` as opposed to the `sk_live_` prefix used in production, per `authentication.md`. Test keys only work against the sandbox host; using a test key against the production API host returns a `403 forbidden` error.

The sandbox database is reset every Sunday at 00:00 UTC, wiping all test data created during the week. This is by design, to keep the sandbox environment lightweight and prevent it from accumulating stale test fixtures — do not rely on sandbox data persisting across weeks.

Webhooks (see `webhooks.md`) fire normally in the sandbox, making it suitable for end-to-end integration testing of webhook handlers. Rate limits in the sandbox are fixed at 60 requests per minute regardless of your account's production tier, matching the Free tier limit described in `rate-limits.md`.
