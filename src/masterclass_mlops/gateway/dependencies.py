from __future__ import annotations

import logging
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from opentelemetry import trace
from sqlalchemy.orm import Session

from masterclass_mlops.models import SessionRecord
from masterclass_mlops.observability import update_request_context
from masterclass_mlops.repositories import SessionRepository

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def get_db_session(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_current_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db_session: Session = Depends(get_db_session),
) -> SessionRecord:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    repository = SessionRepository(db_session)
    with tracer.start_as_current_span("gateway.session_lookup"):
        session_record = repository.get_by_token(credentials.credentials)
    if session_record is None:
        logger.warning("session_lookup_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    update_request_context(user_id=str(session_record.user_id), session_id=str(session_record.id))
    request.state.session_token = credentials.credentials
    return session_record
