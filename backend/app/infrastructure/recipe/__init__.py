"""Recipe provider adapters (fixture and live modes) and the safe-fetch boundary."""

from app.infrastructure.recipe.errors import (
    AdapterErrorCode,
    InvalidStructuredOutputError,
    NoGroundedSourcesError,
    RecipeAdapterError,
    RetrievalTimeoutError,
    SafeFetchError,
    SourceUnavailableError,
    UnknownMappingError,
)
from app.infrastructure.recipe.factory import RecipeAdapters, build_recipe_adapters
from app.infrastructure.recipe.fixture import (
    FixtureRetrievalAdapter,
    FixtureStructuringAdapter,
)
from app.infrastructure.recipe.retrieval import RetrievalAdapter, TavilyRetrievalAdapter
from app.infrastructure.recipe.safe_fetch import FetchedDocument, ensure_safe_url, safe_fetch
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedIngredient,
    NormalizedRecipe,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedSource,
    StructuringRequest,
    parse_normalized_recipe,
)
from app.infrastructure.recipe.structuring import (
    OpenAICompatibleStructuringAdapter,
    StructuringAdapter,
)

__all__ = [
    "AdapterErrorCode",
    "FetchedDocument",
    "FixtureRetrievalAdapter",
    "FixtureStructuringAdapter",
    "InvalidStructuredOutputError",
    "NoGroundedSourcesError",
    "NormalizedIngredient",
    "NormalizedRecipe",
    "OpenAICompatibleStructuringAdapter",
    "RECIPE_SCHEMA_VERSION",
    "RecipeAdapterError",
    "RecipeAdapters",
    "RetrievalAdapter",
    "RetrievalRequest",
    "RetrievalResponse",
    "RetrievalTimeoutError",
    "RetrievedSource",
    "SafeFetchError",
    "SourceUnavailableError",
    "StructuringAdapter",
    "StructuringRequest",
    "TavilyRetrievalAdapter",
    "UnknownMappingError",
    "build_recipe_adapters",
    "ensure_safe_url",
    "parse_normalized_recipe",
    "safe_fetch",
]
