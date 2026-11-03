"""Limite de tentativas de login falhas por conta (memória do processo; vale para 1 worker)."""

from __future__ import annotations

import time
from collections import defaultdict, deque

MAX_FAILURES = 5
WINDOW_SECONDS = 300.0


class FailureThrottle:
    def __init__(self, limit: int = MAX_FAILURES, window: float = WINDOW_SECONDS) -> None:
        self._limit = limit
        self._window = window
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _recent(self, key: str) -> deque[float]:
        failures = self._failures[key]
        now = time.monotonic()
        while failures and now - failures[0] > self._window:
            failures.popleft()
        return failures

    def is_blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self._limit

    def record_failure(self, key: str) -> None:
        self._recent(key).append(time.monotonic())

    def clear(self, key: str) -> None:
        self._failures.pop(key, None)

    def reset(self) -> None:
        self._failures.clear()


login_throttle = FailureThrottle()
