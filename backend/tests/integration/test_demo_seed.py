"""Deployment-facing contracts for deterministic demo data."""

from datetime import date
from pathlib import Path

from app.auth.service import create_user
from app.infrastructure.db.base import Base
from app.infrastructure.db.demo_seed import DEMO_FOODS, seed_demo_inventory_for_user
from app.infrastructure.db.models import ActivityEventRow, FoodDefinitionRow, InventoryLotRow
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

    seed_demo_inventory_for_user(factory, user.id, today=date(2026, 7, 19))

    with factory() as session:
        assert session.scalar(select(func.count()).select_from(FoodDefinitionRow)) == len(
            DEMO_FOODS
        )
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
