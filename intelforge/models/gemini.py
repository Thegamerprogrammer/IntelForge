from __future__ import annotations

import os
from dataclasses import dataclass

from ..core.errors import ProviderError
from ..ratelimit import RateLimitManager

@dataclass
class GeminiModel:
    name: str
    capabilities: tuple[str, ...] = ("generate",)
    healthy: bool = True

class GeminiModelRegistry:
    def __init__(self) -> None:
        self.models: list[GeminiModel] = []

    def discover(self) -> list[GeminiModel]:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            return []
        try:
            from google import genai
            client = genai.Client(api_key=key)
            self.models = [GeminiModel(m.name, tuple(getattr(m, "supported_generation_methods", []) or ("generate",))) for m in client.models.list()]
        except Exception:
            self.models = []
        return self.models

    def select(self, requested: str | None = None) -> GeminiModel | None:
        if requested:
            return next((m for m in self.models if m.name == requested and m.healthy), None)
        return next((m for m in self.models if m.healthy and "generate" in m.capabilities), None)

class GeminiProxy:
    def __init__(self, registry: GeminiModelRegistry | None = None, rate_limits: RateLimitManager | None = None) -> None:
        self.registry = registry or GeminiModelRegistry()
        self.rate_limits = rate_limits or RateLimitManager()

    def generate_poi(self, evidence_package: dict, requested_model: str | None = None) -> str:
        model = self.registry.select(requested_model)
        if not model:
            raise ProviderError("No healthy Gemini generation model is configured")
        # Kept behind this proxy so the engine never depends on a vendor SDK.
        raise ProviderError("Gemini generation integration requires a configured SDK runtime")
