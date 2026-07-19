"""Shelf-life calendar arithmetic and five-level urgency boundaries (contracts section 5)."""

from datetime import date, timedelta

import pytest
from app.domain.food_definition import ShelfLifeRule
from app.domain.inventory_lot import InventoryLot
from app.domain.types import ExpirySource, InventoryLotStatus, StorageLocation
from app.domain.urgency import (
    UrgencyLevel,
    aggregate_urgency,
    lot_urgency,
    suggested_expiration,
)

FOOD_ID = "food-milk"
TODAY = date(2025, 3, 10)


def rule(days: int) -> ShelfLifeRule:
    return ShelfLifeRule(
        food_definition_id=FOOD_ID,
        storage_location=StorageLocation.FRIDGE,
        duration_days=days,
    )


def make_lot(
    lot_id: str,
    expires_on: date | None,
    status: InventoryLotStatus = InventoryLotStatus.ACTIVE,
) -> InventoryLot:
    return InventoryLot(
        id=lot_id,
        food_definition_id=FOOD_ID,
        quantity="1",
        storage_location=StorageLocation.FRIDGE,
        stored_on=TODAY,
        expires_on=expires_on,
        expiry_source=ExpirySource.LIBRARY_DEFAULT,
        status=status,
    )


class TestSuggestedExpiration:
    def test_simple_addition(self) -> None:
        result = suggested_expiration(date(2025, 3, 10), rule(7))
        assert result.suggested_expires_on == date(2025, 3, 17)
        assert result.expiry_source is ExpirySource.LIBRARY_DEFAULT

    def test_month_rollover_uses_calendar_days(self) -> None:
        assert suggested_expiration(date(2025, 1, 30), rule(5)).suggested_expires_on == date(
            2025, 2, 4
        )

    def test_leap_year_boundary(self) -> None:
        assert suggested_expiration(date(2024, 2, 28), rule(2)).suggested_expires_on == date(
            2024, 3, 1
        )

    def test_non_leap_year_boundary(self) -> None:
        assert suggested_expiration(date(2025, 2, 28), rule(2)).suggested_expires_on == date(
            2025, 3, 2
        )

    def test_year_rollover(self) -> None:
        assert suggested_expiration(date(2025, 12, 30), rule(3)).suggested_expires_on == date(
            2026, 1, 2
        )

    def test_zero_duration_expires_on_stored_date(self) -> None:
        assert suggested_expiration(date(2025, 3, 10), rule(0)).suggested_expires_on == date(
            2025, 3, 10
        )

    def test_missing_rule_produces_no_suggestion(self) -> None:
        result = suggested_expiration(date(2025, 3, 10), None)
        assert result.suggested_expires_on is None
        assert result.expiry_source is ExpirySource.NONE

    def test_negative_duration_rejected(self) -> None:
        with pytest.raises(ValueError):
            rule(-1)


class TestLotUrgency:
    @pytest.mark.parametrize(
        ("offset_days", "expected"),
        [
            (-30, UrgencyLevel.PAST),
            (-1, UrgencyLevel.PAST),
            (0, UrgencyLevel.TODAY),
            (1, UrgencyLevel.DUE_IN_1_TO_2_DAYS),
            (2, UrgencyLevel.DUE_IN_1_TO_2_DAYS),
            (3, UrgencyLevel.DUE_IN_3_TO_5_DAYS),
            (4, UrgencyLevel.DUE_IN_3_TO_5_DAYS),
            (5, UrgencyLevel.DUE_IN_3_TO_5_DAYS),
            (6, UrgencyLevel.LATER),
            (30, UrgencyLevel.LATER),
        ],
    )
    def test_boundaries(self, offset_days: int, expected: UrgencyLevel) -> None:
        expires_on = TODAY + timedelta(days=offset_days)
        assert lot_urgency(expires_on, TODAY) is expected

    def test_missing_date_is_later(self) -> None:
        assert lot_urgency(None, TODAY) is UrgencyLevel.LATER

    def test_exhaustive_offsets_match_table(self) -> None:
        # Property-style: every offset in a wide window maps exactly per the doc table.
        for offset in range(-365, 366):
            expires_on = TODAY + timedelta(days=offset)
            level = lot_urgency(expires_on, TODAY)
            if offset < 0:
                assert level is UrgencyLevel.PAST
            elif offset == 0:
                assert level is UrgencyLevel.TODAY
            elif offset <= 2:
                assert level is UrgencyLevel.DUE_IN_1_TO_2_DAYS
            elif offset <= 5:
                assert level is UrgencyLevel.DUE_IN_3_TO_5_DAYS
            else:
                assert level is UrgencyLevel.LATER

    def test_result_depends_only_on_local_dates(self) -> None:
        # Same calendar dates always give the same level; no hidden clock involved.
        assert lot_urgency(date(2025, 3, 11), TODAY) is UrgencyLevel.DUE_IN_1_TO_2_DAYS
        assert lot_urgency(date(2025, 3, 11), TODAY) is lot_urgency(date(2025, 3, 11), TODAY)


class TestAggregateUrgency:
    def test_most_urgent_active_lot_wins(self) -> None:
        lots = [
            make_lot("lot-later", TODAY + timedelta(days=20)),
            make_lot("lot-today", TODAY),
            make_lot("lot-soon", TODAY + timedelta(days=2)),
        ]
        assert aggregate_urgency(lots, TODAY) is UrgencyLevel.TODAY

    def test_past_is_most_urgent(self) -> None:
        lots = [
            make_lot("lot-today", TODAY),
            make_lot("lot-past", TODAY - timedelta(days=1)),
        ]
        assert aggregate_urgency(lots, TODAY) is UrgencyLevel.PAST

    def test_non_active_lots_are_ignored(self) -> None:
        lots = [
            make_lot("lot-depleted", TODAY - timedelta(days=3), InventoryLotStatus.DEPLETED),
            make_lot("lot-discarded", TODAY, InventoryLotStatus.DISCARDED),
            make_lot("lot-active", TODAY + timedelta(days=4)),
        ]
        assert aggregate_urgency(lots, TODAY) is UrgencyLevel.DUE_IN_3_TO_5_DAYS

    def test_no_active_lots_returns_none(self) -> None:
        lots = [make_lot("lot-depleted", TODAY, InventoryLotStatus.DEPLETED)]
        assert aggregate_urgency(lots, TODAY) is None
        assert aggregate_urgency([], TODAY) is None

    def test_missing_dates_are_least_urgent(self) -> None:
        lots = [
            make_lot("lot-nodate", None),
            make_lot("lot-far", TODAY + timedelta(days=10)),
        ]
        assert aggregate_urgency(lots, TODAY) is UrgencyLevel.LATER
