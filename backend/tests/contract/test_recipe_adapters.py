"""Adapter contract tests (contract section 13, ERR-01..ERR-05).

Covers fixture determinism, schema version rejection, malformed output
rejection, the one-repair-attempt limit, timeout classification, and provider
replacement. Live adapters run against mocked HTTP transports only.
"""

import json
from decimal import Decimal

import httpx
import pytest
from app.config import Settings
from app.infrastructure.recipe.errors import (
    AdapterErrorCode,
    InvalidStructuredOutputError,
    RetrievalTimeoutError,
    SourceUnavailableError,
)
from app.infrastructure.recipe.factory import build_recipe_adapters
from app.infrastructure.recipe.fixture import FixtureStructuringAdapter
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedRecipe,
    RetrievalIngredientInput,
    StructuringRequest,
    parse_normalized_recipe,
)
from app.infrastructure.recipe.structuring import OpenAICompatibleStructuringAdapter


def ingredient(food_id: str = "food-kale", name: str = "Kale") -> RetrievalIngredientInput:
    return RetrievalIngredientInput(
        food_definition_id=food_id, name=name, quantity=Decimal("200"), unit="g"
    )


def structuring_request() -> StructuringRequest:
    return StructuringRequest(
        ingredients=[ingredient(), ingredient("food-tofu", "Tofu")],
        servings=2,
    )


def valid_payload() -> dict:
    return {
        "schema_version": RECIPE_SCHEMA_VERSION,
        "title": "Kale stir fry",
        "description": None,
        "base_yield": 2,
        "ingredients": [
            {
                "original_text": "Kale",
                "amount_kind": "NUMERIC",
                "amount": "200",
                "unit": "g",
                "mapping_suggestion": "food-kale",
                "provenance": "AI_INFERENCE",
                "needs_review": False,
            }
        ],
        "steps": ["Wash the kale.", "Stir fry for 3 minutes.", "Season and serve."],
        "source_urls": [],
        "analysis_status": "READY",
        "warnings": [],
    }


def llm_client(contents: list[str]) -> httpx.Client:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        content = contents[min(len(calls) - 1, len(contents) - 1)]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    client.calls = calls  # type: ignore[attr-defined]
    return client


class TestFixtureDeterminism:
    def test_structuring_is_deterministic(self) -> None:
        adapter = FixtureStructuringAdapter()
        request = structuring_request()
        assert adapter.structure(request) == adapter.structure(request)

    def test_fixture_recipe_passes_validation(self) -> None:
        request = structuring_request()
        recipe = FixtureStructuringAdapter().structure(request)
        reparsed = parse_normalized_recipe(
            json.loads(recipe.model_dump_json()), set()
        )
        assert reparsed == recipe

    def test_fixture_has_at_least_3_steps(self) -> None:
        recipe = FixtureStructuringAdapter().structure(structuring_request())
        assert len(recipe.steps) >= 3

    def test_fixture_respects_cuisine(self) -> None:
        request = StructuringRequest(
            ingredients=[ingredient()],
            servings=2,
            cuisine="Chinese",
        )
        recipe = FixtureStructuringAdapter().structure(request)
        assert "Chinese" in recipe.title


class TestSchemaValidation:
    def test_unknown_schema_version_rejected(self) -> None:
        payload = valid_payload()
        payload["schema_version"] = "9.9"
        with pytest.raises(InvalidStructuredOutputError) as excinfo:
            parse_normalized_recipe(payload, set())
        assert excinfo.value.code is AdapterErrorCode.INVALID_STRUCTURED_OUTPUT

    def test_missing_required_structure_rejected(self) -> None:
        payload = valid_payload()
        del payload["steps"]
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, set())

    def test_negative_quantity_rejected(self) -> None:
        payload = valid_payload()
        payload["ingredients"][0]["amount"] = "-5"
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, set())

    def test_numeric_ingredient_requires_amount(self) -> None:
        payload = valid_payload()
        payload["ingredients"][0]["amount"] = None
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, set())

    def test_non_object_payload_rejected(self) -> None:
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(["not", "an", "object"], set())


class TestRepairAttemptLimit:
    def request(self) -> StructuringRequest:
        return structuring_request()

    def test_invalid_then_valid_repaired_once(self) -> None:
        client = llm_client(["not json at all", json.dumps(valid_payload())])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        recipe = adapter.structure(self.request())
        assert isinstance(recipe, NormalizedRecipe)
        assert len(client.calls) == 2  # type: ignore[attr-defined]

    def test_second_invalid_output_fails_classified(self) -> None:
        client = llm_client(["not json", "still not json"])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        with pytest.raises(InvalidStructuredOutputError, match="repair attempt"):
            adapter.structure(self.request())
        assert len(client.calls) == 2  # type: ignore[attr-defined]


class TestLiveAdapterErrors:
    def test_structuring_timeout_classified_err01(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        with pytest.raises(RetrievalTimeoutError):
            adapter.structure(structuring_request())

    def test_structuring_http_error_classified_err04(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(503))
        )
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        with pytest.raises(SourceUnavailableError) as excinfo:
            adapter.structure(structuring_request())
        assert excinfo.value.code is AdapterErrorCode.SOURCE_UNAVAILABLE


class TestProviderReplacement:
    def test_fixture_mode_returns_fixture_adapters(self) -> None:
        adapters = build_recipe_adapters(Settings(recipe_provider_mode="fixture"))
        assert isinstance(adapters.structuring, FixtureStructuringAdapter)

    def test_live_mode_returns_live_adapters(self) -> None:
        adapters = build_recipe_adapters(
            Settings(recipe_provider_mode="live", llm_api_key="k")
        )
        assert isinstance(adapters.structuring, OpenAICompatibleStructuringAdapter)

    def test_live_mode_requires_credentials(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            build_recipe_adapters(Settings(recipe_provider_mode="live"))

    def test_unknown_mode_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown recipe provider mode"):
            build_recipe_adapters(Settings(recipe_provider_mode="mystery"))

    def test_fixture_and_live_share_one_contract(self) -> None:
        request = structuring_request()
        fixture_recipe = FixtureStructuringAdapter().structure(request)
        client = llm_client([json.dumps(valid_payload())])
        live = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        live_recipe = live.structure(request)
        assert type(fixture_recipe) is type(live_recipe) is NormalizedRecipe


class TestAmountCoercion:
    def test_range_amount_coerced(self) -> None:
        client = llm_client([json.dumps({**valid_payload(), "ingredients": [
            {**valid_payload()["ingredients"][0], "amount": "1-2"}
        ]})])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        recipe = adapter.structure(structuring_request())
        assert recipe.ingredients[0].amount == Decimal("1")

    def test_fraction_amount_coerced(self) -> None:
        client = llm_client([json.dumps({**valid_payload(), "ingredients": [
            {**valid_payload()["ingredients"][0], "amount": "1/2"}
        ]})])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        recipe = adapter.structure(structuring_request())
        assert recipe.ingredients[0].amount == Decimal("0.5")

    def test_string_base_yield_coerced(self) -> None:
        client = llm_client([json.dumps({**valid_payload(), "base_yield": "2 servings"})])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        recipe = adapter.structure(structuring_request())
        assert recipe.base_yield == 2
