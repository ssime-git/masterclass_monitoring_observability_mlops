from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from shared.config import Settings


class Base(DeclarativeBase):
    pass


def ensure_sqlite_parent(database_url: str) -> None:
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        database_path = Path(database_url.removeprefix(prefix))
        database_path.parent.mkdir(parents=True, exist_ok=True)


def create_sqlite_engine(settings: Settings) -> Engine:
    ensure_sqlite_parent(settings.database_url)
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )


def build_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = create_sqlite_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
