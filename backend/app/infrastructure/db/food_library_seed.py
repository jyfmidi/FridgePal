"""Versioned, non-destructive startup seed for the shared Food Library."""

import sqlite3
from time import sleep
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.food_library_catalog import FOOD_LIBRARY_CATALOG, PresetFood
from app.infrastructure.db.models import AppSettingRow, FoodDefinitionRow, ShelfLifeRuleRow

FOOD_LIBRARY_SEED_VERSION = 1
FOOD_LIBRARY_SEED_MARKER = "food_library_seed_version"
_MAX_SEED_ATTEMPTS = 3


def _aliases(food: PresetFood) -> dict[str, list[str]]:
    return {locale: list(aliases) for locale, aliases in food.aliases.items()}


def _package_presets(food: PresetFood) -> list[dict[str, object]]:
    return [
        {
            "label": dict(preset.label),
            "amount": str(preset.amount),
            "unit": preset.unit,
        }
        for preset in food.package_presets
    ]


def _new_food(food: PresetFood) -> FoodDefinitionRow:
    return FoodDefinitionRow(
        id=food.food_key,
        names=dict(food.names),
        aliases=_aliases(food),
        category=food.category,
        visual_key=food.visual_key,
        base_unit=food.base_unit,
        rounding_increment=food.rounding_increment,
        package_presets=_package_presets(food),
        recommended_storage=food.recommended_storage,
        origin="SEEDED",
        active=True,
    )


def _fill_legacy_seed_gaps(row: FoodDefinitionRow, food: PresetFood) -> None:
    if row.category == "other":
        row.category = food.category
    if not row.aliases:
        row.aliases = _aliases(food)
    if row.rounding_increment is None:
        row.rounding_increment = food.rounding_increment
    if not row.package_presets:
        row.package_presets = _package_presets(food)


def _is_applied_marker(marker: AppSettingRow | None) -> bool:
    if marker is None or not isinstance(marker.value, dict):
        return False
    value = marker.value.get("value")
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= FOOD_LIBRARY_SEED_VERSION
    )


def _rule_id(food_key: str, storage_location: str) -> str:
    identity = f"fridge-pal:food-library:v{FOOD_LIBRARY_SEED_VERSION}:{food_key}:{storage_location}"
    return str(uuid5(NAMESPACE_URL, identity))


def _seed_once(factory: sessionmaker[Session]) -> None:
    with factory.begin() as session:
        marker = session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER)
        if _is_applied_marker(marker):
            return

        seeded_food_ids: set[str] = set()
        rule_eligible_food_ids: set[str] = set()
        for food in FOOD_LIBRARY_CATALOG:
            row = session.get(FoodDefinitionRow, food.food_key)
            if row is None:
                session.add(_new_food(food))
                seeded_food_ids.add(food.food_key)
                rule_eligible_food_ids.add(food.food_key)
            elif row.origin == "SEEDED":
                _fill_legacy_seed_gaps(row, food)
                seeded_food_ids.add(food.food_key)
                if row.recommended_storage == food.recommended_storage:
                    rule_eligible_food_ids.add(food.food_key)

        # Parent definitions must exist before strict databases accept rule FKs.
        session.flush()

        existing_rule_pairs: set[tuple[str, str]] = {
            (food_definition_id, storage_location)
            for food_definition_id, storage_location in session.execute(
                select(
                    ShelfLifeRuleRow.food_definition_id,
                    ShelfLifeRuleRow.storage_location,
                ).where(ShelfLifeRuleRow.food_definition_id.in_(seeded_food_ids))
            )
        }
        for food in FOOD_LIBRARY_CATALOG:
            if food.food_key not in rule_eligible_food_ids:
                continue
            for rule in food.shelf_life:
                pair = (food.food_key, rule.storage_location)
                if pair in existing_rule_pairs:
                    continue
                session.add(
                    ShelfLifeRuleRow(
                        id=_rule_id(food.food_key, rule.storage_location),
                        food_definition_id=food.food_key,
                        storage_location=rule.storage_location,
                        duration_days=rule.duration_days,
                        source_note=rule.source_note,
                    )
                )
                existing_rule_pairs.add(pair)

        # Flush the complete catalog before recording that this version succeeded.
        session.flush()
        marker_value: dict[str, object] = {"value": FOOD_LIBRARY_SEED_VERSION}
        if marker is None:
            session.add(AppSettingRow(key=FOOD_LIBRARY_SEED_MARKER, value=marker_value))
        else:
            marker.value = marker_value


def _is_sqlite_lock(error: OperationalError) -> bool:
    return isinstance(error.orig, sqlite3.OperationalError) and "locked" in str(error.orig).lower()


def _database_has_applied_marker(factory: sessionmaker[Session]) -> bool:
    try:
        with factory() as session:
            return _is_applied_marker(session.get(AppSettingRow, FOOD_LIBRARY_SEED_MARKER))
    except OperationalError as error:
        if _is_sqlite_lock(error):
            return False
        raise


def seed_food_library(factory: sessionmaker[Session]) -> None:
    """Apply the catalog atomically, tolerating a bounded concurrent-start race."""
    for attempt in range(_MAX_SEED_ATTEMPTS):
        try:
            _seed_once(factory)
            return
        except IntegrityError:
            if _database_has_applied_marker(factory):
                return
            if attempt == _MAX_SEED_ATTEMPTS - 1:
                raise
        except OperationalError as error:
            if not _is_sqlite_lock(error):
                raise
            if _database_has_applied_marker(factory):
                return
            if attempt == _MAX_SEED_ATTEMPTS - 1:
                raise
        sleep(0.02 * (attempt + 1))
