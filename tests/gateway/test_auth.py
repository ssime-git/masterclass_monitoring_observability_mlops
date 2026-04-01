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


def test_admin_login_returns_session_token(client) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "mlops-demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["username"] == "admin"
