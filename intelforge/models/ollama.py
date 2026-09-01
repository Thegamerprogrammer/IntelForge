from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

from ..core.errors import ProviderError
from ..ratelimit import RateLimitManager


class OllamaProxy:
    def __init__(self, endpoint: str | None = None, rate_limits: RateLimitManager | None = None) -> None:
        self.endpoint = endpoint or os.getenv("INTELFORGE_OLLAMA_URL", "http://localhost:11434")
        self.rate_limits = rate_limits or RateLimitManager()

    def analyze_context(self, text: str, model: str | None = None) -> dict:
        if not model or not text:
            return {}
        prompt = "Extract JSON keys agenda_interpretation, foreign_policy, target_hypotheses, research_priorities, legal_priorities, incident_priorities. Use only supplied text.\n" + text[:12000]
        def call():
            request = Request(self.endpoint.rstrip("/") + "/api/generate", data=json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json", "options": {"num_ctx": 4096, "num_predict": 700}}).encode(), headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=30) as response:
                return json.loads(json.loads(response.read())["response"])
        try:
            return self.rate_limits.execute("ollama", call)
        except Exception as exc:
            raise ProviderError("Ollama context analysis failed") from exc
