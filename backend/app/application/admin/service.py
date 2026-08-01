"""Admin use cases: Food Library management and application settings.

The Food Library is a shared, server-owned catalog (FR-LIB-001, FR-LIB-003,
P1 "Full Food Library management UI"): foods are created or edited here by the
administrator, then served to every user through the read-only library
endpoint and the Storage overview. Library mutations never touch user-owned
inventory; user data remains isolated by ``user_id``.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.errors import DomainError
from app.domain.inventory_unit import canonical_inventory_unit
from app.domain.quantity import Quantity, convert
from app.infrastructure.db.models import (
    AppSettingRow,
    FoodDefinitionRow,
    InventoryLotRow,
    ShelfLifeRuleRow,
)

STORAGE_LOCATIONS = ("FRIDGE", "FREEZER", "PANTRY")
CANONICAL_UNITS = ("g", "kg", "ml", "l", "piece")
FOOD_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")

DEFAULT_USE_SOON_WINDOW_DAYS = 5


class AdminError(Exception):
    """Raised when an admin mutation fails validation or a uniqueness rule."""

    def __init__(self, message: str, *, code: str = "ADMIN_ERROR") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ShelfLifeInput:
    storage_location: str
    duration_days: int
    source_note: str | None = None


@dataclass(frozen=True)
class PackagePresetInput:
    label: dict[str, str]
    amount: Decimal
    unit: str


@dataclass(frozen=True)
class FoodDefinitionInput:
    names: dict[str, str]
    visual_key: str
    base_unit: str
    recommended_storage: str
    food_key: str | None = None
    aliases: dict[str, list[str]] | None = None
    category: str = "other"
    rounding_increment: Decimal | None = None
    package_presets: list[PackagePresetInput] | None = None
    active: bool = True
    shelf_life: list[ShelfLifeInput] | None = None


def _slugify(name: str) -> str:
    slug = name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]+", "-", slug).strip("-")
    return slug or "food"


def _validate_food_input(data: FoodDefinitionInput) -> str:
    """Validate shared food-definition fields; returns the canonical food key."""
    if not data.names.get("en", "").strip():
        raise AdminError("An English display name is required.", code="ADMIN_NAME_REQUIRED")
    for locale, name in data.names.items():
        if not isinstance(name, str) or not name.strip():
            raise AdminError(
                f"Name for locale {locale!r} must not be empty.",
                code="ADMIN_NAME_REQUIRED",
            )
        if len(name) > 100:
            raise AdminError(f"Name for locale {locale!r} is too long.", code="ADMIN_NAME_INVALID")

    try:
        base_unit = canonical_inventory_unit(data.base_unit)
    except ValueError as error:
        raise AdminError(str(error), code="ADMIN_UNIT_INVALID") from error
    if base_unit not in CANONICAL_UNITS:
        raise AdminError(
            f"Base unit must be one of {', '.join(CANONICAL_UNITS)}.",
            code="ADMIN_UNIT_INVALID",
        )
    if data.recommended_storage not in STORAGE_LOCATIONS:
        raise AdminError(
            "Recommended storage must be FRIDGE, FREEZER, or PANTRY.",
            code="ADMIN_LOCATION_INVALID",
        )
    if data.rounding_increment is not None and data.rounding_increment <= 0:
        raise AdminError("Rounding increment must be positive.", code="ADMIN_ROUNDING_INVALID")

    for preset in data.package_presets or []:
        if not preset.label.get("en", "").strip():
            raise AdminError(
                "Every package preset needs an English label.",
                code="ADMIN_PRESET_INVALID",
            )
        if preset.amount <= 0:
            raise AdminError(
                "Package preset amounts must be positive.",
                code="ADMIN_PRESET_INVALID",
            )
        try:
            canonical_inventory_unit(preset.unit)
        except ValueError as error:
            raise AdminError(str(error), code="ADMIN_PRESET_INVALID") from error

    seen_locations: set[str] = set()
    for rule in data.shelf_life or []:
        if rule.storage_location not in STORAGE_LOCATIONS:
            raise AdminError(
                "Shelf-life rules must reference FRIDGE, FREEZER, or PANTRY.",
                code="ADMIN_RULE_INVALID",
            )
        if rule.storage_location in seen_locations:
            raise AdminError(
                "A food may have only one shelf-life rule per location.",
                code="ADMIN_RULE_INVALID",
            )
        seen_locations.add(rule.storage_location)
        if rule.duration_days < 0:
            raise AdminError("Shelf-life duration cannot be negative.", code="ADMIN_RULE_INVALID")

    key = data.food_key or _slugify(data.names["en"])
    if not FOOD_KEY_PATTERN.match(key):
        raise AdminError(
            "Food key may contain only lowercase letters, numbers, and hyphens.",
            code="ADMIN_KEY_INVALID",
        )
    return key


def _food_payload(food: FoodDefinitionRow, shelf_life: list[ShelfLifeRuleRow]) -> dict[str, object]:
    return {
        "foodKey": food.id,
        "names": food.names,
        "aliases": food.aliases or {},
        "category": food.category,
        "visualKey": food.visual_key,
        "baseUnit": food.base_unit,
        "roundingIncrement": (
            format(food.rounding_increment.normalize(), "f")
            if food.rounding_increment is not None
            else None
        ),
        "packagePresets": [
            {
                "label": preset.get("label", {}),
                "amount": format(Decimal(str(preset.get("amount", 0))).normalize(), "f"),
                "unit": preset.get("unit", ""),
            }
            for preset in food.package_presets or []
        ],
        "recommendedStorage": food.recommended_storage,
        "origin": food.origin,
        "active": food.active,
        "customIcon": food.custom_icon,
        "shelfLife": [
            {
                "storageLocation": rule.storage_location,
                "durationDays": rule.duration_days,
                "sourceNote": rule.source_note,
            }
            for rule in shelf_life
        ],
    }


def _rules_for(session: Session, food_id: str) -> list[ShelfLifeRuleRow]:
    return list(
        session.scalars(
            select(ShelfLifeRuleRow)
            .where(ShelfLifeRuleRow.food_definition_id == food_id)
            .order_by(ShelfLifeRuleRow.storage_location)
        )
    )


def list_food_definitions(session: Session) -> list[dict[str, object]]:
    """All food definitions including inactive ones, with their shelf-life rules."""
    foods = session.scalars(
        select(FoodDefinitionRow).order_by(FoodDefinitionRow.active.desc(), FoodDefinitionRow.id)
    ).all()
    return [_food_payload(food, _rules_for(session, food.id)) for food in foods]


def list_library(session: Session) -> list[dict[str, object]]:
    """Active food definitions exposed to every user (Food Library typeahead)."""
    foods = session.scalars(
        select(FoodDefinitionRow)
        .where(FoodDefinitionRow.active.is_(True))
        .order_by(FoodDefinitionRow.id)
    ).all()
    return [_food_payload(food, _rules_for(session, food.id)) for food in foods]


def create_food_definition(session: Session, data: FoodDefinitionInput) -> dict[str, object]:
    food_key = _validate_food_input(data)
    if session.get(FoodDefinitionRow, food_key) is not None:
        raise AdminError("A food with this key already exists.", code="ADMIN_FOOD_EXISTS")

    food = FoodDefinitionRow(
        id=food_key,
        names=data.names,
        aliases=data.aliases or {},
        category=data.category.strip() or "other",
        visual_key=data.visual_key or food_key,
        base_unit=canonical_inventory_unit(data.base_unit),
        rounding_increment=data.rounding_increment,
        package_presets=[
            {
                "label": preset.label,
                "amount": str(preset.amount),
                "unit": canonical_inventory_unit(preset.unit),
            }
            for preset in data.package_presets or []
        ],
        recommended_storage=data.recommended_storage,
        origin="USER_CREATED",
        active=data.active,
    )
    session.add(food)
    session.flush()
    for rule in data.shelf_life or []:
        session.add(
            ShelfLifeRuleRow(
                id=str(uuid4()),
                food_definition_id=food.id,
                storage_location=rule.storage_location,
                duration_days=rule.duration_days,
                source_note=rule.source_note,
            )
        )
    session.commit()
    return _food_payload(food, _rules_for(session, food.id))


def _change_base_unit(session: Session, food: FoodDefinitionRow, new_unit: str) -> None:
    """Convert every lot of a food when its base unit changes.

    Only same-dimension conversions are applied (contracts 6.2); anything else
    is rejected instead of guessing.
    """
    if food.base_unit == new_unit:
        return
    lots = session.scalars(
        select(InventoryLotRow).where(InventoryLotRow.food_definition_id == food.id)
    ).all()
    for lot in lots:
        try:
            converted = convert(Quantity(lot.quantity, food.base_unit), new_unit)
        except (ValueError, DomainError) as error:
            raise AdminError(
                f"Cannot change base unit from {food.base_unit!r} to {new_unit!r} "
                f"while lots exist: {error}",
                code="ADMIN_UNIT_CHANGE_CONFLICT",
            ) from error
        lot.quantity = converted.value
    food.base_unit = new_unit


def update_food_definition(
    session: Session, food_id: str, data: FoodDefinitionInput
) -> dict[str, object]:
    food = session.get(FoodDefinitionRow, food_id)
    if food is None:
        raise AdminError("Food definition not found.", code="ADMIN_FOOD_NOT_FOUND")
    if data.food_key is not None and data.food_key != food.id:
        # Lots, events, recipes, and rescue sessions reference the canonical key;
        # renaming would orphan them, so the key is immutable after creation.
        raise AdminError("The food key cannot be changed after creation.", code="ADMIN_KEY_INVALID")

    _validate_food_input(data)
    _change_base_unit(session, food, canonical_inventory_unit(data.base_unit))

    food.names = data.names
    food.aliases = data.aliases or {}
    food.category = data.category.strip() or "other"
    food.visual_key = data.visual_key or food.id
    food.rounding_increment = data.rounding_increment
    food.package_presets = [
        {
            "label": preset.label,
            "amount": str(preset.amount),
            "unit": canonical_inventory_unit(preset.unit),
        }
        for preset in data.package_presets or []
    ]
    food.recommended_storage = data.recommended_storage
    food.active = data.active

    for rule in session.scalars(
        select(ShelfLifeRuleRow).where(ShelfLifeRuleRow.food_definition_id == food.id)
    ).all():
        session.delete(rule)
    # Flush the deletes so the unique (food, location) constraint is free before
    # the replacement rules are inserted.
    session.flush()
    for new_rule in data.shelf_life or []:
        session.add(
            ShelfLifeRuleRow(
                id=str(uuid4()),
                food_definition_id=food.id,
                storage_location=new_rule.storage_location,
                duration_days=new_rule.duration_days,
                source_note=new_rule.source_note,
            )
        )
    session.commit()
    return _food_payload(food, _rules_for(session, food.id))


def soft_delete_food_definition(session: Session, food_id: str) -> None:
    """Deactivate a food; historical lots and events remain valid (DE-01 active flag)."""
    food = session.get(FoodDefinitionRow, food_id)
    if food is None:
        raise AdminError("Food definition not found.", code="ADMIN_FOOD_NOT_FOUND")
    food.active = False
    session.commit()


def get_app_settings(session: Session) -> dict[str, object]:
    row = session.get(AppSettingRow, "use_soon_window_days")
    if row is None:
        return {"useSoonWindowDays": DEFAULT_USE_SOON_WINDOW_DAYS}
    raw = row.value.get("value", DEFAULT_USE_SOON_WINDOW_DAYS)
    if not isinstance(raw, int):
        raise AdminError("Stored setting is corrupt.", code="ADMIN_SETTING_INVALID")
    return {"useSoonWindowDays": raw}


def update_app_settings(session: Session, use_soon_window_days: int) -> dict[str, object]:
    if use_soon_window_days < 1:
        raise AdminError(
            "The Use Soon window must be at least 1 day.", code="ADMIN_SETTING_INVALID"
        )
    if use_soon_window_days > 30:
        raise AdminError("The Use Soon window cannot exceed 30 days.", code="ADMIN_SETTING_INVALID")
    row = session.get(AppSettingRow, "use_soon_window_days")
    if row is None:
        row = AppSettingRow(key="use_soon_window_days", value={"value": use_soon_window_days})
        session.add(row)
    else:
        row.value = {"value": use_soon_window_days}
    session.commit()
    return {"useSoonWindowDays": use_soon_window_days}


def set_food_icon(session: Session, food_id: str, data_uri: str) -> dict[str, object]:
    """Persist a validated custom icon (data URI) on a food definition."""
    food = session.get(FoodDefinitionRow, food_id)
    if food is None:
        raise AdminError("Food definition not found.", code="ADMIN_FOOD_NOT_FOUND")
    food.custom_icon = data_uri
    session.commit()
    return _food_payload(food, _rules_for(session, food.id))


def clear_food_icon(session: Session, food_id: str) -> dict[str, object]:
    """Remove a custom icon so the food falls back to its visual key."""
    food = session.get(FoodDefinitionRow, food_id)
    if food is None:
        raise AdminError("Food definition not found.", code="ADMIN_FOOD_NOT_FOUND")
    food.custom_icon = None
    session.commit()
    return _food_payload(food, _rules_for(session, food.id))


def ensure_default_settings(session: Session) -> None:
    """Idempotently seed default application settings at startup."""
    row = session.get(AppSettingRow, "use_soon_window_days")
    if row is None:
        session.add(
            AppSettingRow(key="use_soon_window_days", value={"value": DEFAULT_USE_SOON_WINDOW_DAYS})
        )
        session.commit()
