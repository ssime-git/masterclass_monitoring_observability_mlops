from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe


def utc_now() -> datetime:
    return datetime.now(tz=UTC).replace(tzinfo=None)


def hash_password(password: str, salt: str) -> str:
    return sha256(f"{salt}:{password}".encode()).hexdigest()


def generate_session_token() -> str:
    return token_urlsafe(32)


def expires_at_from_now(minutes: int) -> datetime:
    return utc_now() + timedelta(minutes=minutes)
