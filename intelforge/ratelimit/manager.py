from __future__ import annotations

import random
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, TypeVar

from ..core.errors import ProviderError

T = TypeVar("T")

@dataclass
class ProviderHealth:
    failures: int = 0
    cooldown_until: datetime | None = None


class RateLimitManager:
    """Bounded retries with cooldowns; provider failures are explicit and finite."""
    def __init__(self, max_retries: int = 2, base_delay: float = 0.05) -> None:
        self.max_retries, self.base_delay = max_retries, base_delay
        self.health: dict[str, ProviderHealth] = defaultdict(ProviderHealth)
        self.events: list[dict] = []

    def execute(self, provider: str, operation: Callable[[], T]) -> T:
        health = self.health[provider]
        if health.cooldown_until and health.cooldown_until > datetime.now(timezone.utc):
            raise ProviderError(f"{provider} is cooling down")
        for attempt in range(self.max_retries + 1):
            try:
                result = operation()
                health.failures = 0
                return result
            except Exception as exc:
                rate_limited = getattr(exc, "status", None) == 429 or "429" in str(exc)
                self.events.append({"provider": provider, "attempt": attempt, "error": str(exc), "rate_limited": rate_limited})
                if attempt == self.max_retries:
                    health.failures += 1
                    health.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=min(60, 2 ** health.failures))
                    raise ProviderError(f"{provider} failed after bounded retries") from exc
                time.sleep(self.base_delay * (2 ** attempt) + random.uniform(0, self.base_delay))
        raise AssertionError("unreachable")
