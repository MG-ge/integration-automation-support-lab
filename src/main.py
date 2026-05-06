import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

APP_NAME = "Integration Automation Support Lab"
DEFAULT_DB_PATH = "integration_lab.db"
IDEMPOTENCY_HEADER = "Idempotency-Key"

app = FastAPI(title=APP_NAME)


class OrderWebhook(BaseModel):
    external_order_id: str = Field(min_length=1)
    customer_email: str = Field(min_length=3)
    amount_cents: int = Field(gt=0)
    simulate_failure: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db_path() -> Path:
    return Path(os.environ.get("INTEGRATION_LAB_DB", DEFAULT_DB_PATH))


def connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS integration_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES webhook_events(id)
            )
            """
        )


def serialize_row(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def get_existing_job(idempotency_key: str) -> sqlite3.Row | None:
    init_db()
    with connect() as connection:
        return connection.execute(
            """
            SELECT
                integration_jobs.id AS job_id,
                integration_jobs.status,
                integration_jobs.attempts,
                integration_jobs.last_error,
                webhook_events.id AS event_id,
                webhook_events.idempotency_key
            FROM webhook_events
            JOIN integration_jobs ON integration_jobs.event_id = webhook_events.id
            WHERE webhook_events.idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()


def create_event_and_job(idempotency_key: str, payload: OrderWebhook) -> int:
    now = utc_now()
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO webhook_events (
                idempotency_key,
                event_type,
                payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                idempotency_key,
                "order.created",
                payload.model_dump_json(),
                now,
            ),
        )
        event_id = int(cursor.lastrowid)
        cursor = connection.execute(
            """
            INSERT INTO integration_jobs (
                event_id,
                status,
                attempts,
                last_error,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, "pending", 0, None, now, now),
        )
        return int(cursor.lastrowid)


def process_job(job_id: int) -> sqlite3.Row:
    init_db()
    with connect() as connection:
        job = connection.execute(
            """
            SELECT
                integration_jobs.id,
                integration_jobs.event_id,
                integration_jobs.attempts,
                webhook_events.payload_json
            FROM integration_jobs
            JOIN webhook_events ON webhook_events.id = integration_jobs.event_id
            WHERE integration_jobs.id = ?
            """,
            (job_id,),
        ).fetchone()

        if job is None:
            raise ValueError("job_not_found")

        payload = json.loads(job["payload_json"])
        next_attempt = int(job["attempts"]) + 1
        now = utc_now()

        if payload.get("simulate_failure"):
            connection.execute(
                """
                UPDATE integration_jobs
                SET status = ?, attempts = ?, last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    next_attempt,
                    "Simulated downstream failure.",
                    now,
                    job_id,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE integration_jobs
                SET status = ?, attempts = ?, last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                ("completed", next_attempt, None, now, job_id),
            )

        updated = connection.execute(
            """
            SELECT
                id,
                event_id,
                status,
                attempts,
                last_error,
                created_at,
                updated_at
            FROM integration_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

        if updated is None:
            raise ValueError("job_not_found")

        return updated


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@app.post("/webhooks/order")
def receive_order_webhook(
    payload: OrderWebhook,
    idempotency_key: str | None = Header(default=None, alias=IDEMPOTENCY_HEADER),
) -> JSONResponse:
    if idempotency_key is None or not idempotency_key.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Missing Idempotency-Key header.",
            },
        )

    clean_key = idempotency_key.strip()
    existing = get_existing_job(clean_key)

    if existing:
        return JSONResponse(
            status_code=200,
            content={
                "status": "duplicate",
                "message": "Webhook already accepted for this idempotency key.",
                "event_id": existing["event_id"],
                "job_id": existing["job_id"],
                "job_status": existing["status"],
                "attempts": existing["attempts"],
            },
        )

    init_db()
    job_id = create_event_and_job(clean_key, payload)
    job = process_job(job_id)

    status_code = 202 if job["status"] == "completed" else 500
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "accepted" if job["status"] == "completed" else "failed",
            "event_id": job["event_id"],
            "job_id": job["id"],
            "job_status": job["status"],
            "attempts": job["attempts"],
            "last_error": job["last_error"],
        },
    )


@app.get("/jobs")
def list_jobs(status: str | None = None) -> dict[str, list[dict[str, Any]]]:
    init_db()
    with connect() as connection:
        if status:
            rows = connection.execute(
                """
                SELECT
                    id,
                    event_id,
                    status,
                    attempts,
                    last_error,
                    created_at,
                    updated_at
                FROM integration_jobs
                WHERE status = ?
                ORDER BY id
                """,
                (status,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    id,
                    event_id,
                    status,
                    attempts,
                    last_error,
                    created_at,
                    updated_at
                FROM integration_jobs
                ORDER BY id
                """
            ).fetchall()

    return {"jobs": [serialize_row(row) for row in rows]}


@app.get("/jobs/{job_id}")
def get_job(job_id: int) -> JSONResponse:
    init_db()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                event_id,
                status,
                attempts,
                last_error,
                created_at,
                updated_at
            FROM integration_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "Job not found.",
            },
        )

    return JSONResponse(status_code=200, content=serialize_row(row))


@app.post("/jobs/{job_id}/retry")
def retry_job(job_id: int) -> JSONResponse:
    init_db()
    with connect() as connection:
        existing = connection.execute(
            "SELECT status FROM integration_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()

    if existing is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "Job not found.",
            },
        )

    if existing["status"] != "failed":
        return JSONResponse(
            status_code=409,
            content={
                "status": "error",
                "message": "Only failed jobs can be retried.",
                "job_status": existing["status"],
            },
        )

    job = process_job(job_id)
    status_code = 200 if job["status"] == "completed" else 500

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "retried",
            "job_id": job["id"],
            "job_status": job["status"],
            "attempts": job["attempts"],
            "last_error": job["last_error"],
        },
    )
