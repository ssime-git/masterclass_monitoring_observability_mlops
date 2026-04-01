from __future__ import annotations


def test_gateway_responses_include_request_id(client) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "mlops-demo"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
