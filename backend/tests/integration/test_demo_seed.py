"""Deployment-facing contracts for deterministic demo data."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.auth.service import create_user
from app.infrastructure.db.base import Base
from app.infrastructure.db.demo_seed import DEMO_FOODS, seed_demo_inventory_for_user
from app.infrastructure.db.food_library_seed import seed_food_library
from app.infrastructure.db.models import (
    ActivityEventRow,
    FoodDefinitionRow,
    InventoryLotRow,
    ShelfLifeRuleRow,
)
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def test_demo_seed_inserts_foods_before_foreign_key_children(tmp_path: Path) -> None:
    engine: Engine = create_engine(f"sqlite:///{tmp_path / 'seed-with-foreign-keys.db'}")
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    with factory() as session:
        user = create_user(session, "seeder", "password123")

    # Deployment startup seeds the shared Food Library before optional demo inventory.
    seed_food_library(factory)
    seed_demo_inventory_for_user(factory, user.id, today=date(2026, 7, 19))

    with factory() as session:
        assert session.scalar(select(func.count()).select_from(FoodDefinitionRow)) == 72
        assert (
            session.scalar(
                select(func.count())
                .select_from(FoodDefinitionRow)
                .where(FoodDefinitionRow.active.is_(True))
            )
            == 70
        )
        for compatibility_key in ("rice", "pasta"):
            compatibility_food = session.get(FoodDefinitionRow, compatibility_key)
            assert compatibility_food is not None
            assert compatibility_food.active is False
        assert session.scalar(select(func.count()).select_from(InventoryLotRow)) == len(DEMO_FOODS)
        assert session.scalar(select(func.count()).select_from(ActivityEventRow)) == len(DEMO_FOODS)


def test_seed_for_user_creates_user_scoped_lots():
    from app.infrastructure.db.session import create_database

    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        user = create_user(session, "alice", "password123")
    seed_demo_inventory_for_user(factory, user.id)
    with factory() as session:
        lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == user.id)
        ).all()
        assert len(lots) == len(DEMO_FOODS)
        for lot in lots:
            assert lot.user_id == user.id

        spinach = session.get(FoodDefinitionRow, "spinach")
        assert spinach is not None
        assert spinach.names == {"en": "Spinach", "zh-CN": "菠菜"}
        assert spinach.aliases == {"en": ["spinach leaves"], "zh-CN": ["波斯菜"]}
        assert spinach.category == "vegetable"
        assert spinach.rounding_increment is not None
        assert spinach.package_presets
        spinach_rule = session.scalar(
            select(ShelfLifeRuleRow).where(ShelfLifeRuleRow.food_definition_id == "spinach")
        )
        assert spinach_rule is not None
        assert spinach_rule.storage_location == "FRIDGE"
        assert spinach_rule.source_note

        for compatibility_key in ("rice", "pasta"):
            compatibility_food = session.get(FoodDefinitionRow, compatibility_key)
            assert compatibility_food is not None
            assert compatibility_food.origin == "SEEDED"
            assert compatibility_food.active is False
            assert compatibility_food.category == "staple"
            assert compatibility_food.visual_key == compatibility_key


def test_demo_lot_quantities_and_history_snapshots_use_definition_units():
    from app.infrastructure.db.session import create_database

    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        user = create_user(session, "unit-check", "password123")
    seed_food_library(factory)
    seed_demo_inventory_for_user(factory, user.id, today=date(2026, 7, 19))

    with factory() as session:
        foods = {food.id: food for food in session.scalars(select(FoodDefinitionRow)).all()}
        lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == user.id)
        ).all()
        events = {
            event.food_definition_id: event
            for event in session.scalars(
                select(ActivityEventRow).where(ActivityEventRow.user_id == user.id)
            ).all()
        }

        for lot in lots:
            food = foods[lot.food_definition_id]
            event = events[lot.food_definition_id]
            assert event.display_snapshot["unit"] == food.base_unit
            assert Decimal(event.display_snapshot["quantity"]) == lot.quantity


def test_seed_for_two_users_does_not_collide():
    from app.infrastructure.db.session import create_database

    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        u1 = create_user(session, "alice", "password123")
        u2 = create_user(session, "bob", "password456")
    seed_demo_inventory_for_user(factory, u1.id)
    seed_demo_inventory_for_user(factory, u2.id)
    with factory() as session:
        u1_lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == u1.id)
        ).all()
        u2_lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == u2.id)
        ).all()
        assert len(u1_lots) == len(DEMO_FOODS)
        assert len(u2_lots) == len(DEMO_FOODS)
