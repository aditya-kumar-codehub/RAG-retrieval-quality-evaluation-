# API Error Codes

Every API error response includes an HTTP status code and a JSON body with a machine-readable `error_code` and a human-readable `message`.

| HTTP Status | error_code | Meaning |
|---|---|---|
| 400 | `invalid_request` | The request body or query parameters failed validation. |
| 401 | `unauthorized` | Missing or invalid authentication credentials — see `authentication.md`. |
| 403 | `forbidden` | Authenticated, but the API key lacks permission for this action. |
| 404 | `not_found` | The requested resource does not exist. |
| 409 | `conflict` | The request conflicts with the current state of the resource (e.g. duplicate creation). |
| 429 | `rate_limited` | The rate limit or an endpoint-specific quota was exceeded — see `rate-limits.md` and `api-quotas.md`. |
| 500 | `internal_error` | An unexpected server error. Safe to retry with backoff. |
| 503 | `service_unavailable` | Temporary overload or maintenance. Check `status-page.md` for active incidents. |

Client libraries listed in `sdks.md` automatically raise a typed exception per `error_code`, so integrators should match on `error_code` rather than parsing the `message` string, which may change wording over time without notice.
