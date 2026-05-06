#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8040}"
JOB_ID="${1:-}"

if [ -z "$JOB_ID" ]; then
  echo "retry_job=fail"
  echo "reason=missing_job_id"
  echo "usage=scripts/retry-failed-job.sh <job_id>"
  exit 1
fi

curl -s -X POST "$BASE_URL/jobs/$JOB_ID/retry" | python -m json.tool
