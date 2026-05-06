# Integration Automation Support Lab

**What this proves.** `Idempotency-Key` handling on a webhook endpoint, duplicate-delivery detection, failed-job visibility via `/jobs?status=failed`, a manual retry endpoint, and a support runbook — the exact loop a Technical Customer Solutions / Integration Support role investigates daily.

**30-second tour.**

```bash
git clone https://github.com/MG-ge/integration-automation-support-lab && cd integration-automation-support-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest
PORT=8040 scripts/run-dev.sh

# in another terminal — first delivery:
curl -s -X POST http://127.0.0.1:8040/webhooks/order \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1001-created" \
  -d '{"external_order_id":"order-1001","customer_email":"x@example.com","amount_cents":1990}'
# {"status":"created", ...}

# replay with the same Idempotency-Key:
curl -s -X POST http://127.0.0.1:8040/webhooks/order \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1001-created" \
  -d '{"external_order_id":"order-1001","customer_email":"x@example.com","amount_cents":1990}'
# {"status":"duplicate", ...}  no second job is created.
```

**Status:** v1 complete · `pytest` green · local SQLite-backed lab, no real payment/logistics integration.

---

Project 4 in the career lab.

This is a local portfolio lab for junior integration support, SaaS technical support, application support, API support, technical customer solutions, and junior implementation-adjacent roles.

This is not production experience. It is a hands-on learning project that simulates webhook intake, idempotency, failed-job visibility, retry handling, API troubleshooting, and support documentation.

## What It Demonstrates

- FastAPI webhook endpoint
- `Idempotency-Key` handling
- SQLite event and job storage
- duplicate webhook detection
- failed integration-job visibility
- manual retry endpoint and script
- pytest coverage
- curl-friendly API checks
- support cases and runbook documentation
- honest known limitations and AI usage notes

## Target Roles

- Technical Customer Solutions Specialist
- Junior Integration Support Specialist
- SaaS Technical Support Specialist
- Application Support Specialist
- API Support Engineer
- Junior Technical Consultant
- Implementation Specialist, junior level

## Tech Stack

- Python
- FastAPI
- SQLite
- pytest
- curl
- shell scripts

No queue, Redis, Celery, Kubernetes, frontend, cloud deployment, or paid monitoring tool is included in this version.

## Run Locally

From the project folder:

```bash
cd /Users/mg/Desktop/Dreams/career-lab-2026/integration-automation-support-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
PORT=8040 scripts/run-dev.sh
```

In another terminal:

```bash
curl -s http://127.0.0.1:8040/health | python -m json.tool
```

## Webhook Demo

Send a successful webhook:

```bash
curl -s -X POST http://127.0.0.1:8040/webhooks/order \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1001-created" \
  -d '{
    "external_order_id": "order-1001",
    "customer_email": "customer@example.com",
    "amount_cents": 1990
  }' | python -m json.tool
```

Send the same webhook again with the same `Idempotency-Key`. The API returns `duplicate` and does not create a second job.

Create a simulated failed integration job:

```bash
curl -s -X POST http://127.0.0.1:8040/webhooks/order \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1002-failed" \
  -d '{
    "external_order_id": "order-1002",
    "customer_email": "customer@example.com",
    "amount_cents": 2990,
    "simulate_failure": true
  }' | python -m json.tool
```

Inspect failed jobs:

```bash
curl -s "http://127.0.0.1:8040/jobs?status=failed" | python -m json.tool
```

Retry a failed job:

```bash
scripts/retry-failed-job.sh 1
```

## API Summary

- `GET /health`
- `POST /webhooks/order`
- `GET /jobs`
- `GET /jobs?status=failed`
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/retry`

Open FastAPI docs while the server is running:

```bash
open http://127.0.0.1:8040/docs
```

## Support Documentation

- [Integration support runbook](runbooks/integration-support-runbook.md)
- [Support cases](support-cases/README.md)
- [Known limitations](docs/known-limitations.md)
- [AI usage note](docs/ai-usage-note.md)
- [Project plan](docs/project-plan.md)

## Not In Scope

- real payment, logistics, or customer systems
- production webhook security
- OAuth or complex authentication
- async queues or background workers
- Redis, Celery, Kafka, Kubernetes, or microservices
- paid observability tools
- real cloud deployment
- production integration ownership claims
