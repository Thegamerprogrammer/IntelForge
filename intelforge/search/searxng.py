from __future__ import annotations

import json
import os
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from ..core.models import Source
from ..ratelimit import RateLimitManager


class SearXNGProxy:
    """Normalized discovery proxy; it discovers sources but does not invent evidence."""
    def __init__(self, endpoint: str | None = None, rate_limits: RateLimitManager | None = None) -> None:
        self.endpoint = endpoint or os.getenv("INTELFORGE_SEARXNG_URL")
        self.rate_limits = rate_limits or RateLimitManager()

    def search(self, query: str, limit: int = 10) -> list[Source]:
        if not self.endpoint:
            return []
        def call():
            url = self.endpoint.rstrip("/") + "/search?" + urlencode({"q": query, "format": "json"})
            with urlopen(url, timeout=20) as response:
                return json.load(response).get("results", [])[:limit]
        rows = self.rate_limits.execute("searxng", call)
        return [Source(id=f"search-{index}", url=row["url"], title=row.get("title", row["url"]), source_type="GENERAL_WEB", official=False, content=row.get("content", "")) for index, row in enumerate(rows, 1)]
