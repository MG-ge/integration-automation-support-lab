# Known Limitations

This is a local integration-support lab, not a production integration platform.

Current limitations:

- no real webhook signature verification
- no real customer, payment, warehouse, logistics, or CRM system
- no background worker or queue
- no automatic retry schedule
- failed jobs are retried manually
- SQLite is used instead of PostgreSQL
- no authentication or authorization
- no frontend dashboard
- no cloud deployment
- no production monitoring

These limits are intentional. The project focuses on junior-level support concepts: API intake, idempotency, duplicates, failed-job visibility, retries, and runbook-style troubleshooting.
