from __future__ import annotations

import re

from ..core.models import MasterContextPacket, ResearchSettings
from .document_parser import DocumentParser


class ContextBuilder:
    def __init__(self, parser: DocumentParser | None = None, local_analyzer=None) -> None:
        self.parser = parser or DocumentParser()
        self.local_analyzer = local_analyzer

    def build(self, settings: ResearchSettings, mandate: dict) -> MasterContextPacket:
        text = self.parser.extract(settings.background_guide) if settings.background_guide else ""
        normalized = re.sub(r"\s+", " ", text).strip()
        analysis = self.local_analyzer.analyze_context(normalized, settings.ollama_model) if normalized and self.local_analyzer else {}
        targets = list(settings.target_countries) or list(analysis.get("target_hypotheses", []))
        exclusions = [settings.portfolio]
        return MasterContextPacket(
            committee={"input": settings.committee, "id": mandate["committeeId"]}, agenda={"text": settings.agenda, "interpretation": analysis.get("agenda_interpretation", settings.agenda)}, portfolio={"name": settings.portfolio}, foreign_policy={"researchRequired": True, "interests": analysis.get("foreign_policy", [])}, freeze_date=settings.freeze_date.isoformat() if settings.freeze_date else None,
            background_guide={"path": settings.background_guide, "textLength": len(normalized), "analysis": analysis}, mandate=mandate,
            research_priorities=analysis.get("research_priorities", [settings.agenda, settings.research_notes]), target_hypotheses=targets,
            legal_priorities=analysis.get("legal_priorities", mandate["legalFrameworks"]), incident_priorities=analysis.get("incident_priorities", []), source_priorities=["official", "primary_document", "official_database"], exclusions=exclusions,
        )
