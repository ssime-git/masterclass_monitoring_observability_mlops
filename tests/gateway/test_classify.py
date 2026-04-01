from __future__ import annotations


def test_classify_requires_authentication(client) -> None:
    response = client.post("/api/classify", json={"text": "payment refund for my subscription"})

    assert response.status_code == 401


def test_classify_returns_history(client) -> None:
    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "mlops-demo"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/classify",
        json={"text": "payment refund for my subscription"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["label"] == "billing"
    assert len(payload["history"]) == 1


def test_sessions_are_isolated(client) -> None:
    alice_token = client.post(
        "/auth/login",
        json={"username": "alice", "password": "mlops-demo"},
    ).json()["access_token"]
    bob_token = client.post(
        "/auth/login",
        json={"username": "bob", "password": "mlops-demo"},
    ).json()["access_token"]

    client.post(
        "/api/classify",
        json={"text": "payment refund for my subscription"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    bob_response = client.post(
        "/api/classify",
        json={"text": "login issue after password reset"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    assert bob_response.status_code == 200
    assert len(bob_response.json()["history"]) == 1
