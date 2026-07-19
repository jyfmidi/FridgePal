"""Transactional check-in, mutation, and read-only Storage overview operations."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.allocation import AllocationLot, allocate
from app.domain.types import InventoryLotStatus, InventoryReason
from app.infrastructure.db.models import (
    ActivityEventRow,
    FoodDefinitionRow,
    InventoryLotRow,
    InventoryTransactionRow,
)


class LotNotFoundError(Exception):
    """Raised when a lot-targeting operation references an unknown lot."""


@dataclass(frozen=True)
class CheckInCommand:
    idempotency_key: str
    food_key: str
    names: dict[str, str]
    quantity: Decimal
    unit: str
    location: str
    stored_on: date
    expires_on: date | None
    expiry_source: str


@dataclass(frozen=True)
class CheckInResult:
    lot_id: str
    activity_event_id: str
    replayed: bool


def check_in_food(session: Session, command: CheckInCommand) -> CheckInResult:
    replay = session.scalar(
        select(InventoryLotRow).where(InventoryLotRow.idempotency_key == command.idempotency_key)
    )
    if replay is not None:
        event = session.scalar(
            select(ActivityEventRow).where(
                ActivityEventRow.idempotency_key == command.idempotency_key
            )
        )
        if event is None:  # The transaction contract makes this unreachable for committed data.
            raise RuntimeError("idempotent lot is missing its ActivityEvent")
        return CheckInResult(replay.id, event.id, True)

    food = session.get(FoodDefinitionRow, command.food_key)
    if food is None:
        food = FoodDefinitionRow(
            id=command.food_key,
            names=command.names,
            visual_key=command.food_key,
            base_unit=command.unit,
            recommended_storage=command.location,
        )
        session.add(food)
    elif food.base_unit != command.unit:
        raise ValueError("check-in unit must match the FoodDefinition base unit")

    lot = InventoryLotRow(
        id=str(uuid4()),
        food_definition_id=food.id,
        quantity=command.quantity,
        storage_location=command.location,
        stored_on=command.stored_on,
        expires_on=command.expires_on,
        expiry_source=command.expiry_source,
        status="ACTIVE",
        idempotency_key=command.idempotency_key,
    )
    event = ActivityEventRow(
        id=str(uuid4()),
        event_type="CHECK_IN",
        food_definition_id=food.id,
        quantity_delta=command.quantity,
        display_snapshot={
            "names": command.names,
            "quantity": decimal_string(command.quantity),
            "unit": command.unit,
            "location": command.location,
        },
        idempotency_key=command.idempotency_key,
    )
    session.add_all([lot, event])
    session.commit()
    return CheckInResult(lot.id, event.id, False)


def decimal_string(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def urgency_for(expires_on: date | None, today: date) -> str:
    if expires_on is None or (expires_on - today).days > 5:
        return "LATER"
    days = (expires_on - today).days
    if days < 0:
        return "PAST_DATE"
    if days == 0:
        return "TODAY"
    if days <= 2:
        return "ONE_TO_TWO_DAYS"
    return "THREE_TO_FIVE_DAYS"


def get_storage_overview(session: Session, today: date) -> dict[str, list[dict[str, object]]]:
    rows = session.execute(
        select(InventoryLotRow, FoodDefinitionRow)
        .join(FoodDefinitionRow, FoodDefinitionRow.id == InventoryLotRow.food_definition_id)
        .where(InventoryLotRow.status == "ACTIVE", InventoryLotRow.quantity > 0)
        .order_by(FoodDefinitionRow.id, InventoryLotRow.storage_location)
    ).all()

    aggregates: dict[tuple[str, str], dict[str, object]] = {}
    ranks = {"PAST_DATE": 5, "TODAY": 4, "ONE_TO_TWO_DAYS": 3, "THREE_TO_FIVE_DAYS": 2, "LATER": 1}
    for lot, food in rows:
        key = (food.id, lot.storage_location)
        urgency = urgency_for(lot.expires_on, today)
        current = aggregates.get(key)
        if current is None:
            aggregates[key] = {
                "foodKey": food.id,
                "names": food.names,
                "visualKey": food.visual_key,
                "quantityDecimal": lot.quantity,
                "unit": food.base_unit,
                "location": lot.storage_location,
                "urgency": urgency,
            }
        else:
            current["quantityDecimal"] = current["quantityDecimal"] + lot.quantity  # type: ignore[operator]
            if ranks[urgency] > ranks[str(current["urgency"])]:
                current["urgency"] = urgency

    inventory: list[dict[str, object]] = []
    for aggregate in aggregates.values():
        quantity = aggregate.pop("quantityDecimal")
        aggregate["quantity"] = decimal_string(quantity)  # type: ignore[arg-type]
        inventory.append(aggregate)

    use_soon = [item for item in inventory if item["urgency"] != "LATER"]
    return {"useSoon": use_soon, "inventory": inventory}


def _active_lots(
    session: Session, food_key: str, location: str | None
) -> list[InventoryLotRow]:
    statement = (
        select(InventoryLotRow)
        .where(
            InventoryLotRow.food_definition_id == food_key,
            InventoryLotRow.status == InventoryLotStatus.ACTIVE.value,
        )
        .order_by(
            InventoryLotRow.expires_on.is_(None),
            InventoryLotRow.expires_on,
            InventoryLotRow.id,
        )
    )
    if location is not None:
        statement = statement.where(InventoryLotRow.storage_location == location)
    return list(session.scalars(statement).all())


def _remaining_quantity(session: Session, food_key: str, location: str) -> Decimal:
    return sum(
        (lot.quantity for lot in _active_lots(session, food_key, location)),
        Decimal(0),
    )


def _allocation_lots(lots: list[InventoryLotRow]) -> list[AllocationLot]:
    return [
        AllocationLot(
            lot_id=lot.id,
            food_definition_id=lot.food_definition_id,
            available_quantity=lot.quantity,
            expires_on=lot.expires_on,
            status=InventoryLotStatus.ACTIVE,
        )
        for lot in lots
    ]


def _find_replay_event(session: Session, idempotency_key: str) -> ActivityEventRow | None:
    return session.scalar(
        select(ActivityEventRow).where(ActivityEventRow.idempotency_key == idempotency_key)
    )


def list_lots(session: Session, food_key: str, location: str) -> dict[str, list[dict[str, object]]]:
    rows = session.execute(
        select(InventoryLotRow, FoodDefinitionRow.base_unit)
        .join(FoodDefinitionRow, FoodDefinitionRow.id == InventoryLotRow.food_definition_id)
        .where(
            InventoryLotRow.food_definition_id == food_key,
            InventoryLotRow.storage_location == location,
            InventoryLotRow.status != InventoryLotStatus.DISCARDED.value,
        )
        .order_by(
            InventoryLotRow.expires_on.is_(None),
            InventoryLotRow.expires_on,
            InventoryLotRow.id,
        )
    ).all()
    return {
        "lots": [
            {
                "lotId": lot.id,
                "quantity": decimal_string(lot.quantity),
                "unit": base_unit,
                "location": lot.storage_location,
                "storedOn": lot.stored_on,
                "expiresOn": lot.expires_on,
                "expirySource": lot.expiry_source,
                "status": lot.status,
            }
            for lot, base_unit in rows
        ]
    }


@dataclass(frozen=True)
class EditLotCommand:
    idempotency_key: str
    lot_id: str
    quantity: Decimal | None
    location: str | None
    expires_on: date | None
    expires_on_provided: bool


@dataclass(frozen=True)
class EditLotResult:
    lot_id: str
    replayed: bool


def edit_lot(session: Session, command: EditLotCommand) -> EditLotResult:
    replay = _find_replay_event(session, command.idempotency_key)
    if replay is not None:
        return EditLotResult(lot_id=replay.display_snapshot["lotId"], replayed=True)

    lot = session.get(InventoryLotRow, command.lot_id)
    if lot is None:
        raise LotNotFoundError(f"unknown lot: {command.lot_id}")

    changes: dict[str, dict[str, str | None]] = {}
    quantity_delta = Decimal(0)
    if command.quantity is not None and command.quantity != lot.quantity:
        quantity_delta = command.quantity - lot.quantity
        changes["quantity"] = {
            "from": decimal_string(lot.quantity),
            "to": decimal_string(command.quantity),
        }
        lot.quantity = command.quantity
    if command.location is not None and command.location != lot.storage_location:
        changes["location"] = {"from": lot.storage_location, "to": command.location}
        lot.storage_location = command.location
    if command.expires_on_provided and command.expires_on != lot.expires_on:
        changes["expiresOn"] = {
            "from": lot.expires_on.isoformat() if lot.expires_on else None,
            "to": command.expires_on.isoformat() if command.expires_on else None,
        }
        lot.expires_on = command.expires_on

    reason = InventoryReason.EDIT.value
    if set(changes) == {"location"}:
        reason = InventoryReason.MOVE.value
    event = ActivityEventRow(
        id=str(uuid4()),
        event_type=reason,
        food_definition_id=lot.food_definition_id,
        quantity_delta=quantity_delta,
        display_snapshot={
            "lotId": lot.id,
            "foodKey": lot.food_definition_id,
            "changes": changes,
            "quantityDelta": decimal_string(quantity_delta),
        },
        idempotency_key=command.idempotency_key,
    )
    session.add(event)
    session.commit()
    return EditLotResult(lot_id=lot.id, replayed=False)


@dataclass(frozen=True)
class ReduceCommand:
    idempotency_key: str
    food_key: str
    location: str
    amount: Decimal
    unit: str


@dataclass(frozen=True)
class ReduceAllocation:
    lot_id: str
    deducted: Decimal


@dataclass(frozen=True)
class ReduceResult:
    new_quantity: Decimal
    allocations: tuple[ReduceAllocation, ...]
    replayed: bool


def reduce_inventory(session: Session, command: ReduceCommand) -> ReduceResult:
    replay = _find_replay_event(session, command.idempotency_key)
    if replay is not None:
        return ReduceResult(
            new_quantity=_remaining_quantity(session, command.food_key, command.location),
            allocations=(),
            replayed=True,
        )

    food = session.get(FoodDefinitionRow, command.food_key)
    if food is not None and food.base_unit != command.unit:
        raise ValueError("reduce unit must match the FoodDefinition base unit")

    lots = _active_lots(session, command.food_key, command.location)
    plan = allocate({command.food_key: command.amount}, _allocation_lots(lots))
    if plan.shortfalls:
        raise ValueError("insufficient quantity")

    lot_by_id = {lot.id: lot for lot in lots}
    transactions: list[InventoryTransactionRow] = []
    allocations: list[ReduceAllocation] = []
    for line in plan.lines:
        lot = lot_by_id[line.lot_id]
        lot.quantity -= line.delta
        if lot.quantity == 0:
            lot.status = InventoryLotStatus.DEPLETED.value
        transactions.append(
            InventoryTransactionRow(
                id=str(uuid4()),
                lot_id=lot.id,
                cooking_session_id=None,
                reason=InventoryReason.MANUAL_CONSUMPTION.value,
                quantity_delta=-line.delta,
                reversal_of=None,
                idempotency_key=f"{command.idempotency_key}:{lot.id}",
            )
        )
        allocations.append(ReduceAllocation(lot_id=lot.id, deducted=line.delta))

    event = ActivityEventRow(
        id=str(uuid4()),
        event_type=InventoryReason.MANUAL_CONSUMPTION.value,
        food_definition_id=command.food_key,
        quantity_delta=-command.amount,
        display_snapshot={
            "names": food.names if food is not None else {"en": command.food_key},
            "quantity": decimal_string(command.amount),
            "unit": command.unit,
            "location": command.location,
        },
        idempotency_key=command.idempotency_key,
    )
    session.add_all([*transactions, event])
    session.commit()
    return ReduceResult(
        new_quantity=_remaining_quantity(session, command.food_key, command.location),
        allocations=tuple(allocations),
        replayed=False,
    )


@dataclass(frozen=True)
class DiscardResult:
    lot_id: str
    replayed: bool


def discard_lot(session: Session, lot_id: str, idempotency_key: str) -> DiscardResult:
    replay = _find_replay_event(session, idempotency_key)
    if replay is not None:
        return DiscardResult(lot_id=replay.display_snapshot["lotId"], replayed=True)

    lot = session.get(InventoryLotRow, lot_id)
    if lot is None:
        raise LotNotFoundError(f"unknown lot: {lot_id}")
    if lot.status != InventoryLotStatus.ACTIVE.value:
        raise ValueError("only an ACTIVE lot can be discarded")

    food = session.get(FoodDefinitionRow, lot.food_definition_id)
    discarded_quantity = lot.quantity
    lot.status = InventoryLotStatus.DISCARDED.value
    transaction = InventoryTransactionRow(
        id=str(uuid4()),
        lot_id=lot.id,
        cooking_session_id=None,
        reason=InventoryReason.DISCARD.value,
        quantity_delta=-discarded_quantity,
        reversal_of=None,
        idempotency_key=f"{idempotency_key}:{lot.id}",
    )
    event = ActivityEventRow(
        id=str(uuid4()),
        event_type=InventoryReason.DISCARD.value,
        food_definition_id=lot.food_definition_id,
        quantity_delta=-discarded_quantity,
        display_snapshot={
            "lotId": lot.id,
            "names": food.names if food is not None else {"en": lot.food_definition_id},
            "quantity": decimal_string(discarded_quantity),
            "unit": food.base_unit if food is not None else "",
            "location": lot.storage_location,
        },
        idempotency_key=idempotency_key,
    )
    session.add_all([transaction, event])
    session.commit()
    return DiscardResult(lot_id=lot.id, replayed=False)


@dataclass(frozen=True)
class PreviewItem:
    food_key: str
    amount: Decimal
    unit: str


def cooking_preview(
    session: Session, items: list[PreviewItem], location: str | None
) -> dict[str, object]:
    lines: list[dict[str, object]] = []
    feasible = True
    for item in items:
        lots = _active_lots(session, item.food_key, location)
        plan = allocate({item.food_key: item.amount}, _allocation_lots(lots))
        shortfall = plan.shortfalls.get(item.food_key, Decimal(0))
        if shortfall > 0:
            feasible = False
        lot_by_id = {lot.id: lot for lot in lots}
        lines.append(
            {
                "foodKey": item.food_key,
                "requested": decimal_string(item.amount),
                "allocated": decimal_string(item.amount - shortfall),
                "shortfall": decimal_string(shortfall),
                "allocations": [
                    {
                        "lotId": line.lot_id,
                        "quantity": decimal_string(line.delta),
                        "lotQuantity": decimal_string(lot_by_id[line.lot_id].quantity),
                    }
                    for line in plan.lines
                    if line.lot_id in lot_by_id
                ],
            }
        )
    return {"lines": lines, "feasible": feasible}


@dataclass(frozen=True)
class CommitAllocation:
    lot_id: str
    quantity: Decimal
    lot_quantity: Decimal


@dataclass(frozen=True)
class CommitLine:
    food_key: str
    allocations: tuple[CommitAllocation, ...]


@dataclass(frozen=True)
class CookingCommitCommand:
    idempotency_key: str
    session_name: str | None
    lines: tuple[CommitLine, ...]


@dataclass(frozen=True)
class CookingCommitResult:
    session_id: str
    replayed: bool


def cooking_commit(session: Session, command: CookingCommitCommand) -> CookingCommitResult:
    replay = _find_replay_event(session, command.idempotency_key)
    if replay is not None:
        return CookingCommitResult(
            session_id=replay.display_snapshot["sessionId"], replayed=True
        )

    cooking_session_id = str(uuid4())
    # Validate every allocation against the live lots before mutating anything.
    deductions: list[tuple[InventoryLotRow, Decimal]] = []
    totals_by_food: dict[str, Decimal] = {}
    units_by_food: dict[str, str] = {}
    for line in command.lines:
        for allocation in line.allocations:
            lot = session.get(InventoryLotRow, allocation.lot_id)
            if lot is None or lot.food_definition_id != line.food_key:
                raise ValueError(f"unknown lot in commit: {allocation.lot_id}")
            if (
                lot.status != InventoryLotStatus.ACTIVE.value
                or lot.quantity != allocation.lot_quantity
                or lot.quantity < allocation.quantity
            ):
                raise ValueError("stale preview")
            deductions.append((lot, allocation.quantity))
            totals_by_food[line.food_key] = (
                totals_by_food.get(line.food_key, Decimal(0)) + allocation.quantity
            )
            if line.food_key not in units_by_food:
                food = session.get(FoodDefinitionRow, line.food_key)
                units_by_food[line.food_key] = food.base_unit if food is not None else ""

    transactions: list[InventoryTransactionRow] = []
    for lot, quantity in deductions:
        lot.quantity -= quantity
        if lot.quantity == 0:
            lot.status = InventoryLotStatus.DEPLETED.value
        transactions.append(
            InventoryTransactionRow(
                id=str(uuid4()),
                lot_id=lot.id,
                cooking_session_id=cooking_session_id,
                reason=InventoryReason.COOKING.value,
                quantity_delta=-quantity,
                reversal_of=None,
                idempotency_key=f"{command.idempotency_key}:{lot.id}",
            )
        )

    first_food = session.get(FoodDefinitionRow, command.lines[0].food_key)
    event = ActivityEventRow(
        id=str(uuid4()),
        event_type=InventoryReason.COOKING.value,
        food_definition_id=command.lines[0].food_key,
        quantity_delta=-sum(totals_by_food.values(), Decimal(0)),
        display_snapshot={
            "sessionId": cooking_session_id,
            "sessionName": command.session_name,
            "items": [
                {
                    "foodKey": food_key,
                    "quantity": decimal_string(quantity),
                    "unit": units_by_food[food_key],
                }
                for food_key, quantity in totals_by_food.items()
            ],
            "names": first_food.names if first_food is not None else {},
        },
        idempotency_key=command.idempotency_key,
    )
    session.add_all([*transactions, event])
    session.commit()
    return CookingCommitResult(session_id=cooking_session_id, replayed=False)
