"""Deduction allocation preview: selected-first, FEFO, shortfalls, invariants (section 9)."""

import random
from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.domain.allocation import AllocationLot, allocate
from app.domain.types import InventoryLotStatus

TODAY = date(2025, 3, 10)
FOOD = "food-tofu"
OTHER = "food-milk"


def lot(
    lot_id: str,
    quantity: str,
    expires_offset: int | None,
    food: str = FOOD,
    status: InventoryLotStatus = InventoryLotStatus.ACTIVE,
) -> AllocationLot:
    expires_on = None if expires_offset is None else TODAY + timedelta(days=expires_offset)
    return AllocationLot(
        lot_id=lot_id,
        food_definition_id=food,
        available_quantity=Decimal(quantity),
        expires_on=expires_on,
        status=status,
    )


class TestFefoOrder:
    def test_earliest_expiry_allocates_first(self) -> None:
        lots = [
            lot("lot-late", "5", 10),
            lot("lot-early", "5", 1),
            lot("lot-mid", "5", 5),
        ]
        plan = allocate({FOOD: Decimal("7")}, lots)
        assert [(line.lot_id, line.delta) for line in plan.lines] == [
            ("lot-early", Decimal("5")),
            ("lot-mid", Decimal("2")),
        ]
        assert plan.shortfalls == {}

    def test_no_date_lots_go_last(self) -> None:
        lots = [
            lot("lot-nodate", "5", None),
            lot("lot-dated", "5", 30),
        ]
        plan = allocate({FOOD: Decimal("6")}, lots)
        assert [line.lot_id for line in plan.lines] == ["lot-dated", "lot-nodate"]

    def test_ties_break_by_lot_id_for_determinism(self) -> None:
        lots = [lot("lot-b", "5", 3), lot("lot-a", "5", 3)]
        plan = allocate({FOOD: Decimal("7")}, lots)
        assert [line.lot_id for line in plan.lines] == ["lot-a", "lot-b"]

    def test_non_active_lots_are_skipped(self) -> None:
        lots = [
            lot("lot-depleted", "5", 1, status=InventoryLotStatus.DEPLETED),
            lot("lot-discarded", "5", 2, status=InventoryLotStatus.DISCARDED),
            lot("lot-active", "5", 9),
        ]
        plan = allocate({FOOD: Decimal("4")}, lots)
        assert [line.lot_id for line in plan.lines] == ["lot-active"]

    def test_other_foods_lots_are_ignored(self) -> None:
        lots = [lot("lot-milk", "5", 1, food=OTHER), lot("lot-tofu", "5", 5)]
        plan = allocate({FOOD: Decimal("3")}, lots)
        assert [line.lot_id for line in plan.lines] == ["lot-tofu"]


class TestSelectedLotsFirst:
    def test_selected_lot_beats_earlier_expiry(self) -> None:
        lots = [
            lot("lot-early", "5", 1),
            lot("lot-selected", "5", 10),
        ]
        plan = allocate({FOOD: Decimal("4")}, lots, selected_lot_ids=["lot-selected"])
        assert [(line.lot_id, line.delta) for line in plan.lines] == [
            ("lot-selected", Decimal("4"))
        ]

    def test_selected_partial_then_fefo_for_remainder(self) -> None:
        lots = [
            lot("lot-early", "5", 1),
            lot("lot-selected", "3", 10),
        ]
        plan = allocate({FOOD: Decimal("6")}, lots, selected_lot_ids=["lot-selected"])
        assert [(line.lot_id, line.delta) for line in plan.lines] == [
            ("lot-selected", Decimal("3")),
            ("lot-early", Decimal("3")),
        ]

    def test_stale_selected_lot_falls_back_to_fefo(self) -> None:
        lots = [
            lot("lot-selected-gone", "5", 1, status=InventoryLotStatus.DEPLETED),
            lot("lot-fresh", "5", 9),
        ]
        plan = allocate({FOOD: Decimal("2")}, lots, selected_lot_ids=["lot-selected-gone"])
        assert [line.lot_id for line in plan.lines] == ["lot-fresh"]

    def test_selected_lot_of_other_food_is_ignored(self) -> None:
        lots = [
            lot("lot-milk", "5", 1, food=OTHER),
            lot("lot-tofu", "5", 5),
        ]
        plan = allocate({FOOD: Decimal("2")}, lots, selected_lot_ids=["lot-milk"])
        assert [line.lot_id for line in plan.lines] == ["lot-tofu"]

    def test_multiple_selected_lots_follow_given_order(self) -> None:
        lots = [
            lot("lot-a", "2", 1),
            lot("lot-b", "2", 2),
            lot("lot-c", "2", 3),
        ]
        plan = allocate({FOOD: Decimal("5")}, lots, selected_lot_ids=["lot-c", "lot-a"])
        assert [line.lot_id for line in plan.lines] == ["lot-c", "lot-a", "lot-b"]


