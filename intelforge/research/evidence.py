from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from ..core.models import Incident

@dataclass
class EvidenceClaim:
    claim_id: str
    incident_id: str
    claim: str
    source_ids: list[str]
    confidence: float
    freeze_valid: bool
    official_support: bool
    def as_dict(self) -> dict: return asdict(self)

class EvidenceVerifier:
    def verify(self, incidents: list[Incident], freeze_date: date | None) -> list[EvidenceClaim]:
        claims = []
        for incident in incidents:
            usable = [s for s in incident.sources if s.usable and (not freeze_date or not s.publication_date or s.publication_date <= freeze_date)]
            official = any(s.official for s in usable)
            # A low-confidence snippet never becomes a claim; at least official support or corroboration is required.
            if not usable or not (official or len(usable) > 1):
                continue
            confidence = min(.98, .55 + .2 * len(usable) + (.2 if official else 0))
            claims.append(EvidenceClaim(f"CLM-{len(claims)+1:06d}", incident.id, incident.conduct, [s.id for s in usable], confidence, True, official))
        return claims
