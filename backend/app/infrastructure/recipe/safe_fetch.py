"""SSRF-safe fetch boundary (contract section 11).

Rejects non-http(s) schemes and loopback, RFC1918/private, link-local,
metadata-service, and otherwise prohibited destinations. The URL is
re-validated after every redirect and DNS resolution step; redirect count,
response size, content type, and timeout are all bounded. Retrieved text is
data — it is never rendered as HTML and never treated as instructions.

The resolver is injectable so tests (and deployments with controlled DNS) can
pin resolution results. Note the inherent TOCTOU gap: the HTTP client
re-resolves the host when connecting; deployments needing a hard guarantee
should route egress through a proxy enforcing the same rules.
"""

import ipaddress
import socket
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx

from app.infrastructure.recipe.errors import SafeFetchError

DEFAULT_MAX_REDIRECTS = 5
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 10.0
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_ALLOWED_CONTENT_TYPE_PREFIXES = ("text/",)
_ALLOWED_CONTENT_TYPES = ("application/json",)

# Cloud metadata endpoints beyond the link-local range covered by is_link_local.
_METADATA_HOSTS = {"metadata.google.internal"}
_METADATA_IPS = {"169.254.169.254", "fd00:ec2::254"}
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")

Resolver = Callable[[str], Sequence[str]]


def default_resolver(host: str) -> Sequence[str]:
    """Resolve a host to IP strings via the system resolver."""
    return [str(info[4][0]) for info in socket.getaddrinfo(host, None)]


def is_prohibited_ip(ip_str: str) -> bool:
    """True for loopback, private, link-local, metadata, and reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    if ip_str in _METADATA_IPS:
        return True
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or ip in _CGNAT_NETWORK
    )


def ensure_safe_url(url: str, resolver: Resolver = default_resolver) -> str:
    """Validate scheme and resolve the host, rejecting prohibited destinations.

    Every resolved address must be public; one prohibited address rejects the
    URL (fail closed).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SafeFetchError(f"URL scheme not allowed: {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise SafeFetchError("URL has no host")
    if host in _METADATA_HOSTS:
        raise SafeFetchError(f"metadata-service host not allowed: {host!r}")
    try:
        addresses = resolver(host)
    except OSError as exc:
        raise SafeFetchError(f"DNS resolution failed for {host!r}") from exc
    if not addresses:
        raise SafeFetchError(f"DNS returned no addresses for {host!r}")
    for address in addresses:
        if is_prohibited_ip(address):
            raise SafeFetchError(f"destination resolves to a prohibited address: {host!r}")
    return url


def _content_type_allowed(content_type: str | None) -> bool:
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in _ALLOWED_CONTENT_TYPES or media_type.startswith(
        _ALLOWED_CONTENT_TYPE_PREFIXES
    )


@dataclass(frozen=True)
class FetchedDocument:
    """A bounded, sanitized fetch result. ``text`` is data, never markup to render."""

    url: str
    status_code: int
    content_type: str
    text: str
    diagnostics: dict[str, str] = field(default_factory=dict)


def safe_fetch(
    url: str,
    *,
    client: httpx.Client | None = None,
    resolver: Resolver = default_resolver,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> FetchedDocument:
    """Fetch ``url`` inside the security boundary and return bounded text."""
    owns_client = client is None
    http_client = client or httpx.Client(follow_redirects=False, timeout=timeout_seconds)
    try:
        current = ensure_safe_url(url, resolver)
        redirects = 0
        while True:
            with http_client.stream("GET", current, follow_redirects=False) as response:
                if response.status_code in _REDIRECT_STATUSES:
                    location = response.headers.get("location")
                    if not location:
                        raise SafeFetchError("redirect without a Location header")
                    redirects += 1
                    if redirects > max_redirects:
                        raise SafeFetchError(f"too many redirects (limit {max_redirects})")
                    current = ensure_safe_url(urljoin(current, location), resolver)
                    continue
                if response.status_code >= 400:
                    raise SafeFetchError(f"source returned HTTP {response.status_code}")
                content_type = response.headers.get("content-type")
                if not _content_type_allowed(content_type):
                    raise SafeFetchError(f"content type not allowed: {content_type!r}")
                declared = response.headers.get("content-length")
                if declared and int(declared) > max_bytes:
                    raise SafeFetchError(f"response too large (limit {max_bytes} bytes)")
                chunks: list[bytes] = []
                received = 0
                for chunk in response.iter_bytes():
                    received += len(chunk)
                    if received > max_bytes:
                        raise SafeFetchError(f"response too large (limit {max_bytes} bytes)")
                    chunks.append(chunk)
            body = b"".join(chunks)
            encoding = response.encoding or "utf-8"
            return FetchedDocument(
                url=current,
                status_code=response.status_code,
                content_type=content_type or "",
                text=body.decode(encoding, errors="replace"),
                diagnostics={"redirects": str(redirects), "bytes": str(len(body))},
            )
    except httpx.TimeoutException as exc:
        raise SafeFetchError("fetch timed out") from exc
    finally:
        if owns_client:
            http_client.close()
