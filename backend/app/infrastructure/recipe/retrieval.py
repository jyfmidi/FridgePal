"""Retrieval adapter protocol and live search adapter (contract 8.1/8.2).

The adapter protocol is provider-neutral; the live implementation talks to a
Tavily-compatible search endpoint. The search query is built deterministically
from selected ingredient names, quantities, and serving count — urgency never
enters the query. Results are reduced to allow-listed source metadata: no raw
page bodies, no secrets in diagnostics.
"""

from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urlparse

import httpx

from app.infrastructure.recipe.errors import (
    NoGroundedSourcesError,
    RetrievalTimeoutError,
    SourceUnavailableError,
)
from app.infrastructure.recipe.schemas import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedSource,
    format_quantity,
)


class RetrievalAdapter(Protocol):
    """Provider-neutral retrieval contract."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Return allow-listed source metadata for the selected foods."""
        ...


def build_search_query(request: RetrievalRequest) -> str:
    """Deterministic query from ingredient names, quantities, and servings."""
    parts = [f"{ing.name} {format_quantity(ing.quantity)}{ing.unit}" for ing in request.ingredients]
    return f"recipe using {', '.join(parts)} for {request.servings} servings"


class TavilyRetrievalAdapter:
    """Live retrieval against a Tavily-compatible search API."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not api_key:
            raise ValueError("search API key is required for live retrieval")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout_seconds

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        query = build_search_query(request)
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": request.max_candidates,
            "include_answer": False,
            "exclude_domains": [
                "youtube.com",
                "m.youtube.com",
                "facebook.com",
                "www.facebook.com",
                "tiktok.com",
                "www.tiktok.com",
                "instagram.com",
                "www.instagram.com",
                "pinterest.com",
                "www.pinterest.com",
                "vimeo.com",
            ],
        }
        timeout = min(request.timeout_seconds, self._timeout)
        client = self._client
        owns_client = client is None
        http_client = client or httpx.Client(timeout=timeout)
        try:
            response = http_client.post(f"{self._base_url}/search", json=payload)
        except httpx.TimeoutException as exc:
            raise RetrievalTimeoutError("search provider timed out") from exc
        except httpx.HTTPError as exc:
            raise SourceUnavailableError(f"search provider unreachable: {exc}") from exc
        finally:
            if owns_client:
                http_client.close()

        if response.status_code >= 400:
            raise SourceUnavailableError(f"search provider returned HTTP {response.status_code}")
        try:
            results = response.json().get("results", [])
        except ValueError as exc:
            raise SourceUnavailableError("search provider returned malformed JSON") from exc

        retrieved_at = datetime.now(UTC)
        sources: list[RetrievedSource] = []
        for result in results:
            url = result.get("url", "")
            title = (result.get("title") or "").strip()
            content = (result.get("content") or "").strip()
            publisher = urlparse(url).netloc
            if not url or not title or not publisher:
                continue
            try:
                sources.append(
                    RetrievedSource(
                        url=url,
                        title=title,
                        publisher=publisher,
                        retrieved_at=retrieved_at,
                        used_food_ids=[],
                        content=content[:4000],
                    )
                )
            except ValueError:
                continue  # unsafe URL — excluded before selection (ERR-04 behavior)
        if not sources:
            raise NoGroundedSourcesError()
        return RetrievalResponse(
            sources=sources,
            diagnostics={"mode": "live", "result_count": str(len(sources))},
        )
