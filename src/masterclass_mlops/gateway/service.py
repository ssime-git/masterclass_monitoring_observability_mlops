from __future__ import annotations

from collections.abc import Sequence

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from masterclass_mlops.config import Settings
from masterclass_mlops.metrics import ACTIVE_SESSIONS, PREDICTIONS_TOTAL
from masterclass_mlops.models import SessionRecord, User
from masterclass_mlops.repositories import PredictionRepository, SessionRepository, UserRepository
from masterclass_mlops.schemas import (
    HistoryItem,
    LoginRequest,
    LoginResponse,
    ModelPredictionResponse,
)
from masterclass_mlops.security import expires_at_from_now, generate_session_token, hash_password


def authenticate_user(db_session: Session, request: LoginRequest, settings: Settings) -> User:
    user = UserRepository(db_session).get_by_username(request.username)
    expected_hash = hash_password(request.password, settings.password_salt)
    if user is None or user.password_hash != expected_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def create_login_response(db_session: Session, user: User, settings: Settings) -> LoginResponse:
    session_repository = SessionRepository(db_session)
    expires_at = expires_at_from_now(settings.session_ttl_minutes)
    session_record = session_repository.create(
        token=generate_session_token(),
        user_id=user.id,
        expires_at=expires_at,
    )
    ACTIVE_SESSIONS.labels(service=settings.app_name).set(session_repository.count_active())
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
    try:
        response = await client.post(
            f"{settings.model_service_url}/predict",
            json={"text": text},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Model service is unavailable",
        ) from exc
    return ModelPredictionResponse.model_validate(response.json())


def record_prediction(
    db_session: Session,
    session_record: SessionRecord,
    text: str,
    result: ModelPredictionResponse,
    settings: Settings,
) -> Sequence[HistoryItem]:
    repository = PredictionRepository(db_session)
    repository.create(
        session_id=session_record.id,
        text=text,
        predicted_label=result.label,
        confidence=result.confidence,
    )
    PREDICTIONS_TOTAL.labels(service=settings.app_name, label=result.label).inc()
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
    repository = SessionRepository(db_session)
    repository.delete_by_token(token)
    ACTIVE_SESSIONS.labels(service=settings.app_name).set(repository.count_active())
