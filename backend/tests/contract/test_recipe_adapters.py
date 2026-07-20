"""Adapter contract tests (contract section 13, ERR-01..ERR-05).

Covers fixture determinism, schema version rejection, allow-list citation
enforcement, malformed output rejection, the one-repair-attempt limit, timeout
classification, and provider replacement. Live adapters run against mocked
HTTP transports only — never the real network.
"""

import json
from decimal import Decimal

import httpx
import pytest
from app.config import Settings
from app.infrastructure.recipe.errors import (
    AdapterErrorCode,
    InvalidStructuredOutputError,
    NoGroundedSourcesError,
    RetrievalTimeoutError,
    SourceUnavailableError,
)
from app.infrastructure.recipe.factory import build_recipe_adapters
from app.infrastructure.recipe.fixture import (
    FixtureRetrievalAdapter,
    FixtureStructuringAdapter,
)
from app.infrastructure.recipe.retrieval import TavilyRetrievalAdapter, build_search_query
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedRecipe,
    RetrievalIngredientInput,
    RetrievalRequest,
    StructuringRequest,
    parse_normalized_recipe,
)
from app.infrastructure.recipe.structuring import OpenAICompatibleStructuringAdapter


def ingredient(food_id: str = "food-kale", name: str = "Kale") -> RetrievalIngredientInput:
    return RetrievalIngredientInput(
        food_definition_id=food_id, name=name, quantity=Decimal("200"), unit="g"
    )


def retrieval_request() -> RetrievalRequest:
    return RetrievalRequest(
        ingredients=[ingredient(), ingredient("food-tofu", "Tofu")], servings=2
    )


def structuring_request() -> StructuringRequest:
    sources = FixtureRetrievalAdapter().retrieve(retrieval_request()).sources
    return StructuringRequest(
        sources=sources,
        ingredients=[ingredient(), ingredient("food-tofu", "Tofu")],
        servings=2,
    )


def valid_payload(source_url: str) -> dict:
    return {
        "schema_version": RECIPE_SCHEMA_VERSION,
        "title": "Kale stir fry",
        "description": None,
        "base_yield": 2,
        "ingredients": [
            {
                "original_text": "200g kale",
                "amount_kind": "NUMERIC",
                "amount": "200",
                "unit": "g",
                "mapping_suggestion": "food-kale",
                "provenance": "SOURCE",
                "needs_review": False,
            }
        ],
        "steps": ["Wash the kale.", "Stir fry for 3 minutes."],
        "source_urls": [source_url],
        "analysis_status": "READY",
        "warnings": [],
    }


def llm_client(contents: list[str]) -> httpx.Client:
    """Mock chat-completions endpoint returning the given contents in order."""
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
    def test_retrieval_is_deterministic(self) -> None:
        adapter = FixtureRetrievalAdapter()
        assert adapter.retrieve(retrieval_request()) == adapter.retrieve(retrieval_request())

    def test_structuring_is_deterministic(self) -> None:
        adapter = FixtureStructuringAdapter()
        request = structuring_request()
        assert adapter.structure(request) == adapter.structure(request)

    def test_fixture_recipe_passes_validation(self) -> None:
        request = structuring_request()
        recipe = FixtureStructuringAdapter().structure(request)
        reparsed = parse_normalized_recipe(
            json.loads(recipe.model_dump_json()), {s.url for s in request.sources}
        )
        assert reparsed == recipe

    def test_diagnostics_carry_no_secrets_or_bodies(self) -> None:
        response = FixtureRetrievalAdapter().retrieve(retrieval_request())
        assert set(response.diagnostics) <= {"mode", "result_count"}


class TestSearchQuery:
    def test_query_uses_names_quantities_and_servings(self) -> None:
        query = build_search_query(retrieval_request())
        assert "Kale 200g" in query
        assert "Tofu 200g" in query
        assert "2 servings" in query

    def test_query_excludes_urgency(self) -> None:
        query = build_search_query(retrieval_request())
        assert "urgent" not in query.lower()
        assert "expir" not in query.lower()


class TestSchemaValidation:
    def test_unknown_schema_version_rejected(self) -> None:
        payload = valid_payload("https://pantry-journal.example/r")
        payload["schema_version"] = "9.9"
        with pytest.raises(InvalidStructuredOutputError) as excinfo:
            parse_normalized_recipe(payload, {"https://pantry-journal.example/r"})
        assert excinfo.value.code is AdapterErrorCode.INVALID_STRUCTURED_OUTPUT

    def test_missing_required_structure_rejected(self) -> None:
        payload = valid_payload("https://pantry-journal.example/r")
        del payload["steps"]
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, {"https://pantry-journal.example/r"})

    def test_non_allowlisted_citation_rejected(self) -> None:
        payload = valid_payload("https://evil.example/x")
        with pytest.raises(InvalidStructuredOutputError, match="allow-list"):
            parse_normalized_recipe(payload, {"https://pantry-journal.example/r"})

    def test_unsafe_citation_scheme_rejected(self) -> None:
        payload = valid_payload("ftp://pantry-journal.example/r")
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, {"ftp://pantry-journal.example/r"})

    def test_negative_quantity_rejected(self) -> None:
        payload = valid_payload("https://pantry-journal.example/r")
        payload["ingredients"][0]["amount"] = "-5"
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, {"https://pantry-journal.example/r"})

    def test_numeric_ingredient_requires_amount(self) -> None:
        payload = valid_payload("https://pantry-journal.example/r")
        payload["ingredients"][0]["amount"] = None
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(payload, {"https://pantry-journal.example/r"})

    def test_non_object_payload_rejected(self) -> None:
        with pytest.raises(InvalidStructuredOutputError):
            parse_normalized_recipe(["not", "an", "object"], set())


