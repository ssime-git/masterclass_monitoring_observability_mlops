from __future__ import annotations

import logging
from collections.abc import Sequence

import httpx
from fastapi import HTTPException, status
from opentelemetry import propagate, trace
from sqlalchemy.orm import Session

from shared.config import Settings
from shared.metrics import ACTIVE_SESSIONS, PREDICTIONS_TOTAL
from shared.models import SessionRecord, User
from shared.observability import get_request_context
from shared.repositories import PredictionRepository, SessionRepository, UserRepository
from shared.schemas import (
    HistoryItem,
    LoginRequest,
    LoginResponse,
    ModelPredictionResponse,
)
from shared.security import expires_at_from_now, generate_session_token, hash_password

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def authenticate_user(db_session: Session, request: LoginRequest, settings: Settings) -> User:
    with tracer.start_as_current_span("gateway.authenticate_user"):
        user = UserRepository(db_session).get_by_username(request.username)
        expected_hash = hash_password(request.password, settings.password_salt)
        if user is None or user.password_hash != expected_hash:
            logger.warning("authentication_failed", extra={"username": request.username})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        logger.info(
            "authentication_succeeded",
            extra={"username": user.username, "user_id": user.id},
        )
        return user


def create_login_response(db_session: Session, user: User, settings: Settings) -> LoginResponse:
    with tracer.start_as_current_span("gateway.create_session"):
        session_repository = SessionRepository(db_session)
        expires_at = expires_at_from_now(settings.session_ttl_minutes)
        session_record = session_repository.create(
            token=generate_session_token(),
            user_id=user.id,
            expires_at=expires_at,
        )
        ACTIVE_SESSIONS.labels(service=settings.app_name).set(session_repository.count_active())
        logger.info(
            "session_created",
            extra={"username": user.username, "user_id": user.id, "session_id": session_record.id},
        )
        return LoginResponse(
            access_token=session_record.token,
            username=user.username,
            expires_at=session_record.expires_at,
        )


async def request_prediction(
    client: httpx.AsyncClient,
    settings: Settings,
    text: str,
) -> ModelPredictionResponse:
    context = get_request_context()
    headers: dict[str, str] = {}
    propagate.inject(headers)
    request_id = context.get("request_id")
    if request_id is not None:
        headers["X-Request-ID"] = request_id
    if "user_id" in context:
        headers["X-User-ID"] = context["user_id"]
    if "session_id" in context:
        headers["X-Session-ID"] = context["session_id"]
    with tracer.start_as_current_span("gateway.forward_prediction"):
        try:
            response = await client.post(
                f"{settings.model_service_url}/predict",
                json={"text": text},
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("model_service_unavailable")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Model service is unavailable",
            ) from exc
        logger.info("model_service_response_received")
        return ModelPredictionResponse.model_validate(response.json())


def record_prediction(
    db_session: Session,
    session_record: SessionRecord,
    text: str,
    result: ModelPredictionResponse,
    settings: Settings,
) -> Sequence[HistoryItem]:
    with tracer.start_as_current_span("gateway.store_prediction_history"):
        repository = PredictionRepository(db_session)
        repository.create(
            session_id=session_record.id,
            text=text,
            predicted_label=result.label,
            confidence=result.confidence,
        )
        PREDICTIONS_TOTAL.labels(service=settings.app_name, label=result.label).inc()
        logger.info(
            "prediction_recorded",
            extra={
                "label": result.label,
                "confidence": result.confidence,
                "session_id": session_record.id,
            },
        )
        return [
            HistoryItem(
                text=item.text,
                predicted_label=item.predicted_label,
                confidence=item.confidence,
                created_at=item.created_at,
            )
            for item in repository.list_recent_for_session(session_record.id)
        ]


def logout(db_session: Session, token: str, settings: Settings) -> None:
    with tracer.start_as_current_span("gateway.delete_session"):
        repository = SessionRepository(db_session)
        repository.delete_by_token(token)
        ACTIVE_SESSIONS.labels(service=settings.app_name).set(repository.count_active())
        logger.info("session_deleted")
