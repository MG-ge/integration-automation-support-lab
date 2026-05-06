# Case 001: Duplicate Webhook Does Not Create Duplicate Job

## Scenario

A sender retries the same order webhook because it did not receive the first response clearly.

## Check

Send the same payload twice with the same `Idempotency-Key`.

Expected result:

- first request creates one job
- second request returns `status=duplicate`
- `/jobs` still shows one job

## Support Explanation

The duplicate webhook was handled safely because the same idempotency key was reused. No duplicate integration job was created.

## Next Action

Tell the sender to reuse the same idempotency key for retries of the same event.
