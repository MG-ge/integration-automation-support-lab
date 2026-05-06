# Case 002: Failed Webhook Is Visible In Failed Jobs

## Scenario

An order webhook is accepted but the simulated downstream processing fails.

## Check

Create a webhook with:

```json
{
  "simulate_failure": true
}
```

Then inspect:

```bash
curl -s "http://127.0.0.1:8040/jobs?status=failed" | python -m json.tool
```

## Expected Result

The failed job is visible with:

- `status=failed`
- `attempts=1`
- `last_error=Simulated downstream failure.`

## Support Explanation

The webhook failure is visible through the jobs API, so support can identify the failing job and document the next retry or escalation step.
