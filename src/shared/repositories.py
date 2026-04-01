from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.models import PredictionRecord, SessionRecord, User
from shared.security import utc_now


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.session.scalar(statement)

    def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, token: str, user_id: int, expires_at: datetime) -> SessionRecord:
        session_record = SessionRecord(token=token, user_id=user_id, expires_at=expires_at)
        self.session.add(session_record)
        self.session.commit()
        self.session.refresh(session_record)
        return session_record

    def get_by_token(self, token: str) -> SessionRecord | None:
        statement = select(SessionRecord).where(SessionRecord.token == token)
        session_record = self.session.scalar(statement)
        if session_record is None:
            return None
        if session_record.expires_at <= utc_now():
            self.session.delete(session_record)
            self.session.commit()
            return None
        return session_record

    def delete_by_token(self, token: str) -> None:
        session_record = self.get_by_token(token)
        if session_record is None:
            return
        self.session.delete(session_record)
        self.session.commit()

    def count_active(self) -> int:
        now = utc_now()
        statement = (
            select(func.count())
            .select_from(SessionRecord)
            .where(SessionRecord.expires_at > now)
        )
        return self.session.execute(statement).scalar_one()


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        session_id: int,
        text: str,
        predicted_label: str,
        confidence: float,
    ) -> PredictionRecord:
        prediction = PredictionRecord(
            session_id=session_id,
            text=text,
            predicted_label=predicted_label,
            confidence=confidence,
        )
        self.session.add(prediction)
        self.session.commit()
        self.session.refresh(prediction)
        return prediction

    def list_recent_for_session(
        self,
        session_id: int,
        limit: int = 5,
    ) -> Sequence[PredictionRecord]:
        statement = (
            select(PredictionRecord)
            .where(PredictionRecord.session_id == session_id)
            .order_by(PredictionRecord.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))
