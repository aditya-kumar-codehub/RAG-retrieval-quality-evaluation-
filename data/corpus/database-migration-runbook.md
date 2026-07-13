# Database Migration Runbook

All schema migrations must be backwards-compatible with the previous application version for at least one full deploy cycle, so that a rollback (per `rollback-procedure.md`) never leaves the database in a state the previous code version cannot handle. This means migrations are applied in two phases: an additive phase (new columns, tables, or indexes, all nullable or defaulted) deployed and verified first, followed by a cleanup phase (dropping old columns) only after the new code path has been running successfully in production for at least 7 days.

Migrations are applied automatically as part of the CI/CD pipeline described in `deployment-process.md`, but any migration expected to lock a table for more than 1 second on production-sized data requires manual review and typically runs during the lowest-traffic window, currently 3:00-5:00 AM UTC.

Large backfills (updating millions of existing rows) are run as a separate, throttled background job rather than inline in the migration itself, to avoid replication lag that could trigger alerting thresholds described in `monitoring-alerting.md`.

Every production database has continuous backups with point-in-time recovery, which feed into the disaster recovery plan in `disaster-recovery.md`. Before running any migration expected to be destructive (a data-losing column drop, for example), the on-call engineer confirms a recent verified backup exists.
