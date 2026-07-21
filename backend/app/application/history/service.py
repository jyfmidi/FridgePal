"""History list and undo operations."""

from datetime import UTC
from uuid import uuid4

from sqlalchemy import String, cast, select
from sqlalchemy.orm import Session

from app.application.inventory.service import decimal_string
from app.domain.types import InventoryLotStatus, InventoryReason
from app.infrastructure.db.models import (
    ActivityEventRow,
    InventoryLotRow,
    InventoryTransactionRow,
)

REVERSIBLE_EVENT_TYPES = {"CHECK_IN", "MANUAL_CONSUMPTION", "DISCARD", "COOKING"}


def list_history(session: Session, user_id: str, limit: int = 50) -> list[dict[str, object]]:
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    rows = session.execute(
        select(ActivityEventRow)
        .where(ActivityEventRow.user_id == user_id)
        .order_by(ActivityEventRow.created_at.desc())
        .limit(limit)
    ).scalars().all()

    events = []
    for row in rows:
        reversible = _is_event_reversible(session, user_id, row)
        dt = row.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        events.append({
            "id": row.id,
            "eventType": row.event_type,
            "foodKey": row.food_definition_id,
            "quantityDelta": decimal_string(row.quantity_delta),
            "displaySnapshot": row.display_snapshot,
            "createdAt": dt.isoformat(),
            "reversible": reversible,
        })
    return events


def _is_event_reversible(session: Session, user_id: str, event: ActivityEventRow) -> bool:
    if event.event_type not in REVERSIBLE_EVENT_TYPES:
        return False
    existing_reversal = session.scalar(
        select(ActivityEventRow).where(
            ActivityEventRow.user_id == user_id,
            ActivityEventRow.event_type == InventoryReason.REVERSAL.value,
            cast(ActivityEventRow.display_snapshot["reversalOf"], String) == event.id,
        )
    )
    return existing_reversal is None


def undo_activity(session: Session, user_id: str, event_id: str, idempotency_key: str) -> dict[str, object]:
    original = session.scalar(
        select(ActivityEventRow).where(
            ActivityEventRow.id == event_id,
            ActivityEventRow.user_id == user_id,
        )
    )
    if original is None:
        raise ValueError("event not found")

    existing_reversal_by_event = session.scalar(
        select(ActivityEventRow).where(
            ActivityEventRow.user_id == user_id,
            ActivityEventRow.event_type == InventoryReason.REVERSAL.value,
            cast(ActivityEventRow.display_snapshot["reversalOf"], String) == event_id,
        )
    )
    existing_reversal_by_key = session.scalar(
        select(ActivityEventRow).where(
            ActivityEventRow.user_id == user_id,
            ActivityEventRow.event_type == InventoryReason.REVERSAL.value,
            ActivityEventRow.idempotency_key == idempotency_key,
        )
    )
    existing_reversal = existing_reversal_by_event or existing_reversal_by_key
    if existing_reversal is not None:
        return {"replayed": True, "eventId": existing_reversal.id}

    if original.event_type not in REVERSIBLE_EVENT_TYPES:
        raise ValueError("event type is not reversible")

    related_transactions = session.execute(
        select(InventoryTransactionRow).where(
            InventoryTransactionRow.user_id == user_id,
            (InventoryTransactionRow.idempotency_key == original.idempotency_key)
            | (InventoryTransactionRow.idempotency_key.like(f"{original.idempotency_key}:%")),
            InventoryTransactionRow.reversal_of.is_(None),
        )
    ).scalars().all()

    items: list[dict[str, object]] = []
    compensating_transactions: list[InventoryTransactionRow] = []

    for trans in related_transactions:
        lot = session.scalar(
            select(InventoryLotRow).where(
                InventoryLotRow.id == trans.lot_id,
                InventoryLotRow.user_id == user_id,
            )
        )
        if lot is None:
            raise ValueError(f"lot not found: {trans.lot_id}")

        compensating_delta = -trans.quantity_delta
        compensating_idem_key = f"undo:{event_id}:{trans.id}"
        if len(compensating_idem_key) > 200:
            compensating_idem_key = compensating_idem_key[:200]

        compensating = InventoryTransactionRow(
            id=str(uuid4()),
            lot_id=lot.id,
            cooking_session_id=None,
            reason=InventoryReason.REVERSAL.value,
            quantity_delta=compensating_delta,
            reversal_of=trans.id,
            idempotency_key=compensating_idem_key,
            user_id=user_id,
        )
        compensating_transactions.append(compensating)

        if trans.reason == InventoryReason.DISCARD.value:
            lot.status = InventoryLotStatus.ACTIVE.value
        else:
            lot.quantity -= trans.quantity_delta
            if lot.status == InventoryLotStatus.DISCARDED.value or (
                lot.status == InventoryLotStatus.DEPLETED.value and lot.quantity > 0
            ):
                lot.status = InventoryLotStatus.ACTIVE.value

        items.append({
            "lotId": lot.id,
            "quantityDelta": decimal_string(compensating_delta),
            "unit": "",
        })

    reversal_event = ActivityEventRow(
        id=str(uuid4()),
        event_type=InventoryReason.REVERSAL.value,
        food_definition_id=original.food_definition_id,
        quantity_delta=-original.quantity_delta,
        display_snapshot={
            "reversalOf": original.id,
            "originalEventType": original.event_type,
            "items": items,
        },
        idempotency_key=idempotency_key,
        user_id=user_id,
    )

    session.add_all([*compensating_transactions, reversal_event])
    session.commit()

    return {
        "eventId": reversal_event.id,
        "reversedTransactions": len(compensating_transactions),
        "replayed": False,
    }
