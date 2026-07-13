# Postmortem Process

A written postmortem is required within 5 business days of resolution for every SEV1 and SEV2 incident, as stated in `incident-response.md`. The postmortem owner is, by default, the engineer who was primary on-call when the incident was declared, though ownership can be reassigned by the engineering lead if a different engineer has more context.

Postmortems follow a blameless format: the goal is to identify systemic and process gaps, not individual fault. The standard template includes a timeline of events, root cause analysis, customer impact assessment, and a list of concrete action items, each with an assigned owner and a due date.

Completed postmortems are reviewed in a weekly postmortem review meeting attended by engineering leadership, and are stored in a searchable internal wiki so patterns across incidents can be identified over time. Action items are tracked to completion in the same ticketing system used for regular engineering work, and are audited monthly for overdue items.

If an incident involved customer data loss or exposure, the postmortem is additionally shared with the legal and security teams, and may inform updates to the disaster recovery plan described in `disaster-recovery.md`.
