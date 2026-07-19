"""Domain error types shared by the pure domain modules."""


class DomainError(Exception):
    """Base class for all domain rule violations."""


class IncompatibleUnitError(DomainError):
    """Raised when a unit conversion has no deterministic rule or metadata."""


class InvalidMultiplierError(DomainError):
    """Raised when a portion multiplier is not a positive decimal."""
