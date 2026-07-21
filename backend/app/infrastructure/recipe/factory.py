from dataclasses import dataclass

from app.config import Settings
from app.infrastructure.recipe.fixture import FixtureStructuringAdapter
from app.infrastructure.recipe.structuring import (
    OpenAICompatibleStructuringAdapter,
    StructuringAdapter,
)

MODE_FIXTURE = "fixture"
MODE_LIVE = "live"


@dataclass(frozen=True)
class RecipeAdapters:
    structuring: StructuringAdapter


def build_recipe_adapters(settings: Settings) -> RecipeAdapters:
    mode = settings.recipe_provider_mode
    if mode == MODE_FIXTURE:
        return RecipeAdapters(structuring=FixtureStructuringAdapter())
    if mode == MODE_LIVE:
        if not settings.llm_api_key:
            raise ValueError("llm_api_key is required in live provider mode")
        return RecipeAdapters(
            structuring=OpenAICompatibleStructuringAdapter(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            ),
        )
    raise ValueError(f"unknown recipe provider mode: {mode!r}")
