# Project Plan

## Goal

Build a junior-friendly integration support lab that proves practical understanding of webhooks, idempotency, failed-job visibility, retries, API troubleshooting, and support documentation.

## Slices

### Slice 1: Webhook Intake

- FastAPI app
- `GET /health`
- `POST /webhooks/order`
- SQLite storage for webhook events and integration jobs
- pytest coverage

### Slice 2: Idempotency

- Require `Idempotency-Key`
- Return safe duplicate response for repeated events
- Confirm duplicate events do not create duplicate jobs

### Slice 3: Failed-Job Visibility

- Simulated downstream failure
- `GET /jobs`
- `GET /jobs?status=failed`
- `GET /jobs/{job_id}`

### Slice 4: Retry

- `POST /jobs/{job_id}/retry`
- retry script
- tests for retry behavior

### Slice 5: Support Package

- README
- runbook
- support cases
- known limitations
- AI usage note

## Rules

- Keep it local.
- Keep it junior-credible.
- Do not add queues, Kubernetes, frontend, paid tools, auth, or fake production claims.
