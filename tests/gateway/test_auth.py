from __future__ import annotations


def test_login_returns_session_token(client) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "mlops-demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["username"] == "alice"


def test_login_rejects_invalid_credentials(client) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_logout_invalidates_session(client) -> None:
    token = client.post(
        "/auth/login",
        json={"username": "alice", "password": "mlops-demo"},
    ).json()["access_token"]

    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})

    response = client.post(
        "/api/classify",
        json={"text": "My payment failed and I need a refund."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
