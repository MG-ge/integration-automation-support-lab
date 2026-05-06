#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8040}"

uvicorn src.main:app --reload --host 127.0.0.1 --port "$PORT"
