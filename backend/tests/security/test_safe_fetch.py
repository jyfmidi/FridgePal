"""Safe-fetch boundary security tests (contract section 11, NFR-SEC).

The boundary must fail closed: non-http schemes, loopback, private, link-local,
CGNAT, and metadata-service destinations are rejected, including after
redirects and DNS resolution. Size, content-type, redirect, and timeout limits
are enforced. All HTTP is mocked; DNS is injected through a fake resolver.
"""

import httpx
import pytest
from app.infrastructure.recipe.errors import SafeFetchError
from app.infrastructure.recipe.safe_fetch import (
    ensure_safe_url,
    is_prohibited_ip,
    safe_fetch,
)

PUBLIC_IP = "93.184.216.34"


def public_resolver(host: str) -> list[str]:
    return [PUBLIC_IP]


def resolver_for(mapping: dict[str, str]):
    return lambda host: [mapping.get(host, PUBLIC_IP)]


def client_with(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def ok_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text="recipe text", headers={"content-type": "text/plain"})


class TestSchemeAndDestinationRejection:
    @pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd", "gopher://x/"])
    def test_non_http_schemes_rejected(self, url: str) -> None:
        with pytest.raises(SafeFetchError, match="scheme"):
            ensure_safe_url(url, public_resolver)

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",  # loopback
            "10.0.0.5",  # RFC1918
            "172.16.0.9",  # RFC1918
            "192.168.1.1",  # RFC1918
            "169.254.169.254",  # link-local cloud metadata
            "100.64.0.1",  # CGNAT
            "0.0.0.0",  # unspecified
            "::1",  # IPv6 loopback
            "fd00:ec2::254",  # IPv6 metadata
        ],
    )
    def test_prohibited_ips_rejected(self, ip: str) -> None:
        assert is_prohibited_ip(ip)
        with pytest.raises(SafeFetchError):
            ensure_safe_url("http://internal/", resolver_for({"internal": ip}))

    def test_metadata_hostname_rejected(self) -> None:
        with pytest.raises(SafeFetchError, match="metadata"):
            ensure_safe_url("http://metadata.google.internal/", public_resolver)

    def test_any_prohibited_address_fails_closed(self) -> None:
        def mixed(host: str) -> list[str]:
            return [PUBLIC_IP, "192.168.0.1"]

        with pytest.raises(SafeFetchError):
            ensure_safe_url("http://dual.example/", mixed)

    def test_dns_failure_rejected(self) -> None:
        def broken(host: str) -> list[str]:
            raise OSError("nxdomain")

        with pytest.raises(SafeFetchError, match="DNS"):
            ensure_safe_url("http://gone.example/", broken)


class TestFetchLimits:
    def test_successful_fetch_returns_bounded_text(self) -> None:
        doc = safe_fetch(
            "http://recipes.example/kale",
            client=client_with(ok_handler),
            resolver=public_resolver,
        )
        assert doc.text == "recipe text"
        assert doc.diagnostics["redirects"] == "0"

    def test_redirect_to_private_target_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"location": "http://internal.example/secret"})

        with pytest.raises(SafeFetchError, match="prohibited"):
            safe_fetch(
                "http://recipes.example/",
                client=client_with(handler),
                resolver=resolver_for({"internal.example": "10.1.2.3"}),
            )

    def test_public_redirect_followed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/":
                return httpx.Response(301, headers={"location": "/final"})
            return ok_handler(request)

        doc = safe_fetch(
            "http://recipes.example/",
            client=client_with(handler),
            resolver=public_resolver,
        )
        assert doc.url.endswith("/final")
        assert doc.diagnostics["redirects"] == "1"

    def test_redirect_limit_enforced(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(302, headers={"location": "/loop"})

        with pytest.raises(SafeFetchError, match="redirects"):
            safe_fetch(
                "http://recipes.example/loop",
                client=client_with(handler),
                resolver=public_resolver,
                max_redirects=2,
            )

    def test_oversized_declared_body_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"x" * 100,
                headers={"content-type": "text/plain", "content-length": str(10_000)},
            )

        with pytest.raises(SafeFetchError, match="too large"):
            safe_fetch(
                "http://recipes.example/big",
                client=client_with(handler),
                resolver=public_resolver,
                max_bytes=1_000,
            )

    def test_oversized_streamed_body_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"x" * 5_000, headers={"content-type": "text/plain"})

        with pytest.raises(SafeFetchError, match="too large"):
            safe_fetch(
                "http://recipes.example/big",
                client=client_with(handler),
                resolver=public_resolver,
                max_bytes=1_000,
            )

    @pytest.mark.parametrize("content_type", ["application/octet-stream", "image/png", None])
    def test_disallowed_content_types_rejected(self, content_type: str | None) -> None:
        headers = {} if content_type is None else {"content-type": content_type}

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"data", headers=headers)

        with pytest.raises(SafeFetchError, match="content type"):
            safe_fetch(
                "http://recipes.example/blob",
                client=client_with(handler),
                resolver=public_resolver,
            )

    def test_json_content_type_allowed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b'{"ok": true}', headers={"content-type": "application/json"}
            )

        doc = safe_fetch(
            "http://recipes.example/data",
            client=client_with(handler),
            resolver=public_resolver,
        )
        assert doc.text == '{"ok": true}'

    def test_http_error_rejected(self) -> None:
        client = client_with(lambda request: httpx.Response(404, text="nope"))
        with pytest.raises(SafeFetchError, match="HTTP 404"):
            safe_fetch(
                "http://recipes.example/missing",
                client=client,
                resolver=public_resolver,
            )

    def test_timeout_fails_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        with pytest.raises(SafeFetchError, match="timed out"):
            safe_fetch(
                "http://recipes.example/slow",
                client=client_with(handler),
                resolver=public_resolver,
            )
