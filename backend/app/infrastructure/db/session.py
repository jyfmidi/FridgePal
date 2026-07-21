"""Database engine/session construction owned by one application instance."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base import Base


def _ensure_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "rescue_sessions" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("rescue_sessions")}
    if "cuisine" not in existing:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE rescue_sessions "
                    "ADD COLUMN cuisine VARCHAR(30) DEFAULT ''"
                )
            )


def create_database(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    _ensure_columns(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def session_dependency(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
