from pathlib import Path

from fastapi.testclient import TestClient

from src.main import APP_NAME, app, get_db_path


def configure_test_db(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("INTEGRATION_LAB_DB", str(tmp_path / "test.db"))


def order_payload(simulate_failure: bool = False) -> dict[str, object]:
    return {
        "external_order_id": "order-1001",
        "customer_email": "customer@example.com",
        "amount_cents": 1990,
        "simulate_failure": simulate_failure,
    }


def test_health_returns_ok(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": APP_NAME,
    }


def test_webhook_requires_idempotency_key(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/webhooks/order", json=order_payload())

    assert response.status_code == 400
    assert response.json()["message"] == "Missing Idempotency-Key header."


def test_order_webhook_creates_completed_job(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "order-1001-created"},
        json=order_payload(),
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert response.json()["job_status"] == "completed"
    assert response.json()["attempts"] == 1
    assert get_db_path().exists()


def test_duplicate_idempotency_key_does_not_create_second_job(
    monkeypatch,
    tmp_path: Path,
) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    first_response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "duplicate-check-1"},
        json=order_payload(),
    )
    second_response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "duplicate-check-1"},
        json=order_payload(),
    )
    jobs_response = client.get("/jobs")

    assert first_response.status_code == 202
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "duplicate"
    assert second_response.json()["job_id"] == first_response.json()["job_id"]
    assert len(jobs_response.json()["jobs"]) == 1


def test_failed_webhook_is_visible_in_failed_jobs(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    webhook_response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "failure-check-1"},
        json=order_payload(simulate_failure=True),
    )
    failed_jobs_response = client.get("/jobs", params={"status": "failed"})

    assert webhook_response.status_code == 500
    assert webhook_response.json()["job_status"] == "failed"
    assert failed_jobs_response.status_code == 200
    assert len(failed_jobs_response.json()["jobs"]) == 1
    assert failed_jobs_response.json()["jobs"][0]["last_error"] == (
        "Simulated downstream failure."
    )


def test_get_job_returns_404_for_unknown_job(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/jobs/999")

    assert response.status_code == 404
    assert response.json()["message"] == "Job not found."


def test_retry_only_allows_failed_jobs(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    webhook_response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "retry-conflict-1"},
        json=order_payload(),
    )
    job_id = webhook_response.json()["job_id"]

    retry_response = client.post(f"/jobs/{job_id}/retry")

    assert retry_response.status_code == 409
    assert retry_response.json()["message"] == "Only failed jobs can be retried."
    assert retry_response.json()["job_status"] == "completed"


def test_retry_failed_job_increments_attempts(monkeypatch, tmp_path: Path) -> None:
    configure_test_db(monkeypatch, tmp_path)
    client = TestClient(app)

    webhook_response = client.post(
        "/webhooks/order",
        headers={"Idempotency-Key": "retry-failed-1"},
        json=order_payload(simulate_failure=True),
    )
    job_id = webhook_response.json()["job_id"]

    retry_response = client.post(f"/jobs/{job_id}/retry")

    assert retry_response.status_code == 500
    assert retry_response.json()["status"] == "retried"
    assert retry_response.json()["job_status"] == "failed"
    assert retry_response.json()["attempts"] == 2
