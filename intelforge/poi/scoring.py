from __future__ import annotations

from ..core.models import POICandidate, POIScores

def score(candidate: POICandidate, novel: bool) -> POIScores:
    source_count = len(candidate.incident.sources)
    official_count = sum(s.official for s in candidate.incident.sources)
    evidence = min(100, int(candidate.incident.confidence * 70 + source_count * 10 + official_count * 10))
    legal = int(candidate.legal.confidence * 80 + (20 if candidate.legal.applicable else 0))
    specifics = sum(bool(v) for v in (candidate.incident.event_date, candidate.incident.location, candidate.incident.actors, candidate.incident.conduct)) * 25
    genericity = max(0, 70 - specifics + (20 if not candidate.incident.event_date else 0))
    pressure = min(100, int((evidence + legal + specifics) / 3))
    return POIScores(evidence, legal, specifics, 95 if novel else 0, max(0, pressure - genericity // 3), genericity, 100 if candidate.mandate_fit.value == "WITHIN_MANDATE" else 65, max(0, pressure - 10), max(0, 100 - genericity), pressure)
