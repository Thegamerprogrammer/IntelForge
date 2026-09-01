from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class MandateFit(StrEnum):
    WITHIN_MANDATE = "WITHIN_MANDATE"
    INDIRECTLY_RELEVANT = "INDIRECTLY_RELEVANT"
    OUTSIDE_MANDATE = "OUTSIDE_MANDATE"


@dataclass(frozen=True)
class ResearchSettings:
    committee: str
    agenda: str
    portfolio: str
    freeze_date: date | None = None
    background_guide: str | None = None
    research_notes: str = ""
    extra_links: tuple[str, ...] = ()
    target_countries: tuple[str, ...] = ()
    poi_count: int = 10
    aggression: int = 50
    controversy: int = 50
    diplomacy: int = 50
    gemini_model: str | None = None
    ollama_model: str | None = None

    def __post_init__(self) -> None:
        if not self.committee.strip() or not self.agenda.strip() or not self.portfolio.strip():
            raise ValueError("committee, agenda, and portfolio are mandatory")
        if self.poi_count < 1:
            raise ValueError("poi_count must be at least 1")
        for name in ("aggression", "controversy", "diplomacy"):
            if not 0 <= getattr(self, name) <= 100:
                raise ValueError(f"{name} must be between 0 and 100")


@dataclass
class Source:
    id: str
    url: str
    title: str
    source_type: str
    official: bool
    publication_date: date | None = None
    event_date: date | None = None
    supplied: bool = False
    usable: bool = True
    content: str = ""


@dataclass
class Incident:
    id: str
    target: str
    title: str
    conduct: str
    event_date: date | None
    location: str | None
    actors: list[str]
    sources: list[Source]
    confidence: float


@dataclass
class LegalFramework:
    id: str
    name: str
    provision: str
    obligation: str
    official_source: str
    applicable: bool
    reasoning: str
    confidence: float


@dataclass
class POIScores:
    evidence_strength: int
    legal_strength: int
    specificity: int
    novelty: int
    think_score: int
    genericity: int
    mandate_fit: int
    answer_difficulty: int
    counter_attack_risk: int
    tactical_pressure: int


@dataclass
class POICandidate:
    target: str
    incident: Incident
    legal: LegalFramework
    cited_violation: str
    tactical_relationship: str
    question: str = ""
    scores: POIScores | None = None
    mandate_fit: MandateFit = MandateFit.OUTSIDE_MANDATE
    validation_errors: list[str] = field(default_factory=list)

    def fingerprint(self) -> dict[str, Any]:
        return {"incidentIds": [self.incident.id], "sourceIds": [s.id for s in self.incident.sources], "legalIds": [self.legal.id], "actorIds": self.incident.actors, "targetId": self.target.casefold(), "tacticalPattern": self.tactical_relationship.casefold()}


@dataclass
class MasterContextPacket:
    committee: dict[str, Any]
    agenda: dict[str, Any]
    portfolio: dict[str, Any]
    foreign_policy: dict[str, Any]
    freeze_date: str | None
    background_guide: dict[str, Any]
    mandate: dict[str, Any]
    research_priorities: list[str]
    target_hypotheses: list[str]
    legal_priorities: list[str]
    incident_priorities: list[str]
    source_priorities: list[str]
    exclusions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
