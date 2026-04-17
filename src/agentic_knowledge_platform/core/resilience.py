from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 2, recovery_timeout: float = 15.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "closed"
        self.open_until = 0.0

    def allow_request(self) -> bool:
        if self.state != "open":
            return True
        if time.monotonic() >= self.open_until:
            self.state = "half-open"
            return True
        return False

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "closed"
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.open_until = time.monotonic() + self.recovery_timeout

    def snapshot(self) -> dict[str, float | int | str]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "open_until": self.open_until,
        }


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self.events[key]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 2
    base_delay_seconds: float = 0.01

    def call(
        self,
        operation: Callable[[], str],
        exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> str:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except exceptions:
                if attempt >= self.max_attempts:
                    raise
                time.sleep(self.base_delay_seconds * (2 ** (attempt - 1)))
        raise RuntimeError("retry policy exhausted unexpectedly")
