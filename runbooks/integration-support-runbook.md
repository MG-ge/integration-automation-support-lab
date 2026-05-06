# Integration Support Runbook

Use this runbook when a webhook or integration job appears to be missing, duplicated, or failed.

## 1. Confirm The API Is Running

```bash
curl -s http://127.0.0.1:8040/health | python -m json.tool
```

Expected:

```json
{
  "status": "ok",
  "service": "Integration Automation Support Lab"
}
```

## 2. Check The Customer Report

Collect:

- approximate time of the event
- external order ID
- idempotency key
- expected result
- actual result
- any error message

## 3. Check Failed Jobs

```bash
curl -s "http://127.0.0.1:8040/jobs?status=failed" | python -m json.tool
```

Look for:

- `status`
- `attempts`
- `last_error`
- `updated_at`

## 4. Check A Specific Job

```bash
curl -s http://127.0.0.1:8040/jobs/1 | python -m json.tool
```

If the job does not exist, confirm the webhook was accepted and the idempotency key was correct.

## 5. Handle Duplicate Webhooks

If a sender retries the same webhook with the same `Idempotency-Key`, the API should return:

```text
status=duplicate
```

This is expected behavior and should not create a second job.

## 6. Retry A Failed Job

```bash
scripts/retry-failed-job.sh 1
```

If retry still fails, document:

- job ID
- attempts
- latest error
- next recommended action

## 7. Escalation Notes

Escalate when:

- the same job keeps failing after retry
- the webhook payload is invalid
- the sender cannot provide an idempotency key
- the customer impact is unclear

Do not claim production incident ownership. This is a local lab workflow.
