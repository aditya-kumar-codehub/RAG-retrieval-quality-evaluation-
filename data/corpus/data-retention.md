# Data Retention

Data retention periods vary by pricing tier, as summarized in `pricing-tiers.md`:

- Free and Starter tiers: 30 days
- Pro tier: 90 days
- Enterprise tier: configurable, from 30 days up to 7 years, set per contract

After the retention window elapses, raw event and request data is permanently deleted from primary storage. Aggregated usage metrics (used for billing purposes) are retained indefinitely regardless of tier, since they are required for historical invoicing records.

Enterprise customers with compliance requirements (GDPR, SOC 2, etc.) should review the Data Processing Agreement described in `data-processing-agreement.md`, which governs how retention periods interact with data subject deletion requests. A deletion request under GDPR takes precedence over the standard retention window and is processed within 30 days regardless of tier.

Audit logs, described in `audit-logs.md`, are retained separately from general account data and follow the same tier-based retention window unless a custom audit log retention period is negotiated as part of an Enterprise contract. Data can be exported prior to deletion using the export tooling described in `data-export.md`.
