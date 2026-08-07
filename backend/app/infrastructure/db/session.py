"""Database engine/session construction owned by one application instance."""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base import Base


def _ensure_columns(engine: Engine) -> None:
    """Additive column migrations for databases created before a schema change.

    The MVP uses ``Base.metadata.create_all`` (fresh databases always match the
    models), so this only repairs pre-existing databases at startup. Every
    migration is additive and idempotent.
    """
    migrations: tuple[tuple[str, dict[str, str]], ...] = (
        ("rescue_sessions", {"cuisine": "VARCHAR(30) DEFAULT ''"}),
        ("users", {"is_admin": "BOOLEAN DEFAULT 0"}),
        (
            "food_definitions",
            {
                "aliases": "JSON",
                "category": "VARCHAR(50) DEFAULT 'other'",
                "rounding_increment": "NUMERIC(18, 6)",
                "package_presets": "JSON",
                "origin": "VARCHAR(20) DEFAULT 'SEEDED'",
                "active": "BOOLEAN DEFAULT 1",
                "custom_icon": "TEXT",
                # Existing food definitions stay public (NULL) because legacy
                # rows do not record a trustworthy owner.
                "owner_user_id": "VARCHAR(36)",
            },
        ),
    )
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table, columns in migrations:
        if table not in existing_tables:
            continue
        existing = {col["name"] for col in inspector.get_columns(table)}
        with engine.begin() as conn:
            for name, definition in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

    if "food_definitions" in existing_tables:
        owner_index = "ix_food_definitions_owner_user_id"
        existing_indexes = {
            index["name"] for index in inspect(engine).get_indexes("food_definitions")
        }
        if owner_index not in existing_indexes:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "CREATE INDEX ix_food_definitions_owner_user_id "
                        "ON food_definitions (owner_user_id)"
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
