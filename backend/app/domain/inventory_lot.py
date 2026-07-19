"""DE-03 InventoryLot (persistence mapping comes in Task 2)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.quantity import _coerce_decimal
from app.domain.types import ExpirySource, InventoryLotStatus, StorageLocation


@dataclass(frozen=True)
class InventoryLot:
    """One physical lot of a food. Quantity is in the FoodDefinition base unit."""

    id: str
    food_definition_id: str
    # Accepts Decimal/int/str at runtime; always coerced to Decimal in __post_init__.
    quantity: Decimal
    storage_location: StorageLocation
    stored_on: date
    expires_on: date | None
    expiry_source: ExpirySource
    status: InventoryLotStatus

    def __post_init__(self) -> None:
        coerced = _coerce_decimal(self.quantity)
        if coerced < 0:
            raise ValueError("inventory quantity is never negative")
        object.__setattr__(self, "quantity", coerced)