class TestRepairAttemptLimit:
    def request(self) -> StructuringRequest:
        return structuring_request()

    def test_invalid_then_valid_repaired_once(self) -> None:
        allowed = self.request().sources[0].url
        client = llm_client(["not json at all", json.dumps(valid_payload(allowed))])
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
        assert len(client.calls) == 2  # type: ignore[attr-defined] — never a third try

    def test_non_allowlisted_citation_triggers_repair_then_failure(self) -> None:
        bad = json.dumps(valid_payload("https://evil.example/x"))
        client = llm_client([bad, bad])
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        with pytest.raises(InvalidStructuredOutputError):
            adapter.structure(self.request())
        assert len(client.calls) == 2  # type: ignore[attr-defined]


class TestLiveAdapterErrors:
    def test_retrieval_timeout_classified_err01(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        adapter = TavilyRetrievalAdapter(
            api_key="k", base_url="https://search.example", client=client
        )
        with pytest.raises(RetrievalTimeoutError) as excinfo:
            adapter.retrieve(retrieval_request())
        assert excinfo.value.code is AdapterErrorCode.RETRIEVAL_TIMEOUT
        assert excinfo.value.retriable

    def test_structuring_timeout_classified_err01(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        adapter = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        with pytest.raises(RetrievalTimeoutError):
            adapter.structure(structuring_request())

    def test_retrieval_http_error_classified_err04(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(503))
        )
        adapter = TavilyRetrievalAdapter(
            api_key="k", base_url="https://search.example", client=client
        )
        with pytest.raises(SourceUnavailableError) as excinfo:
            adapter.retrieve(retrieval_request())
        assert excinfo.value.code is AdapterErrorCode.SOURCE_UNAVAILABLE

    def test_empty_results_classified_err03(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"results": []})
            )
        )
        adapter = TavilyRetrievalAdapter(
            api_key="k", base_url="https://search.example", client=client
        )
        with pytest.raises(NoGroundedSourcesError) as excinfo:
            adapter.retrieve(retrieval_request())
        assert excinfo.value.code is AdapterErrorCode.NO_GROUNDED_SOURCES

    def test_live_retrieval_maps_results(self) -> None:
        payload = {
            "results": [
                {"url": "https://cooks.example/kale", "title": "Kale dinner"},
                {"url": "ftp://bad.example/x", "title": "Unsafe"},
            ]
        }
        client = httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
        )
        adapter = TavilyRetrievalAdapter(
            api_key="k", base_url="https://search.example", client=client
        )
        response = adapter.retrieve(retrieval_request())
        assert [s.url for s in response.sources] == ["https://cooks.example/kale"]
        assert response.sources[0].publisher == "cooks.example"

    def test_api_key_stays_in_payload_not_diagnostics(self) -> None:
        captured: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={"results": []})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        adapter = TavilyRetrievalAdapter(
            api_key="secret-key", base_url="https://search.example", client=client
        )
        with pytest.raises(NoGroundedSourcesError):
            adapter.retrieve(retrieval_request())
        assert captured[0]["api_key"] == "secret-key"


class TestProviderReplacement:
    def test_fixture_mode_returns_fixture_adapters(self) -> None:
        adapters = build_recipe_adapters(Settings(recipe_provider_mode="fixture"))
        assert isinstance(adapters.retrieval, FixtureRetrievalAdapter)
        assert isinstance(adapters.structuring, FixtureStructuringAdapter)

    def test_live_mode_returns_live_adapters(self) -> None:
        adapters = build_recipe_adapters(
            Settings(
                recipe_provider_mode="live",
                llm_api_key="k",
                search_api_key="k",
            )
        )
        assert isinstance(adapters.retrieval, TavilyRetrievalAdapter)
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
        allowed = request.sources[0].url
        client = llm_client([json.dumps(valid_payload(allowed))])
        live = OpenAICompatibleStructuringAdapter(
            api_key="k", base_url="https://llm.example/v1", model="m", client=client
        )
        live_recipe = live.structure(request)
        assert type(fixture_recipe) is type(live_recipe) is NormalizedRecipe
