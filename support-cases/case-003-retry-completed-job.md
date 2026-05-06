# Case 003: Retry Blocked For Completed Job

## Scenario

A user tries to retry a job that has already completed.

## Check

Create a successful webhook, then call:

```bash
curl -s -X POST http://127.0.0.1:8040/jobs/1/retry | python -m json.tool
```

## Expected Result

The API returns `409` and explains that only failed jobs can be retried.

## Support Explanation

The retry is blocked because retrying completed work could create duplicate downstream actions. Only failed jobs are eligible for manual retry in this lab.
