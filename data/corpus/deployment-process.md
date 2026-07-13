# Deployment Process

All changes to production systems are deployed through the CI/CD pipeline; there is no mechanism for manually deploying code outside of CI, even for on-call engineers responding to an incident. Every deployment requires at least one approving code review and a passing CI test suite before it can merge to the main branch, which triggers an automatic deploy to staging.

Promotion from staging to production requires a second, explicit approval from the deploying engineer's team lead (or the on-call engineering lead for urgent hotfixes) and is gated behind feature flags for any change affecting core account, billing, or authentication flows — see `secrets-management.md` for how flag-related secrets are handled.

Northwind Cloud observes a deploy freeze every Friday after 2:00 PM in the primary engineering time zone, through the following Monday morning, except for critical hotfixes approved by the on-call engineering lead as part of the incident response process described in `incident-response.md`. This freeze exists to avoid introducing risk right before a weekend when fewer engineers are actively monitoring systems.

If a deployment causes a regression, engineers follow the rollback procedure in `rollback-procedure.md` rather than attempting a forward-fix under time pressure unless the fix is trivial and already reviewed.
