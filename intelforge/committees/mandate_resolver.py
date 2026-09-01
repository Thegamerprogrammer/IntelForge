from __future__ import annotations

from ..core.errors import ValidationError
from ..core.models import MandateFit
from .registry import CommitteeRecord, CommitteeRegistry


class MandateResolver:
    def __init__(self, registry: CommitteeRegistry) -> None:
        self.registry = registry

    def resolve(self, committee: str) -> dict:
        record = self.registry.get(committee)
        if not record:
            raise ValidationError(f"Unknown committee '{committee}'. Register it first or use a known alias.")
        return {"committeeId": record.id, "confidence": 1.0, "mandate": record.as_dict(), "scope": {"jurisdiction": list(record.jurisdiction), "topicsWithin": list(record.topics_within), "topicsOutside": list(record.topics_outside), "powers": list(record.powers), "limitations": list(record.limitations)}, "legalFrameworks": list(record.legal_frameworks), "sourceCapabilities": list(record.research_capabilities), "warnings": []}

    def classify(self, record: CommitteeRecord, text: str) -> MandateFit:
        terms = set((text or "").casefold().replace("-", " ").split())
        covered = {word for topic in record.topics_within for word in topic.casefold().split()}
        if not covered:
            return MandateFit.INDIRECTLY_RELEVANT
        return MandateFit.WITHIN_MANDATE if terms & covered else MandateFit.INDIRECTLY_RELEVANT
