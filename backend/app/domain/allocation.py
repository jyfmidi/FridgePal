"""Pure deduction-allocation preview (contracts section 9).

Given user-confirmed per-food demand and candidate lots, produce proposed
lot-level deltas without mutating anything. Explicitly selected lots are used
first (when still valid and active), then remaining demand is allocated by
earliest ``expires_on`` (FEFO) with no-date lots last. Allocation never exceeds
lot availability or demand, never produces a negative remainder, and exposes a
per-food shortfall when availability runs out.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.quantity import _coerce_decimal
from app.domain.types import InventoryLotStatus


@dataclass(frozen=True)
class AllocationLot:
    """A candidate lot for the allocation preview."""

    lot_id: str
    food_definition_id: str
    # Accepts Decimal/int/str at runtime; always coerced to Decimal in __post_init__.
    available_quantity: Decimal
    expires_on: date | None
    status: InventoryLotStatus = InventoryLotStatus.ACTIVE

    def __post_init__(self) -> None:
        coerced = _coerce_decimal(self.available_quantity)
        if coerced < 0:
            raise ValueError("lot availability is never negative")
        object.__setattr__(self, "available_quantity", coerced)


@dataclass(frozen=True)
class AllocationLine:
    """Proposed deduction of ``delta`` from one lot, in the food's base unit."""

    lot_id: str
    delta: Decimal


@dataclass(frozen=True)
class AllocationPlan:
    """Preview result: proposed per-lot deltas plus per-food shortfalls."""

    lines: tuple[AllocationLine, ...]
    shortfalls: dict[str, Decimal]


def _fefo_key(lot: AllocationLot) -> tuple[bool, date, str]:
    # Dated lots first (earliest expiry), no-date lots last, lot id breaks ties.
    return (lot.expires_on is None, lot.expires_on or date.min, lot.lot_id)


def allocate(
    demands: Mapping[str, Decimal | int | str],
    lots: Sequence[AllocationLot],
    selected_lot_ids: Iterable[str] = (),
) -> AllocationPlan:
    """Build the allocation preview. Pure: inputs are never mutated."""
    normalized_demands: dict[str, Decimal] = {}
    for food_id, raw in demands.items():
        demand = _coerce_decimal(raw)
        if demand < 0:
            raise ValueError("demand must be non-negative")
        if demand > 0:
            normalized_demands[food_id] = demand

    lot_by_id = {lot.lot_id: lot for lot in lots}
    selected_order = list(dict.fromkeys(selected_lot_ids))

    lines: list[AllocationLine] = []
    shortfalls: dict[str, Decimal] = {}
    for food_id, demand in normalized_demands.items():
        active_lots = [
            lot
            for lot in lots
            if lot.food_definition_id == food_id and lot.status is InventoryLotStatus.ACTIVE
        ]
        active_ids = {lot.lot_id for lot in active_lots}

        ordered: list[AllocationLot] = []
        for lot_id in selected_order:
            candidate = lot_by_id.get(lot_id)
            if candidate is not None and candidate.lot_id in active_ids:
                ordered.append(candidate)
        ordered_ids = {lot.lot_id for lot in ordered}
        ordered.extend(
            sorted((lot for lot in active_lots if lot.lot_id not in ordered_ids), key=_fefo_key)
        )

        remaining = demand
        for lot in ordered:
            if remaining <= 0:
                break
            delta = min(remaining, lot.available_quantity)
            if delta > 0:
                lines.append(AllocationLine(lot_id=lot.lot_id, delta=delta))
                remaining -= delta
        if remaining > 0:
            shortfalls[food_id] = remaining

    return AllocationPlan(lines=tuple(lines), shortfalls=shortfalls)
