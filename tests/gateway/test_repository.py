from __future__ import annotations

from shared.bootstrap import initialize_database, seed_demo_users
from shared.database import build_session_factory
from shared.repositories import SessionRepository, UserRepository
from shared.security import expires_at_from_now, generate_session_token


def test_session_persists_in_sqlite(settings) -> None:
    session_factory = build_session_factory(settings)
    initialize_database(session_factory.kw["bind"])
    with session_factory() as db_session:
        seed_demo_users(db_session, settings)
        user = UserRepository(db_session).get_by_username("alice")
        assert user is not None
        session_record = SessionRepository(db_session).create(
            token=generate_session_token(),
            user_id=user.id,
            expires_at=expires_at_from_now(30),
        )

    reopened_factory = build_session_factory(settings)
    with reopened_factory() as reopened_session:
        loaded = SessionRepository(reopened_session).get_by_token(session_record.token)
        assert loaded is not None
        assert loaded.user_id == session_record.user_id
