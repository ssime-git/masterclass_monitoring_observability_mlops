from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from services.gateway.app import app
from shared.bootstrap import initialize_database, seed_demo_users
from shared.config import Settings
from shared.database import build_session_factory


class MockModelTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "label": "billing",
                "confidence": 0.91,
                "processing_time_ms": 11.5,
            },
        )


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="gateway",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        model_service_url="http://mocked-model",
        session_ttl_minutes=90,
        password_salt="test-salt",
    )


@pytest.fixture
def client(settings: Settings) -> Generator[TestClient, None, None]:
    session_factory = build_session_factory(settings)
    initialize_database(session_factory.kw["bind"])
    with session_factory() as db_session:
        seed_demo_users(db_session, settings)

    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.http_client = httpx.AsyncClient(transport=MockModelTransport())
    with TestClient(app) as test_client:
        yield test_client
    asyncio.run(app.state.http_client.aclose())
