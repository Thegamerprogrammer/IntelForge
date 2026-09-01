from __future__ import annotations

import re
from datetime import date

from ..core.models import MandateFit, POICandidate

class POIValidator:
    forbidden = ("does the delegation agree", "does the delegation support", "would the delegation")
    def validate(self, candidate: POICandidate, freeze_date: date | None) -> list[str]:
        errors: list[str] = []
        question = candidate.question.strip()
        if not question.endswith("?"):
            errors.append("POI must end with a substantive question")
        if question.casefold().startswith(self.forbidden) or re.match(r"^(is|are|do|does|did|can|will)\b", question.casefold()):
            errors.append("POI must not be yes/no")
        if candidate.target.casefold() in {"", "unknown"}:
            errors.append("POI target is missing")
        if candidate.mandate_fit == MandateFit.OUTSIDE_MANDATE:
            errors.append("incident is outside committee mandate")
        if not candidate.legal.applicable:
            errors.append("legal framework is not applicable")
        if not candidate.incident.sources:
            errors.append("incident has no evidence sources")
        if freeze_date:
            for source in candidate.incident.sources:
                if source.publication_date and source.publication_date > freeze_date:
                    errors.append(f"source {source.id} is post-freeze")
        return errors
