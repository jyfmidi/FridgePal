"""DE-01 FoodDefinition and DE-02 ShelfLifeRule (persistence mapping comes in Task 2)."""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.quantity import CrossDimensionConversion, is_known_unit
from app.domain.types import FoodOrigin, StorageLocation


@dataclass(frozen=True)
class FoodDefinition:
    """Canonical library food. Quantities are stored in ``base_unit``."""

    id: str
    names: dict[str, str]
    category: str
    visual_key: str
    base_unit: str
    rounding_increment: Decimal
    recommended_storage: StorageLocation
    origin: FoodOrigin
    aliases: dict[str, list[str]] = field(default_factory=dict)
    package_presets: dict[str, Decimal] = field(default_factory=dict)
    active: bool = True
    cross_dimension_conversion: CrossDimensionConversion | None = None

    def __post_init__(self) -> None:
        if not self.names:
            raise ValueError("FoodDefinition requires at least one localized name")
        if not is_known_unit(self.base_unit):
            raise ValueError(f"unknown base unit: {self.base_unit!r}")
        if self.rounding_increment <= 0:
            raise ValueError("rounding_increment must be positive")
        if self.cross_dimension_conversion is not None and self.base_unit not in (
            self.cross_dimension_conversion.source_unit,
            self.cross_dimension_conversion.target_unit,
        ):
            raise ValueError(
                "cross-dimension conversion metadata must involve the food's base unit"
            )


@dataclass(frozen=True)
class ShelfLifeRule:
    """Suggested shelf life for a food at one storage location, in calendar days."""

    food_definition_id: str
    storage_location: StorageLocation
    duration_days: int
    source_note: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.duration_days, bool) or not isinstance(self.duration_days, int):
            raise TypeError("duration_days must be an integer number of calendar days")
        if self.duration_days < 0:
            raise ValueError("duration_days must be non-negative")
