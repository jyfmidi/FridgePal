"""In-memory sliding-window rate limiter for the auth endpoints.

Single-process state is sufficient for the private single-node deployment of
Fridge Pal. Requests are bucketed by client address; a window of
``window_seconds`` allows at most ``max_events`` attempts. ``max_events <= 0``
disables limiting (useful for tests and fixture-mode demos).
"""

import threading
import time
from collections import deque
from collections.abc import Callable

_MAX_KEYS = 10_000


class RateLimiter:
    """Thread-safe fixed-window limiter keyed by arbitrary strings."""

    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_events = max_events
        self._window = window_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        """Record one attempt for ``key`` and report whether it is permitted."""
        if self._max_events <= 0:
            return True
        now = self._clock()
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and now - events[0] > self._window:
                events.popleft()
            events.append(now)
            self._prune_if_large(now)
            return len(events) <= self._max_events

    def _prune_if_large(self, now: float) -> None:
        """Bound memory when many distinct keys accumulate; drop empty windows."""
        if len(self._events) <= _MAX_KEYS:
            return
        expired: list[str] = []
        for key, events in self._events.items():
            while events and now - events[0] > self._window:
                events.popleft()
            if not events:
                expired.append(key)
        for key in expired:
            del self._events[key]
