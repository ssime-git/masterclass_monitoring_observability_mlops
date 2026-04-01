from __future__ import annotations

from fastapi.testclient import TestClient

from services.model_service.app import app


def test_model_metrics_endpoint_exposes_prometheus_payload() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "masterclass_predictions_total" in response.text
