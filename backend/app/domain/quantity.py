"""Decimal quantity value object and deterministic unit conversion (contracts sections 2, 6.2).

Persisted quantities are always ``decimal.Decimal`` in a canonical base unit;
floats are rejected at the boundary. Same-dimension conversion (mass, volume,
count) is deterministic. Cross-dimension conversion (e.g. count to mass) is
only possible through explicit per-food conversion metadata and is never
invented.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Self

from app.domain.errors import IncompatibleUnitError

DecimalLike = Decimal | int | str


class UnitDimension(Enum):
    MASS = "MASS"
    VOLUME = "VOLUME"
    COUNT = "COUNT"


# unit -> (dimension, multiplier to the canonical base unit of that dimension)
_UNIT_TABLE: dict[str, tuple[UnitDimension, Decimal]] = {
    "g": (UnitDimension.MASS, Decimal("1")),
    "kg": (UnitDimension.MASS, Decimal("1000")),
    "ml": (UnitDimension.VOLUME, Decimal("1")),
    "l": (UnitDimension.VOLUME, Decimal("1000")),
    "piece": (UnitDimension.COUNT, Decimal("1")),
    "clove": (UnitDimension.COUNT, Decimal("1")),
    "head": (UnitDimension.COUNT, Decimal("1")),
    "bunch": (UnitDimension.COUNT, Decimal("1")),
}


def _coerce_decimal(value: DecimalLike) -> Decimal:
    if isinstance(value, (bool, float)):
        raise TypeError("quantities must be Decimal/int/str, never float")
    if isinstance(value, Decimal):
        return value
    return Decimal(value)


def is_known_unit(unit: str) -> bool:
    return unit in _UNIT_TABLE


def unit_dimension(unit: str) -> UnitDimension:
    try:
        return _UNIT_TABLE[unit][0]
    except KeyError:
        raise ValueError(f"unknown unit: {unit!r}") from None


@dataclass(frozen=True)
class Quantity:
    """A non-negative decimal amount in a known unit."""

    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        coerced = _coerce_decimal(self.value)
        if coerced < 0:
            raise ValueError("quantity must be non-negative")
        object.__setattr__(self, "value", coerced)
        if not is_known_unit(self.unit):
            raise ValueError(f"unknown unit: {self.unit!r}")

    def __add__(self, other: Self) -> Self:
        self._require_same_unit(other)
        return type(self)(self.value + other.value, self.unit)

    def __sub__(self, other: Self) -> Self:
        self._require_same_unit(other)
        return type(self)(self.value - other.value, self.unit)

    def _require_same_unit(self, other: Self) -> None:
        if not isinstance(other, Quantity) or self.unit != other.unit:
            raise IncompatibleUnitError(
                "arithmetic requires identical units; convert explicitly first"
            )


@dataclass(frozen=True)
class CrossDimensionConversion:
    """Explicit conversion metadata: ``1 source_unit == factor target_unit``.

    The two units must belong to different dimensions; within-dimension
    conversions are handled deterministically without metadata.
    """

    source_unit: str
    target_unit: str
    factor: Decimal

    def __post_init__(self) -> None:
        if unit_dimension(self.source_unit) is unit_dimension(self.target_unit):
            raise ValueError("cross-dimension metadata must connect two different dimensions")
        coerced = _coerce_decimal(self.factor)
        if coerced <= 0:
            raise ValueError("conversion factor must be positive")
        object.__setattr__(self, "factor", coerced)


def convert(
    quantity: Quantity,
    target_unit: str,
    *,
    cross: CrossDimensionConversion | None = None,
) -> Quantity:
    """Convert ``quantity`` to ``target_unit``.

    Same-dimension conversions are exact. Cross-dimension conversions require
    ``cross`` metadata whose ``source_unit``/``target_unit`` exactly matches the
    requested direction (or its inverse); anything else raises
    :class:`IncompatibleUnitError` rather than guessing.
    """
    if not is_known_unit(target_unit):
        raise ValueError(f"unknown unit: {target_unit!r}")
    if quantity.unit == target_unit:
        return quantity
    source_dimension = unit_dimension(quantity.unit)
    target_dimension = unit_dimension(target_unit)
    if source_dimension is target_dimension:
        base_value = quantity.value * _UNIT_TABLE[quantity.unit][1]
        return Quantity(base_value / _UNIT_TABLE[target_unit][1], target_unit)
    if cross is None:
        raise IncompatibleUnitError(
            f"no conversion from {quantity.unit!r} to {target_unit!r} without explicit metadata"
        )
    if quantity.unit == cross.source_unit and unit_dimension(target_unit) is unit_dimension(
        cross.target_unit
    ):
        in_cross_target = Quantity(quantity.value * cross.factor, cross.target_unit)
        return convert(in_cross_target, target_unit)
    if quantity.unit == cross.target_unit and unit_dimension(target_unit) is unit_dimension(
        cross.source_unit
    ):
        in_cross_source = Quantity(quantity.value / cross.factor, cross.source_unit)
        return convert(in_cross_source, target_unit)
    raise IncompatibleUnitError(
        f"conversion metadata {cross.source_unit!r}->{cross.target_unit!r} does not apply "
        f"to {quantity.unit!r}->{target_unit!r}"
    )


def round_to_increment(value: Decimal, increment: Decimal) -> Decimal:
    """Round ``value`` (half-up) to the nearest multiple of ``increment``.

    Used for display only; internal values keep full Decimal precision.
    """
    if increment <= 0:
        raise ValueError("rounding increment must be positive")
    steps = (value / increment).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return steps * increment
