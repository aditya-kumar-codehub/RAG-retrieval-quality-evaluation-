# Employee Security Policy

Multi-factor authentication (MFA) is required for every employee on all company systems, including email, the HR portal, and internal engineering tools. Accounts without MFA enabled are automatically suspended after a 7-day grace period following account creation.

Passwords must be a minimum of 14 characters. Northwind Cloud does not enforce periodic password rotation (e.g. forced changes every 90 days), following current industry best practice that rotation without cause provides little security benefit and encourages weak password patterns; passwords are instead checked against known-breach databases and must be changed immediately if a match is found.

All company laptops must have full-disk encryption enabled, as described in `equipment-policy.md`. Access to internal systems is granted on a least-privilege basis and reviewed quarterly by IT, per the process in `access-control-runbook.md`.

All employees complete mandatory security and compliance training within their first 2 weeks of employment and annually thereafter, which includes a re-acknowledgment of the Code of Conduct described in `code-of-conduct.md`. Secrets used in engineering systems follow the dedicated process described in `secrets-management.md` and must never be stored in plaintext in code, chat, or documents.
