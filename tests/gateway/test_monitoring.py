from __future__ import annotations


def test_gateway_metrics_endpoint_exposes_prometheus_payload(client) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "masterclass_http_requests_total" in response.text
