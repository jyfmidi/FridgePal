"""Decimal quantity arithmetic and unit conversion rules (contracts sections 2 and 6.2)."""

from decimal import Decimal

import pytest
from app.domain.errors import IncompatibleUnitError
from app.domain.quantity import (
    CrossDimensionConversion,
    Quantity,
    convert,
    round_to_increment,
)


class TestQuantityValueObject:
    def test_rejects_negative_values(self) -> None:
        with pytest.raises(ValueError):
            Quantity(Decimal("-0.01"), "g")

    def test_zero_is_allowed(self) -> None:
        assert Quantity(Decimal("0"), "g").value == Decimal("0")

    def test_rejects_float_input(self) -> None:
        with pytest.raises(TypeError):
            Quantity(0.1, "g")  # type: ignore[arg-type]

    def test_rejects_unknown_unit(self) -> None:
        with pytest.raises(ValueError):
            Quantity(Decimal("1"), "furlong")

    def test_accepts_int_and_str_and_normalizes(self) -> None:
        assert Quantity(2, "g").value == Decimal("2")
        assert Quantity("2.50", "g").value == Decimal("2.50")

    def test_decimal_arithmetic_has_no_float_artifacts(self) -> None:
        a = Quantity("0.1", "g")
        b = Quantity("0.2", "g")
        assert (a + b).value == Decimal("0.3")
        assert (a + b).value != 0.1 + 0.2  # float artifact must not appear

    def test_addition_requires_same_unit(self) -> None:
        with pytest.raises(IncompatibleUnitError):
            Quantity("1", "g") + Quantity("1", "ml")

    def test_addition_result_stays_non_negative(self) -> None:
        with pytest.raises(ValueError):
            Quantity("1", "g") - Quantity("2", "g")

    def test_equality_compares_unit(self) -> None:
        assert Quantity("1", "g") != Quantity("1", "kg")
        assert Quantity("1", "g") == Quantity(Decimal("1"), "g")


class TestSameDimensionConversion:
    @pytest.mark.parametrize(
        ("value", "source", "target", "expected"),
        [
            ("1500", "g", "kg", "1.5"),
            ("1.5", "kg", "g", "1500"),
            ("250", "ml", "l", "0.25"),
            ("2", "l", "ml", "2000"),
            ("1", "kg", "kg", "1"),
            ("3", "piece", "clove", "3"),  # count dimension is shared
            ("2", "head", "bunch", "2"),
            ("0.5", "kg", "g", "500"),
            ("0.001", "l", "ml", "1"),
        ],
    )
    def test_compatible_units(self, value: str, source: str, target: str, expected: str) -> None:
        result = convert(Quantity(value, source), target)
        assert result.unit == target
        assert result.value == Decimal(expected)

    def test_conversion_is_exact(self) -> None:
        result = convert(Quantity("1", "kg"), "g")
        assert result.value == Decimal("1000")
        back = convert(result, "kg")
        assert back.value == Decimal("1")


class TestCrossDimensionConversion:
    GRAMS_PER_PIECE = CrossDimensionConversion(source_unit="piece", target_unit="g", factor="120")

    def test_count_to_mass_with_metadata(self) -> None:
        result = convert(Quantity("3", "piece"), "g", cross=self.GRAMS_PER_PIECE)
        assert result.value == Decimal("360")

    def test_mass_to_count_uses_inverse(self) -> None:
        result = convert(Quantity("360", "g"), "piece", cross=self.GRAMS_PER_PIECE)
        assert result.value == Decimal("3")

    def test_metadata_scales_between_prefixed_units(self) -> None:
        result = convert(Quantity("2", "piece"), "kg", cross=self.GRAMS_PER_PIECE)
        assert result.value == Decimal("0.24")

    def test_cross_dimension_without_metadata_is_rejected(self) -> None:
        with pytest.raises(IncompatibleUnitError):
            convert(Quantity("3", "piece"), "g")
        with pytest.raises(IncompatibleUnitError):
            convert(Quantity("500", "g"), "ml")

    def test_mass_to_volume_never_invented(self) -> None:
        # g -> ml is cross-dimension too; without explicit density it must fail.
        with pytest.raises(IncompatibleUnitError):
            convert(Quantity("100", "g"), "ml", cross=self.GRAMS_PER_PIECE)

    def test_metadata_with_wrong_units_is_rejected(self) -> None:
        with pytest.raises(IncompatibleUnitError):
            convert(Quantity("3", "piece"), "ml", cross=self.GRAMS_PER_PIECE)
        with pytest.raises(IncompatibleUnitError):
            convert(Quantity("3", "clove"), "g", cross=self.GRAMS_PER_PIECE)

    def test_count_to_volume_with_metadata(self) -> None:
        ml_per_piece = CrossDimensionConversion(source_unit="piece", target_unit="ml", factor="50")
        result = convert(Quantity("2", "piece"), "ml", cross=ml_per_piece)
        assert result.value == Decimal("100")


class TestRounding:
    @pytest.mark.parametrize(
        ("value", "increment", "expected"),
        [
            ("1234", "5", "1235"),
            ("1232", "5", "1230"),
            ("1.234", "0.05", "1.25"),
            ("1.225", "0.05", "1.25"),  # half up
            ("1.224", "0.05", "1.2"),
            ("0.04", "0.05", "0.05"),
            ("10", "1", "10"),
            ("2.5", "1", "3"),
        ],
    )
    def test_round_to_increment(self, value: str, increment: str, expected: str) -> None:
        assert round_to_increment(Decimal(value), Decimal(increment)) == Decimal(expected)

    def test_non_positive_increment_rejected(self) -> None:
        with pytest.raises(ValueError):
            round_to_increment(Decimal("1"), Decimal("0"))
        with pytest.raises(ValueError):
            round_to_increment(Decimal("1"), Decimal("-1"))


class TestGeneratedArithmeticInvariants:
    def test_add_then_convert_roundtrip(self) -> None:
        # Property-style: generated cases keep Decimal exactness and non-negativity.
        for i in range(1, 50):
            a = Quantity(Decimal(i) / Decimal(7), "g")
            b = Quantity(Decimal(i) / Decimal(11), "g")
            total = a + b
            expected = Decimal(i) / Decimal(7) + Decimal(i) / Decimal(11)
            assert total.value == expected
            in_kg = convert(total, "kg")
            assert in_kg.value == expected / Decimal(1000)
            back = convert(in_kg, "g")
            assert back.value == total.value
