"""Adapter selection from deployment configuration (contract section 12).

``fixture`` mode returns deterministic offline adapters; ``live`` mode returns
the configured provider adapters and requires credentials. Swapping providers
means swapping these adapters only — domain and application code never see
provider details.
"""

from dataclasses import dataclass

from app.config import Settings
from app.infrastructure.recipe.fixture import (
    FixtureRetrievalAdapter,
    FixtureStructuringAdapter,
)
from app.infrastructure.recipe.retrieval import RetrievalAdapter, TavilyRetrievalAdapter
from app.infrastructure.recipe.structuring import (
    OpenAICompatibleStructuringAdapter,
    StructuringAdapter,
)

MODE_FIXTURE = "fixture"
MODE_LIVE = "live"


@dataclass(frozen=True)
class RecipeAdapters:
    """The adapter pair used by the recipe pipeline."""

    retrieval: RetrievalAdapter
    structuring: StructuringAdapter


def build_recipe_adapters(settings: Settings) -> RecipeAdapters:
    """Pick fixture or live adapters from ``settings.recipe_provider_mode``."""
    mode = settings.recipe_provider_mode
    if mode == MODE_FIXTURE:
        return RecipeAdapters(
            retrieval=FixtureRetrievalAdapter(),
            structuring=FixtureStructuringAdapter(),
        )
    if mode == MODE_LIVE:
        if not settings.search_api_key:
            raise ValueError("search_api_key is required in live provider mode")
        if not settings.llm_api_key:
            raise ValueError("llm_api_key is required in live provider mode")
        return RecipeAdapters(
            retrieval=TavilyRetrievalAdapter(
                api_key=settings.search_api_key,
                base_url=settings.search_base_url,
            ),
            structuring=OpenAICompatibleStructuringAdapter(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            ),
        )
    raise ValueError(f"unknown recipe provider mode: {mode!r}")
