from __future__ import annotations

from dataclasses import asdict, dataclass

from ..core.models import MasterContextPacket, ResearchSettings
from ..sources import SourceCapabilityRegistry

@dataclass(frozen=True)
class ResearchQuery:
    query: str
    target: str
    purpose: str
    source_types: tuple[str, ...]
    priority: float

class DynamicResearchPlanner:
    def __init__(self, sources: SourceCapabilityRegistry | None = None) -> None:
        self.sources = sources or SourceCapabilityRegistry()

    def plan(self, context: MasterContextPacket, settings: ResearchSettings) -> list[ResearchQuery]:
        targets = [target for target in context.target_hypotheses if target.casefold() != settings.portfolio.casefold()]
        queries = []
        for target in targets:
            pressure = (settings.aggression + settings.controversy) / 200
            queries.extend((
                ResearchQuery(f"{target} {settings.agenda} official investigation incident", target, "incident_discovery", ("official", "primary_document"), round(.65 + .3 * pressure, 2)),
                ResearchQuery(f"{target} {settings.agenda} treaty ratification official", target, "legal_applicability", ("official_database",), .9),
            ))
        return queries

    def plan_from_dict(self, context: dict, settings: ResearchSettings) -> list[ResearchQuery]:
        """Deserialize persisted context without giving the planner database knowledge."""
        from ..core.models import MasterContextPacket
        return self.plan(MasterContextPacket(**context), settings)

    @staticmethod
    def as_json(queries: list[ResearchQuery]) -> dict:
        return {"queries": [{"query": q.query, "target": q.target, "purpose": q.purpose, "sourceTypes": list(q.source_types), "priority": q.priority} for q in queries]}
