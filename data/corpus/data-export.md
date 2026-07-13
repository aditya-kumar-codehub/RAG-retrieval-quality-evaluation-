# Data Export

Account data can be exported in JSON or CSV format via the `/v2/exports` endpoint. Exports are asynchronous: creating an export job returns immediately with a job ID, and Northwind Cloud processes the export in the background, emitting an `export.completed` webhook event (see `webhooks.md`) when the file is ready.

Completed export files are available for download for 24 hours via a signed URL; after that window, the file is deleted and a new export must be requested. Exports respect the data retention window described in `data-retention.md` — you cannot export data that has already been purged.

The export endpoint is subject to a stricter quota than general API traffic; see `api-quotas.md` for the exact limit. This is because export jobs are computationally expensive and generating too many concurrently can degrade performance for other customers sharing the same infrastructure.

Enterprise customers with a signed Data Processing Agreement (see `data-processing-agreement.md`) can additionally request a full account data export for compliance purposes, which includes audit log history beyond what's available through the standard export endpoint.