class TestShortfallsAndCaps:
    def test_demand_above_availability_reports_shortfall(self) -> None:
        lots = [lot("lot-a", "3", 1), lot("lot-b", "2", 2)]
        plan = allocate({FOOD: Decimal("9")}, lots)
        assert sum((line.delta for line in plan.lines), Decimal("0")) == Decimal("5")
        assert plan.shortfalls == {FOOD: Decimal("4")}

    def test_zero_availability_lot_produces_no_line(self) -> None:
        lots = [lot("lot-empty", "0", 1), lot("lot-full", "4", 2)]
        plan = allocate({FOOD: Decimal("2")}, lots)
        assert [line.lot_id for line in plan.lines] == ["lot-full"]

    def test_per_food_shortfalls_are_independent(self) -> None:
        lots = [lot("lot-tofu", "10", 1), lot("lot-milk", "1", 1, food=OTHER)]
        plan = allocate({FOOD: Decimal("3"), OTHER: Decimal("5")}, lots)
        assert plan.shortfalls == {OTHER: Decimal("4")}

    def test_negative_demand_rejected(self) -> None:
        with pytest.raises(ValueError):
            allocate({FOOD: Decimal("-1")}, [])

    def test_zero_demand_is_noop(self) -> None:
        plan = allocate({FOOD: Decimal("0")}, [lot("lot-a", "5", 1)])
        assert plan.lines == ()
        assert plan.shortfalls == {}


class TestGeneratedInvariants:
    def test_allocation_never_negative_never_exceeds_bounds(self) -> None:
        rng = random.Random(20250310)
        for _ in range(500):
            foods = ["food-a", "food-b", "food-c"]
            lots = [
                AllocationLot(
                    lot_id=f"lot-{i}",
                    food_definition_id=rng.choice(foods),
                    available_quantity=Decimal(rng.randint(0, 20)),
                    expires_on=(
                        None if rng.random() < 0.2 else TODAY + timedelta(days=rng.randint(-5, 30))
                    ),
                    status=rng.choice(list(InventoryLotStatus)),
                )
                for i in range(rng.randint(0, 8))
            ]
            demands = {food: Decimal(rng.randint(0, 25)) for food in foods if rng.random() < 0.8}
            selected = [candidate.lot_id for candidate in lots if rng.random() < 0.3]
            plan = allocate(demands, lots, selected_lot_ids=selected)

            lot_by_id = {candidate.lot_id: candidate for candidate in lots}
            per_lot: dict[str, Decimal] = {}
            per_food_allocated: dict[str, Decimal] = {}
            for line in plan.lines:
                assert line.delta > 0
                candidate = lot_by_id[line.lot_id]
                assert candidate.status is InventoryLotStatus.ACTIVE
                per_lot[line.lot_id] = per_lot.get(line.lot_id, Decimal("0")) + line.delta
                per_food_allocated[candidate.food_definition_id] = (
                    per_food_allocated.get(candidate.food_definition_id, Decimal("0")) + line.delta
                )
            # Never allocate more than a lot holds; remainder never negative.
            for lot_id, total in per_lot.items():
                assert total <= lot_by_id[lot_id].available_quantity
            # Never allocate more than demanded; shortfall closes the gap exactly.
            for food, demand in demands.items():
                allocated = per_food_allocated.get(food, Decimal("0"))
                assert allocated <= demand
                shortfall = plan.shortfalls.get(food, Decimal("0"))
                assert shortfall >= 0
                assert allocated + shortfall == demand
            # No shortfall without exhausting availability.
            for food, shortfall in plan.shortfalls.items():
                if shortfall > 0:
                    availability = sum(
                        (
                            candidate.available_quantity
                            for candidate in lots
                            if candidate.food_definition_id == food
                            and candidate.status is InventoryLotStatus.ACTIVE
                        ),
                        Decimal("0"),
                    )
                    assert per_food_allocated.get(food, Decimal("0")) == min(
                        demands[food], availability
                    )
