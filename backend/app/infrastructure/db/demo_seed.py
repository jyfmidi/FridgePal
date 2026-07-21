"""Deterministic bilingual demo inventory for fixture-mode MVP development."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.inventory.service import decimal_string
from app.domain.inventory_unit import LEGACY_COUNT_UNIT_ALIASES
from app.infrastructure.db.models import ActivityEventRow, FoodDefinitionRow, InventoryLotRow

DEMO_FOODS = (
    ("spinach", "Spinach", "菠菜", "250", "g", "FRIDGE", 0),
    ("yogurt", "Yogurt", "酸奶", "300", "g", "FRIDGE", 0),
    ("chicken-breast", "Chicken breast", "鸡胸肉", "600", "g", "FRIDGE", 1),
    ("mushrooms", "Mushrooms", "蘑菇", "300", "g", "FRIDGE", 2),
    ("broccoli", "Broccoli", "西兰花", "300", "g", "FRIDGE", 2),
    ("tofu", "Tofu", "豆腐", "400", "g", "FRIDGE", 3),
    ("lemon", "Lemon", "柠檬", "3", "piece", "FRIDGE", 3),
    ("eggs", "Eggs", "鸡蛋", "8", "piece", "FRIDGE", None),
    ("milk", "Milk", "牛奶", "900", "ml", "FRIDGE", None),
    ("carrots", "Carrots", "胡萝卜", "5", "piece", "FRIDGE", None),
    ("tomatoes", "Tomatoes", "番茄", "4", "piece", "FRIDGE", None),
    ("onion", "Onion", "洋葱", "6", "piece", "PANTRY", None),
    ("garlic", "Garlic", "大蒜", "80", "g", "PANTRY", None),
    ("rice", "Rice", "大米", "1.2", "kg", "PANTRY", None),
    ("pasta", "Pasta", "意面", "500", "g", "PANTRY", None),
    ("frozen-peas", "Frozen peas", "冷冻豌豆", "450", "g", "FREEZER", None),
)


def normalize_legacy_inventory_units(factory: sessionmaker[Session]) -> None:
    """Map legacy food-specific count aliases to the canonical `piece` unit once."""
    with factory() as session:
        foods = session.scalars(
            select(FoodDefinitionRow).where(
                FoodDefinitionRow.base_unit.in_(LEGACY_COUNT_UNIT_ALIASES)
            )
        ).all()
        for food in foods:
            food.base_unit = "piece"
        session.commit()


def seed_demo_inventory_for_user(
    factory: sessionmaker[Session], user_id: str, today: date | None = None
) -> None:
    stored_on = today or date.today()
    with factory() as session:
        for food_key, name_en, name_zh, raw_quantity, unit, location, expiry_days in DEMO_FOODS:
            idempotency_key = f"demo-seed-{user_id}-{food_key}"
            already_seeded = session.scalar(
                select(InventoryLotRow.id).where(InventoryLotRow.idempotency_key == idempotency_key)
            )
            if already_seeded is not None:
                continue

            food = session.get(FoodDefinitionRow, food_key)
            names = {"en": name_en, "zh-CN": name_zh}
            if food is None:
                food = FoodDefinitionRow(
                    id=food_key,
                    names=names,
                    visual_key=food_key,
                    base_unit=unit,
                    recommended_storage=location,
                )
                session.add(food)
                # The rows below store scalar foreign keys instead of ORM relationships.
                # Persist the parent explicitly so strict databases never flush a child first.
                session.flush()

            quantity = Decimal(raw_quantity)
            expires_on = (
                stored_on + timedelta(days=expiry_days) if expiry_days is not None else None
            )
            session.add(
                InventoryLotRow(
                    id=f"demo-lot-{user_id[:8]}-{food_key}",
                    food_definition_id=food_key,
                    quantity=quantity,
                    storage_location=location,
                    stored_on=stored_on,
                    expires_on=expires_on,
                    expiry_source="LIBRARY_DEFAULT" if expires_on else "NONE",
                    status="ACTIVE",
                    idempotency_key=idempotency_key,
                    user_id=user_id,
                )
            )
            session.add(
                ActivityEventRow(
                    id=f"demo-event-{user_id[:8]}-{food_key}",
                    event_type="CHECK_IN",
                    food_definition_id=food_key,
                    quantity_delta=quantity,
                    display_snapshot={
                        "names": names,
                        "quantity": decimal_string(quantity),
                        "unit": unit,
                        "location": location,
                    },
                    idempotency_key=idempotency_key,
                    user_id=user_id,
                )
            )
        session.commit()
