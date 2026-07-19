"""Lightweight entity invariants for FoodDefinition, ShelfLifeRule, and InventoryLot."""

from datetime import date
from decimal import Decimal

import pytest
from app.domain.food_definition import FoodDefinition
from app.domain.inventory_lot import InventoryLot
from app.domain.quantity import CrossDimensionConversion
from app.domain.types import (
    ExpirySource,
    FoodOrigin,
    InventoryLotStatus,
    StorageLocation,
)


def make_food(**overrides: object) -> FoodDefinition:
    fields: dict[str, object] = {
        "id": "food-garlic",
        "names": {"en": "Garlic", "zh-CN": "大蒜"},
        "aliases": {"en": ["garlic clove"]},
        "category": "produce",
        "visual_key": "garlic",
        "base_unit": "piece",
        "rounding_increment": Decimal("1"),
        "recommended_storage": StorageLocation.PANTRY,
        "origin": FoodOrigin.SEEDED,
    }
    fields.update(overrides)
    return FoodDefinition(**fields)  # type: ignore[arg-type]


class TestFoodDefinition:
    def test_defaults_to_active_without_conversion_metadata(self) -> None:
        food = make_food()
        assert food.active is True
        assert food.cross_dimension_conversion is None

    def test_rejects_unknown_base_unit(self) -> None:
        with pytest.raises(ValueError):
            make_food(base_unit="furlong")

    def test_rejects_non_positive_rounding_increment(self) -> None:
        with pytest.raises(ValueError):
            make_food(rounding_increment=Decimal("0"))

    def test_requires_primary_name(self) -> None:
        with pytest.raises(ValueError):
            make_food(names={})

    def test_explicit_cross_dimension_metadata_is_allowed(self) -> None:
        conversion = CrossDimensionConversion(source_unit="piece", target_unit="g", factor="5")
        food = make_food(cross_dimension_conversion=conversion)
        assert food.cross_dimension_conversion is conversion

    def test_conversion_metadata_must_involve_base_unit(self) -> None:
        # Metadata that does not connect the base unit to another dimension is useless.
        bad = CrossDimensionConversion(source_unit="g", target_unit="ml", factor="1")
        with pytest.raises(ValueError):
            make_food(cross_dimension_conversion=bad)

    def test_same_dimension_metadata_is_not_cross_dimension(self) -> None:
        with pytest.raises(ValueError):
            CrossDimensionConversion(source_unit="g", target_unit="kg", factor="1")


class TestInventoryLot:
    def make(self, **overrides: object) -> InventoryLot:
        fields: dict[str, object] = {
            "id": "lot-1",
            "food_definition_id": "food-garlic",
            "quantity": Decimal("3"),
            "storage_location": StorageLocation.FRIDGE,
            "stored_on": date(2025, 3, 10),
            "expires_on": date(2025, 3, 17),
            "expiry_source": ExpirySource.LIBRARY_DEFAULT,
            "status": InventoryLotStatus.ACTIVE,
        }
        fields.update(overrides)
        return InventoryLot(**fields)  # type: ignore[arg-type]

    def test_quantity_coerced_to_decimal(self) -> None:
        lot = self.make(quantity="2.5")
        assert lot.quantity == Decimal("2.5")
        assert isinstance(lot.quantity, Decimal)

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValueError):
            self.make(quantity=Decimal("-1"))

    def test_float_quantity_rejected(self) -> None:
        with pytest.raises(TypeError):
            self.make(quantity=1.5)

    def test_expires_on_may_be_none(self) -> None:
        lot = self.make(expires_on=None, expiry_source=ExpirySource.NONE)
        assert lot.expires_on is None
