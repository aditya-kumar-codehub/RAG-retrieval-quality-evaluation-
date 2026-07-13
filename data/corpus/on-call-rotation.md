# On-Call Rotation

Engineering on-call rotates weekly, with shifts starting Monday at 10:00 AM in the on-call engineer's local time zone. Each rotation has a primary and a secondary on-call engineer; the secondary serves as the escalation path described in `incident-response.md` if the primary doesn't acknowledge a page within 15 minutes.

Engineers are compensated for on-call duty with a $200 stipend per week of primary rotation and $100 per week of secondary rotation, paid alongside the next regular payroll cycle, plus one floating comp day to be used within 30 days of the rotation ending. Being on-call does not exempt an engineer from their regular workload, but managers are expected to account for on-call interruptions when planning sprint capacity.

The on-call schedule is managed in PagerDuty and is generated automatically on a rolling 12-week basis, covering all engineers on teams that own customer-facing production systems. Engineers can swap shifts with a teammate at any time as long as the swap is reflected in PagerDuty at least 24 hours before the shift begins; last-minute swaps require the outgoing on-call engineer to remain reachable as a backup for that shift.

New engineers join the on-call rotation only after completing the incident response training covered during onboarding, described in `onboarding-checklist.md`, typically around 60-90 days after their start date.
