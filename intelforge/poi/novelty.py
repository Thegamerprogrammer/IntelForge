from __future__ import annotations

from ..core.models import POICandidate

class NoveltyEngine:
    def __init__(self) -> None:
        self._fingerprints: list[dict] = []

    def is_novel(self, candidate: POICandidate) -> bool:
        current = candidate.fingerprint()
        for old in self._fingerprints:
            if set(current["incidentIds"]) & set(old["incidentIds"]):
                return False
            overlap = sum(bool(set(current[key]) & set(old[key])) for key in ("sourceIds", "legalIds", "actorIds"))
            if current["targetId"] == old["targetId"] and current["tacticalPattern"] == old["tacticalPattern"] and overlap >= 1:
                return False
        self._fingerprints.append(current)
        return True
