from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen

from ..core.models import Source
from ..ratelimit import RateLimitManager


class SearXNGProxy:
    """Normalized discovery proxy; it discovers sources but does not invent evidence."""
    def __init__(self, endpoint: str | None = None, rate_limits: RateLimitManager | None = None) -> None:
        self.endpoint = endpoint or os.getenv("SEARXNG_BASE_URL") or os.getenv("INTELFORGE_SEARXNG_URL")
        self.rate_limits = rate_limits or RateLimitManager()
        self._cache: dict[tuple, list[Source]] = {}

    def search(self, query: str, limit: int = 10, *, categories: str = "general", language: str | None = None, time_range: str | None = None, domains: list[str] | None = None, page: int = 1) -> list[Source]:
        if not self.endpoint:
            raise RuntimeError("SEARXNG_BASE_URL is not configured")
        key = (query, limit, categories, language, time_range, tuple(domains or ()), page)
        if key in self._cache:
            return self._cache[key]
        def call():
            params = {"q": query, "format": "json", "categories": categories, "pageno": page}
            if language: params["language"] = language
            if time_range: params["time_range"] = time_range
            if domains: params["domains"] = ",".join(domains)
            url = self.endpoint.rstrip("/") + "/search?" + urlencode(params)
            with urlopen(url, timeout=20) as response:
                return json.load(response).get("results", [])[:limit]
        rows = self.rate_limits.execute("searxng", call)
        results = [Source(id=f"search-{abs(hash((query, row['url'])))}", url=row["url"], title=row.get("title", row["url"]), source_type="SEARCH_HIT", official=any(host in row["url"].casefold() for host in (".un.org", ".int", ".gov")), content=row.get("content", "")) for row in rows]
        self._cache[key] = results
        return results
