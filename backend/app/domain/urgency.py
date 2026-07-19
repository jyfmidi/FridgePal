"""Date and urgency rules (contracts section 5).

All functions operate on local calendar dates (``datetime.date``) passed in by
the caller; nothing reads a clock, so results are deterministic and
time-zone-safe. Urgency is a derived display state, never a lifecycle status,
and never a food-safety claim.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import IntEnum

from app.domain.food_definition import ShelfLifeRule
from app.domain.inventory_lot import InventoryLot
from app.domain.types import ExpirySource, InventoryLotStatus


class UrgencyLevel(IntEnum):
    """Derived display urgency; a higher number is more urgent."""

    LATER = 1
    DUE_IN_3_TO_5_DAYS = 2
    DUE_IN_1_TO_2_DAYS = 3
    TODAY = 4
    PAST = 5


@dataclass(frozen=True)
class SuggestedExpiration:
    suggested_expires_on: date | None
    expiry_source: ExpirySource


def suggested_expiration(stored_on: date, rule: ShelfLifeRule | None) -> SuggestedExpiration:
    """Suggested expiration = stored_on + duration_days (calendar days)."""
    if rule is None:
        return SuggestedExpiration(suggested_expires_on=None, expiry_source=ExpirySource.NONE)
    return SuggestedExpiration(
        suggested_expires_on=stored_on + timedelta(days=rule.duration_days),
        expiry_source=ExpirySource.LIBRARY_DEFAULT,
    )


def lot_urgency(expires_on: date | None, today: date) -> UrgencyLevel:
    """Five-level urgency for one active lot, per the contract table."""
    if expires_on is None:
        return UrgencyLevel.LATER
    days_left = (expires_on - today).days
    if days_left < 0:
        return UrgencyLevel.PAST
    if days_left == 0:
        return UrgencyLevel.TODAY
    if days_left <= 2:
        return UrgencyLevel.DUE_IN_1_TO_2_DAYS
    if days_left <= 5:
        return UrgencyLevel.DUE_IN_3_TO_5_DAYS
    return UrgencyLevel.LATER


def aggregate_urgency(lots: Iterable[InventoryLot], today: date) -> UrgencyLevel | None:
    """Aggregated-tile urgency: the most urgent active lot's state.

    Returns ``None`` when there is no active lot to display.
    """
    levels = [
        lot_urgency(lot.expires_on, today)
        for lot in lots
        if lot.status is InventoryLotStatus.ACTIVE
    ]
    if not levels:
        return None
    return max(levels)
