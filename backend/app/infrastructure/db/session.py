"""Database engine/session construction owned by one application instance."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base import Base


def create_database(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def session_dependency(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
