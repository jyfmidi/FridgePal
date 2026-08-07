"""Integration contracts for the shared, versioned Food Library seed."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from threading import Barrier, Lock, get_ident

import pytest
from app.infrastructure.db.base import Base
from app.infrastructure.db.food_library_seed import (
    FOOD_LIBRARY_SEED_MARKER,
    FOOD_LIBRARY_SEED_VERSION,
    seed_food_library,
)
from app.infrastructure.db.models import (
    ActivityEventRow,
    AppSettingRow,
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


def _factory(tmp_path: Path, name: str) -> sessionmaker[Session]:
    engine: Engine = create_engine(
        f"sqlite:///{tmp_path / name}",
        connect_args={"check_same_thread": False, "timeout": 2},
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def _count(session: Session, row_type: type) -> int:
    return session.scalar(select(func.count()).select_from(row_type)) or 0


def test_fresh_seed_inserts_catalog_rules_and_version_without_user_data(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "fresh.db")

    seed_food_library(factory)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 70
        assert _count(session, ShelfLifeRuleRow) == 70
        assert session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER).value == {
            "value": FOOD_LIBRARY_SEED_VERSION
        }
        assert _count(session, InventoryLotRow) == 0
        assert _count(session, ActivityEventRow) == 0

        bok_choy = session.get(FoodDefinitionRow, "bok-choy")
        assert bok_choy is not None
        assert bok_choy.names == {"en": "Bok choy", "zh-CN": "上海青"}
        assert isinstance(bok_choy.aliases["en"], list)
        assert bok_choy.package_presets == [
            {
                "label": {"en": "Regular amount", "zh-CN": "常用份量"},
                "amount": "300",
                "unit": "g",
            },
            {
                "label": {"en": "Large amount", "zh-CN": "大份"},
                "amount": "500",
                "unit": "g",
            },
        ]


def test_generated_rule_ids_fit_schema_and_are_unique_and_deterministic(tmp_path: Path) -> None:
    first_factory = _factory(tmp_path, "rule-ids-first.db")
    second_factory = _factory(tmp_path, "rule-ids-second.db")

    seed_food_library(first_factory)
    seed_food_library(second_factory)

    def rule_ids(factory: sessionmaker[Session]) -> list[str]:
        with factory() as session:
            return list(session.scalars(select(ShelfLifeRuleRow.id).order_by(ShelfLifeRuleRow.id)))

    first_ids = rule_ids(first_factory)
    second_ids = rule_ids(second_factory)
    assert len(first_ids) == 70
    assert len(set(first_ids)) == 70
    assert all(len(rule_id) <= 36 for rule_id in first_ids)
    assert first_ids == second_ids


def test_second_seed_call_is_idempotent(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "idempotent.db")
    seed_food_library(factory)

    with factory() as session:
        spinach = session.get(FoodDefinitionRow, "spinach")
        assert spinach is not None
        spinach.active = False
        spinach.names = {"en": "Admin spinach", "zh-CN": "管理员菠菜"}
        session.commit()

    seed_food_library(factory)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 70
        assert _count(session, ShelfLifeRuleRow) == 70
        assert _count(session, AppSettingRow) == 1
        spinach = session.get(FoodDefinitionRow, "spinach")
        assert spinach is not None
        assert spinach.active is False
        assert spinach.names == {"en": "Admin spinach", "zh-CN": "管理员菠菜"}


def test_concurrent_startup_seed_calls_both_succeed(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "concurrent.db")
    barrier = Barrier(2)
    lock = Lock()
    synchronized_threads: set[int] = set()

    def synchronize_initial_insert(_mapper, _connection, target: FoodDefinitionRow) -> None:
        if target.id != "spinach":
            return
        thread_id = get_ident()
        with lock:
            if thread_id in synchronized_threads:
                return
            synchronized_threads.add(thread_id)
        barrier.wait(timeout=5)

    event.listen(FoodDefinitionRow, "before_insert", synchronize_initial_insert)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(seed_food_library, factory) for _ in range(2)]
            for future in futures:
                future.result(timeout=10)
    finally:
        event.remove(FoodDefinitionRow, "before_insert", synchronize_initial_insert)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 70
        assert _count(session, ShelfLifeRuleRow) == 70
        assert session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER).value == {
            "value": FOOD_LIBRARY_SEED_VERSION
        }


def test_only_the_exact_integer_version_is_treated_as_current(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "non-integer-marker.db")
    with factory() as session:
        session.add(AppSettingRow(key=FOOD_LIBRARY_SEED_MARKER, value={"value": True}))
        session.commit()

    seed_food_library(factory)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 70
        assert session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER).value == {
            "value": FOOD_LIBRARY_SEED_VERSION
        }


def test_newer_integer_marker_is_never_downgraded(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "newer-marker.db")
    with factory() as session:
        session.add(AppSettingRow(key=FOOD_LIBRARY_SEED_MARKER, value={"value": 2}))
        session.commit()

    seed_food_library(factory)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 0
        assert _count(session, ShelfLifeRuleRow) == 0
        assert session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER).value == {"value": 2}


def test_upgrade_only_fills_approved_seeded_gaps_and_preserves_owned_fields(
    tmp_path: Path,
) -> None:
    factory = _factory(tmp_path, "legacy.db")
    custom_icon = "data:image/svg+xml;base64,PHN2Zy8+"
    with factory() as session:
        session.add(
            FoodDefinitionRow(
                id="spinach",
                names={"en": "My spinach", "zh-CN": "我的菠菜"},
                aliases={},
                category="other",
                visual_key="custom-spinach",
                base_unit="kg",
                rounding_increment=None,
                package_presets=[],
                recommended_storage="PANTRY",
                origin="SEEDED",
                active=False,
                custom_icon=custom_icon,
            )
        )
        session.flush()
        session.add(
            ShelfLifeRuleRow(
                id="legacy-spinach-pantry",
                food_definition_id="spinach",
                storage_location="PANTRY",
                duration_days=99,
                source_note="Admin rule",
            )
        )

        session.add(
            FoodDefinitionRow(
                id="apple",
                names={"en": "Heritage apple", "zh-CN": "传统苹果"},
                aliases={"en": ["keeper"], "zh-CN": ["老品种"]},
                category="orchard",
                visual_key="custom-apple",
                base_unit="piece",
                rounding_increment=Decimal("2"),
                package_presets=[{"label": {"en": "Crate"}, "amount": "12", "unit": "piece"}],
                recommended_storage="FREEZER",
                origin="SEEDED",
                active=False,
                custom_icon=custom_icon,
            )
        )
        session.flush()
        session.add(
            ShelfLifeRuleRow(
                id="legacy-apple-fridge",
                food_definition_id="apple",
                storage_location="FRIDGE",
                duration_days=88,
                source_note="Existing Admin rule",
            )
        )

        session.add(
            FoodDefinitionRow(
                id="tofu",
                names={"en": "Personal tofu", "zh-CN": "自定义豆腐"},
                aliases={},
                category="other",
                visual_key="personal-tofu",
                base_unit="piece",
                rounding_increment=None,
                package_presets=[],
                recommended_storage="PANTRY",
                origin="USER_CREATED",
                active=False,
                custom_icon=custom_icon,
            )
        )
        session.add(
            FoodDefinitionRow(
                id="broccoli",
                names={"en": "Legacy broccoli", "zh-CN": "旧西兰花"},
                aliases={},
                category="other",
                visual_key="broccoli",
                base_unit="g",
                rounding_increment=None,
                package_presets=[],
                recommended_storage="FRIDGE",
                origin="SEEDED",
                active=True,
                custom_icon=None,
            )
        )
        session.add(
            FoodDefinitionRow(
                id="private-herb",
                names={"en": "Private herb", "zh-CN": "私房香草"},
                aliases={},
                category="other",
                visual_key="private-herb",
                base_unit="g",
                rounding_increment=None,
                package_presets=[],
                recommended_storage="FRIDGE",
                origin="USER_CREATED",
                active=True,
                custom_icon=None,
            )
        )
        session.commit()

    seed_food_library(factory)

    with factory() as session:
        spinach = session.get(FoodDefinitionRow, "spinach")
        assert spinach is not None
        assert spinach.names == {"en": "My spinach", "zh-CN": "我的菠菜"}
        assert spinach.aliases
        assert spinach.category == "vegetable"
        assert spinach.visual_key == "custom-spinach"
        assert spinach.base_unit == "kg"
        assert spinach.rounding_increment == Decimal("10")
        assert spinach.package_presets
        assert spinach.recommended_storage == "PANTRY"
        assert spinach.custom_icon == custom_icon
        assert spinach.active is False

        spinach_rules = {
            rule.storage_location: (rule.duration_days, rule.source_note)
            for rule in session.scalars(
                select(ShelfLifeRuleRow).where(ShelfLifeRuleRow.food_definition_id == "spinach")
            )
        }
        assert spinach_rules["PANTRY"] == (99, "Admin rule")
        assert "FRIDGE" not in spinach_rules

        broccoli_rules = list(
            session.scalars(
                select(ShelfLifeRuleRow).where(ShelfLifeRuleRow.food_definition_id == "broccoli")
            )
        )
        assert len(broccoli_rules) == 1
        assert broccoli_rules[0].storage_location == "FRIDGE"
        assert broccoli_rules[0].duration_days == 4

        apple = session.get(FoodDefinitionRow, "apple")
        assert apple is not None
        assert apple.names == {"en": "Heritage apple", "zh-CN": "传统苹果"}
        assert apple.aliases == {"en": ["keeper"], "zh-CN": ["老品种"]}
        assert apple.category == "orchard"
        assert apple.visual_key == "custom-apple"
        assert apple.base_unit == "piece"
        assert apple.rounding_increment == Decimal("2")
        assert apple.package_presets == [
            {"label": {"en": "Crate"}, "amount": "12", "unit": "piece"}
        ]
        assert apple.recommended_storage == "FREEZER"
        assert apple.custom_icon == custom_icon
        assert apple.active is False
        apple_rules = {
            rule.storage_location: (rule.duration_days, rule.source_note)
            for rule in session.scalars(
                select(ShelfLifeRuleRow).where(ShelfLifeRuleRow.food_definition_id == "apple")
            )
        }
        assert apple_rules["FRIDGE"] == (88, "Existing Admin rule")

        tofu = session.get(FoodDefinitionRow, "tofu")
        assert tofu is not None
        assert tofu.names == {"en": "Personal tofu", "zh-CN": "自定义豆腐"}
        assert tofu.aliases == {}
        assert tofu.category == "other"
        assert tofu.visual_key == "personal-tofu"
        assert tofu.base_unit == "piece"
        assert tofu.rounding_increment is None
        assert tofu.package_presets == []
        assert tofu.recommended_storage == "PANTRY"
        assert tofu.custom_icon == custom_icon
        assert tofu.active is False
        assert (
            session.scalar(
                select(func.count())
                .select_from(ShelfLifeRuleRow)
                .where(ShelfLifeRuleRow.food_definition_id == "tofu")
            )
            == 0
        )

        private_herb = session.get(FoodDefinitionRow, "private-herb")
        assert private_herb is not None
        assert private_herb.origin == "USER_CREATED"
        assert _count(session, FoodDefinitionRow) == 71


def test_persistence_failure_rolls_back_catalog_and_version_marker(tmp_path: Path) -> None:
    factory = _factory(tmp_path, "rollback.db")

    def fail_on_rule_insert(_mapper, _connection, target: ShelfLifeRuleRow) -> None:
        if target.food_definition_id == "fish":
            raise RuntimeError("injected shelf-life persistence failure")

    event.listen(ShelfLifeRuleRow, "before_insert", fail_on_rule_insert)
    try:
        with pytest.raises(RuntimeError, match="injected shelf-life persistence failure"):
            seed_food_library(factory)
    finally:
        event.remove(ShelfLifeRuleRow, "before_insert", fail_on_rule_insert)

    with factory() as session:
        assert _count(session, FoodDefinitionRow) == 0
        assert _count(session, ShelfLifeRuleRow) == 0
        assert session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER) is None
