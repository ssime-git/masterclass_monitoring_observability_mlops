from sqlalchemy import Engine
from sqlalchemy.orm import Session

from masterclass_mlops.config import Settings
from masterclass_mlops.database import Base
from masterclass_mlops.repositories import UserRepository
from masterclass_mlops.security import hash_password

DEMO_USERS = ("alice", "bob", "admin")
DEMO_PASSWORD = "mlops-demo"


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


def seed_demo_users(session: Session, settings: Settings) -> None:
    repository = UserRepository(session)
    for username in DEMO_USERS:
        if repository.get_by_username(username) is None:
            password_hash = hash_password(DEMO_PASSWORD, settings.password_salt)
            repository.create(username=username, password_hash=password_hash)
