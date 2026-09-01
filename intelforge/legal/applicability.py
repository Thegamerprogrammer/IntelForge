from __future__ import annotations

from datetime import date

from ..core.models import LegalFramework

class LegalApplicabilityValidator:
    def validate(self, framework: LegalFramework, ratification_date: date | None, event_date: date | None, freeze_date: date | None) -> LegalFramework:
        applicable = framework.applicable and (ratification_date is None or event_date is None or ratification_date <= event_date) and (freeze_date is None or event_date is None or event_date <= freeze_date)
        return LegalFramework(**{**framework.__dict__, "applicable": applicable, "reasoning": framework.reasoning + ("; temporal and membership checks passed" if applicable else "; failed temporal or membership check")})
