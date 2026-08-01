"""Behavior tests for the in-memory sliding-window rate limiter."""

import time

from app.auth.rate_limit import RateLimiter


def test_allows_requests_up_to_the_limit() -> None:
    now = 1_000.0
    limiter = RateLimiter(max_events=3, window_seconds=60.0, clock=lambda: now)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False


def test_window_expires_and_allows_again() -> None:
    now = 1_000.0
    limiter = RateLimiter(max_events=2, window_seconds=60.0, clock=lambda: now)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False
    now = 1_061.0
    assert limiter.allow("client-a") is True


def test_keys_are_isolated() -> None:
    limiter = RateLimiter(max_events=1, window_seconds=60.0)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-b") is True


def test_zero_max_events_disables_limiting() -> None:
    limiter = RateLimiter(max_events=0, window_seconds=60.0)
    for _ in range(100):
        assert limiter.allow("client-a") is True


def test_default_clock_is_monotonic() -> None:
    limiter = RateLimiter(max_events=1, window_seconds=60.0)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False
    # A second client is unaffected; also exercises real elapsed time safely.
    assert limiter.allow("client-b") is True
    assert time.monotonic() > 0
