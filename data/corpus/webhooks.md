# Webhooks

Webhooks let your application receive real-time notifications when events happen in your Northwind Cloud account. Configure a webhook endpoint URL from the dashboard, and Northwind Cloud will POST a JSON payload to it whenever a subscribed event occurs.

Common event types include `invoice.paid`, `invoice.payment_failed`, `usage.threshold_exceeded`, `export.completed` (see `data-export.md`), and `api_key.rotated`. The full event catalog is listed in the dashboard's webhook settings page.

Every webhook payload is signed using HMAC-SHA256 with a per-endpoint shared secret, sent in the `X-Northwind-Signature` header. Verify this signature before processing the payload to ensure the request genuinely originated from Northwind Cloud.

If your endpoint does not return a `2xx` status code, Northwind Cloud retries delivery on a backoff schedule: 1 minute, 5 minutes, 15 minutes, 1 hour, and 6 hours, for a total of 5 retry attempts. After the final attempt fails, the event is marked as failed and is visible in the dashboard's webhook delivery log, where it can be manually redelivered. If your endpoint responds with `429 Too Many Requests`, Northwind Cloud honors any `Retry-After` header you return, similar in spirit to the backoff behavior your own client should use against the Northwind Cloud API as described in `rate-limits.md` — though webhook retries themselves are not subject to your account's API rate limit.
