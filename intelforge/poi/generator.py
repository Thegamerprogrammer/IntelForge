from __future__ import annotations

from ..core.models import POICandidate, ResearchSettings

class EvidenceBoundPOIGenerator:
    """Deterministic safe fallback; a configured model may replace this through its proxy."""
    def generate(self, candidate: POICandidate, settings: ResearchSettings) -> str:
        incident, legal = candidate.incident, candidate.legal
        date_text = f" on {incident.event_date.isoformat()}" if incident.event_date else ""
        location = f" in {incident.location}" if incident.location else ""
        tone = "reconcile" if settings.diplomacy >= 60 else "justify"
        return (f"In relation to {incident.title}{date_text}{location}, the documented conduct of {incident.conduct} "
                f"engages {legal.name}, {legal.provision}. Given the official evidence cited, how does the {candidate.target} delegation {tone} "
                f"this {candidate.tactical_relationship} with its obligation to {legal.obligation}?")
