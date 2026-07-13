# API Authentication

Northwind Cloud's API supports two authentication methods: API keys and OAuth 2.0.

API keys are the simplest method and are recommended for server-to-server integrations. Every account has two API keys: a live key (prefixed `sk_live_`) and a test key (prefixed `sk_test_`) that operates against the sandbox environment described in `sandbox-environment.md`. Keys are passed via the `Authorization: Bearer <key>` header on every request. API keys never expire automatically, but they can be rotated at any time from the dashboard; rotating a key invalidates the old one after a 24-hour grace period to allow in-flight deployments to pick up the new value.

OAuth 2.0 is required for any integration that acts on behalf of an end user, such as third-party apps listed in the Northwind Cloud marketplace. Northwind Cloud supports the authorization code grant with PKCE. Access tokens are valid for 1 hour and refresh tokens are valid for 90 days of inactivity. SSO/SAML, covered in `sso-saml.md`, is a separate mechanism used for authenticating human users into the Northwind Cloud dashboard itself, not for API requests.

All authentication failures return a `401 Unauthorized` error with a machine-readable `error_code` field; see `error-codes.md` for the full list of codes. Requests without any authentication header are rejected before rate limiting is applied, so unauthenticated requests do not count against the quotas described in `rate-limits.md`.
