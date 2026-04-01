from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import Depends, FastAPI, Request, Response, status
from sqlalchemy.orm import Session

from masterclass_mlops.bootstrap import initialize_database, seed_demo_users
from masterclass_mlops.config import Settings, get_settings
from masterclass_mlops.database import build_session_factory
from masterclass_mlops.gateway.dependencies import get_current_session, get_db_session
from masterclass_mlops.gateway.service import (
    authenticate_user,
    create_login_response,
    logout,
    record_prediction,
    request_prediction,
)
from masterclass_mlops.metrics import ACTIVE_SESSIONS, metrics_response, record_http_metrics
from masterclass_mlops.models import SessionRecord
from masterclass_mlops.repositories import SessionRepository
from masterclass_mlops.schemas import (
    ClassifyResponse,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    PredictionRequest,
    PredictionResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = getattr(app.state, "settings", get_settings())
    session_factory = getattr(app.state, "session_factory", build_session_factory(settings))
    initialize_database(session_factory.kw["bind"])
    with session_factory() as db_session:
        seed_demo_users(db_session, settings)
        active_sessions = SessionRepository(db_session).count_active()
        ACTIVE_SESSIONS.labels(service=settings.app_name).set(active_sessions)

    app.state.settings = settings
    app.state.session_factory = session_factory

    http_client = getattr(app.state, "http_client", httpx.AsyncClient())
    created_http_client = not hasattr(app.state, "http_client")
    app.state.http_client = http_client
    try:
        yield
    finally:
        if created_http_client:
            await app.state.http_client.aclose()


app = FastAPI(title="gateway", lifespan=lifespan)


@app.middleware("http")
async def metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings: Settings = request.app.state.settings
    return await record_http_metrics(request, call_next, settings.app_name)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/metrics")
def metrics() -> Response:
    return metrics_response()


@app.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db_session: Session = Depends(get_db_session),
) -> LoginResponse:
    settings: Settings = request.app.state.settings
    user = authenticate_user(db_session, payload, settings)
    return create_login_response(db_session, user, settings)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout_view(
    request: Request,
    session_record: SessionRecord = Depends(get_current_session),
    db_session: Session = Depends(get_db_session),
) -> Response:
    del session_record
    settings: Settings = request.app.state.settings
    token = request.state.session_token
    logout(db_session, token, settings)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/classify", response_model=ClassifyResponse)
async def classify(
    payload: PredictionRequest,
    request: Request,
    session_record: SessionRecord = Depends(get_current_session),
    db_session: Session = Depends(get_db_session),
) -> ClassifyResponse:
    settings: Settings = request.app.state.settings
    result = await request_prediction(request.app.state.http_client, settings, payload.text)
    history = list(record_prediction(db_session, session_record, payload.text, result, settings))
    prediction = PredictionResponse(
        label=result.label,
        confidence=result.confidence,
        processing_time_ms=result.processing_time_ms,
    )
    return ClassifyResponse(result=prediction, history=history)


def main() -> None:
    uvicorn.run("masterclass_mlops.gateway.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
