"""Schema contracts for public and user-owned Food Library definitions."""

from pathlib import Path

from app.infrastructure.db.models import FoodDefinitionRow  # noqa: F401
from app.infrastructure.db.session import create_database
from sqlalchemy import create_engine, inspect, text


def test_fresh_food_definition_schema_has_nullable_indexed_owner_foreign_key(
    tmp_path: Path,
) -> None:
    engine, _ = create_database(f"sqlite:///{tmp_path / 'fresh.db'}")
    inspector = inspect(engine)

    column = next(
        item
        for item in inspector.get_columns("food_definitions")
        if item["name"] == "owner_user_id"
    )
    assert column["nullable"] is True
    assert any(
        foreign_key["constrained_columns"] == ["owner_user_id"]
        and foreign_key["referred_table"] == "users"
        and foreign_key["referred_columns"] == ["id"]
        for foreign_key in inspector.get_foreign_keys("food_definitions")
    )
    assert any(
        index["column_names"] == ["owner_user_id"]
        for index in inspector.get_indexes("food_definitions")
    )


def test_legacy_sqlite_food_definitions_gain_nullable_owner_column_and_index(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    legacy_engine = create_engine(database_url)
    with legacy_engine.begin() as connection:
        connection.execute(text("CREATE TABLE food_definitions (id VARCHAR(100) PRIMARY KEY)"))
        connection.execute(text("INSERT INTO food_definitions (id) VALUES ('legacy-food')"))

    engine, _ = create_database(database_url)
    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("food_definitions")}

    assert columns["owner_user_id"]["nullable"] is True
    assert any(
        index["column_names"] == ["owner_user_id"]
        for index in inspector.get_indexes("food_definitions")
    )
    with engine.connect() as connection:
        owner = connection.execute(text("SELECT owner_user_id FROM food_definitions")).scalar()
        assert owner is None
