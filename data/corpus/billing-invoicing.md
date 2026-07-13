# Billing and Invoicing

Northwind Cloud bills on a monthly cycle, on the same calendar day each month that the account was created (the "billing anniversary"). Invoices are generated on the billing anniversary and are due net-15 — payment is expected within 15 days of the invoice date.

Paid tiers (Starter, Pro, Enterprise, per `pricing-tiers.md`) are billed via credit card by default; Enterprise customers may arrange invoiced payment via bank transfer as part of their contract. Usage overage charges (for exceeding the included API call volume) are calculated at the end of the billing cycle and appear as a line item on the next invoice, not billed in real time.

If a payment fails, Northwind Cloud retries the charge up to 3 times over 7 days. If all 3 attempts fail, the account enters a grace period of an additional 7 days during which service continues uninterrupted but a payment warning banner is shown in the dashboard. If payment is still not received after the grace period, the account is automatically downgraded to the Free tier, and any tier-specific features (SSO, custom domains, audit logs) are disabled until payment is resolved and the account is manually upgraded again.

Downgrading due to non-payment does not delete any data; data retention continues to follow whatever window applied at the time it was ingested, per `data-retention.md`.
