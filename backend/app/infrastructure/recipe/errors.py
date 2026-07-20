"""Classified recipe provider errors (contracts section 10, ERR-01..ERR-05).

Adapter failures carry a stable code so the application layer can map them to
the documented user experience without inspecting provider-specific exceptions.
"""

from enum import StrEnum


class AdapterErrorCode(StrEnum):
    """Stable error codes from the error contract."""

    RETRIEVAL_TIMEOUT = "ERR-01"
    INVALID_STRUCTURED_OUTPUT = "ERR-02"
    NO_GROUNDED_SOURCES = "ERR-03"
    SOURCE_UNAVAILABLE = "ERR-04"
    UNKNOWN_MAPPING = "ERR-05"


class RecipeAdapterError(Exception):
    """Base class for classified adapter failures."""

    code: AdapterErrorCode

    def __init__(self, message: str, *, retriable: bool = False) -> None:
        super().__init__(message)
        self.retriable = retriable


class RetrievalTimeoutError(RecipeAdapterError):
    """ERR-01: retrieval or structuring provider timed out."""

    code = AdapterErrorCode.RETRIEVAL_TIMEOUT

    def __init__(self, message: str = "recipe provider timed out") -> None:
        super().__init__(message, retriable=True)


class InvalidStructuredOutputError(RecipeAdapterError):
    """ERR-02: structured output failed validation after the repair attempt."""

    code = AdapterErrorCode.INVALID_STRUCTURED_OUTPUT


class NoGroundedSourcesError(RecipeAdapterError):
    """ERR-03: retrieval returned no grounded sources."""

    code = AdapterErrorCode.NO_GROUNDED_SOURCES

    def __init__(self, message: str = "no grounded recipe sources found") -> None:
        super().__init__(message, retriable=True)


class SourceUnavailableError(RecipeAdapterError):
    """ERR-04: a source or provider endpoint is unavailable."""

    code = AdapterErrorCode.SOURCE_UNAVAILABLE

    def __init__(self, message: str = "recipe source unavailable") -> None:
        super().__init__(message, retriable=True)


class UnknownMappingError(RecipeAdapterError):
    """ERR-05: ingredient mapping or unit could not be resolved."""

    code = AdapterErrorCode.UNKNOWN_MAPPING


class SafeFetchError(Exception):
    """The safe-fetch boundary rejected a URL or response (fails closed)."""
