# API Rate Limits

Rate limits are enforced per API key and vary by pricing tier, as defined in `pricing-tiers.md`:

- Free tier: 60 requests per minute
- Starter tier: 300 requests per minute
- Pro tier: 1,500 requests per minute
- Enterprise tier: custom limits negotiated per contract, typically starting at 10,000 requests per minute

Every response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers so callers can track their usage without guessing. When a caller exceeds their limit, the API returns `429 Too Many Requests` with a `Retry-After` header indicating the number of seconds to wait before retrying.

Northwind Cloud recommends implementing exponential backoff with jitter: start with a 1-second delay and double it on each subsequent 429, capping at 60 seconds. Do not retry immediately in a tight loop, as repeated immediate retries can trigger a temporary IP-level block independent of the per-key rate limit.

Rate limits apply to the general request budget. Certain expensive endpoints have additional, stricter per-endpoint quotas layered on top — see `api-quotas.md` for details, particularly around the bulk data export endpoint. Webhook delivery retries (see `webhooks.md`) are exempt from your outbound rate limit since they originate from Northwind Cloud's infrastructure, not your API key.
