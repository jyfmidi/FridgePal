"""Versioned internal retrieval and normalized-recipe schemas (contract section 8).

Retrieval returns allow-listed source metadata only — never raw page bodies.
Structuring returns a versioned normalized recipe; ``parse_normalized_recipe``
is the single validation gate and rejects unknown schema versions, missing
required structure, non-allow-listed citations, invalid quantities, and unsafe
URLs. Provider payloads never cross this boundary unvalidated.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.recipe import PROVENANCE_AI_INFERENCE, PROVENANCE_SOURCE
from app.domain.types import IngredientAmountKind, RecipeAnalysisStatus
from app.infrastructure.recipe.errors import InvalidStructuredOutputError

RECIPE_SCHEMA_VERSION = "1.0"

_VALID_PROVENANCE = {PROVENANCE_SOURCE, PROVENANCE_AI_INFERENCE}


def format_quantity(quantity: Decimal) -> str:
    """Plain decimal string without scientific notation or trailing zeros."""
    text = format(quantity, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def ensure_http_url(url: str) -> str:
    """Only http/https URLs with a host are safe to carry or fetch."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"unsafe URL: {url!r}")
    return url


class RetrievalIngredientInput(BaseModel):
    """One selected food fact for retrieval: name, quantity, unit."""

    model_config = ConfigDict(frozen=True)

    food_definition_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1)


class RetrievalRequest(BaseModel):
    """Deterministic retrieval input (contract 8.1).

    Built from selected ingredient names, quantities, and serving count.
    Urgency stays in internal snapshots and never enters the search query.
    """

    model_config = ConfigDict(frozen=True)

    ingredients: list[RetrievalIngredientInput] = Field(min_length=1)
    servings: int = Field(ge=1)
    locale: str = "en"
    max_candidates: int = Field(default=8, ge=1, le=20)
    timeout_seconds: float = Field(default=10.0, gt=0)


class RetrievedSource(BaseModel):
    """Allow-listed source metadata (contract 8.2). No raw page content."""

    model_config = ConfigDict(frozen=True)

    url: str
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    retrieved_at: datetime
    base_yield: int | None = Field(default=None, ge=1)
    used_food_ids: list[str] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def _url_is_safe(cls, value: str) -> str:
        return ensure_http_url(value)


class RetrievalResponse(BaseModel):
    """Sources plus diagnostics that contain no secrets or raw page archives."""

    model_config = ConfigDict(frozen=True)

    sources: list[RetrievedSource]
    diagnostics: dict[str, str] = Field(default_factory=dict)


class StructuringRequest(BaseModel):
    """Sources plus selected-food facts handed to the structuring adapter."""

    model_config = ConfigDict(frozen=True)

    sources: list[RetrievedSource] = Field(min_length=1)
    ingredients: list[RetrievalIngredientInput] = Field(min_length=1)
    servings: int = Field(ge=1)
    locale: str = "en"
    timeout_seconds: float = Field(default=30.0, gt=0)


class NormalizedIngredient(BaseModel):
    """One normalized recipe ingredient (contract 8.3, DE-07 fields)."""

    model_config = ConfigDict(frozen=True)

    original_text: str = Field(min_length=1)
    amount_kind: IngredientAmountKind
    amount: Decimal | None = None
    unit: str | None = None
    mapping_suggestion: str | None = None
    provenance: str = PROVENANCE_SOURCE
    needs_review: bool = False

    @field_validator("provenance")
    @classmethod
    def _provenance_is_known(cls, value: str) -> str:
        if value not in _VALID_PROVENANCE:
            raise ValueError(f"unknown provenance: {value!r}")
        return value

    @model_validator(mode="after")
    def _amount_matches_kind(self) -> "NormalizedIngredient":
        if self.amount_kind is IngredientAmountKind.NUMERIC:
            if self.amount is None:
                raise ValueError("NUMERIC ingredient requires an amount")
            if self.amount < 0:
                raise ValueError("amount must be non-negative")
        return self


class NormalizedRecipe(BaseModel):
    """Versioned normalized recipe returned by every structuring adapter."""

    model_config = ConfigDict(frozen=True)

    schema_version: str
    title: str = Field(min_length=1)
    description: str | None = None
    base_yield: int = Field(ge=1)
    ingredients: list[NormalizedIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    source_urls: list[str] = Field(default_factory=list)
    analysis_status: RecipeAnalysisStatus
    warnings: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _schema_version_is_supported(cls, value: str) -> str:
        if value != RECIPE_SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version: {value!r}")
        return value

    @field_validator("steps")
    @classmethod
    def _steps_are_non_empty(cls, value: list[str]) -> list[str]:
        if any(not step.strip() for step in value):
            raise ValueError("steps must be non-empty strings")
        return value

    @model_validator(mode="after")
    def _status_is_terminal(self) -> "NormalizedRecipe":
        if self.analysis_status not in (
            RecipeAnalysisStatus.READY,
            RecipeAnalysisStatus.PARTIAL,
        ):
            raise ValueError("analysis status must be READY or PARTIAL")
        return self


def parse_normalized_recipe(payload: Any, allowed_urls: set[str]) -> NormalizedRecipe:
    """Validate untrusted structuring output against the schema and allow-list.

    Raises ``InvalidStructuredOutputError`` (ERR-02) for unknown schema
    versions, missing required structure, non-allow-listed citations, invalid
    quantities, or unsafe URLs.
    """
    if not isinstance(payload, dict):
        raise InvalidStructuredOutputError("structured output is not a JSON object")
    try:
        recipe = NormalizedRecipe.model_validate(payload)
    except ValueError as exc:
        raise InvalidStructuredOutputError(f"invalid structured output: {exc}") from exc
    for url in recipe.source_urls:
        try:
            ensure_http_url(url)
        except ValueError as exc:
            raise InvalidStructuredOutputError(f"unsafe source URL: {url!r}") from exc
        if url not in allowed_urls:
            raise InvalidStructuredOutputError(
                f"source citation outside the retrieval allow-list: {url!r}"
            )
    return recipe
