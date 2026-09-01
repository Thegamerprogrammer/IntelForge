from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from ..committees import CommitteeRegistry, MandateResolver
from ..context import ContextBuilder
from ..models.ollama import OllamaProxy
from ..persistence import Database
from ..research import DynamicResearchPlanner
from ..search import SearXNGProxy
from ..sources import SourceCapabilityRegistry
from .models import ResearchSettings, Source

STAGES = ("Context Intelligence", "Mandate Resolution", "Research Planning", "Target Discovery", "Web Discovery", "Incident Extraction", "Evidence Verification", "Legal Frameworks", "Tactical Analysis", "POI Generation", "Novelty Validation", "Final Validation")

class ResearchPipeline:
    """Orchestrates persisted, gated stages; it never makes a POI from discovery alone."""
    def __init__(self, database: Database | None = None, registry: CommitteeRegistry | None = None, search: SearXNGProxy | None = None) -> None:
        self.database = database or Database()
        self.registry = registry or CommitteeRegistry()
        self.resolver = MandateResolver(self.registry)
        self.context_builder = ContextBuilder(local_analyzer=OllamaProxy())
        self.planner = DynamicResearchPlanner(SourceCapabilityRegistry())
        self.search = search or SearXNGProxy()

    def run(self, settings: ResearchSettings) -> dict:
        job_id = self.database.create_job(asdict(settings))
        mandate = self.resolver.resolve(settings.committee)
        context = self.context_builder.build(settings, mandate)
        self.database.save(job_id, "context_packet", context.as_dict())
        self.database.update_job(job_id, "research_planning")
        queries = self.planner.plan(context, settings)
        self.database.save(job_id, "queries", self.planner.as_json(queries))
        targets = [target for target in context.target_hypotheses if target.casefold() != settings.portfolio.casefold()]
        supplied = [Source(id=f"supplied-{i}", url=url, title=urlparse(url).netloc or url, source_type="USER_SUPPLIED", official=False, supplied=True, usable=False) for i, url in enumerate(settings.extra_links, 1)]
        discovered = []
        for query in queries:
            try:
                discovered.extend(self.search.search(query.query, limit=5))
            except Exception as exc:
                self.database.save(job_id, "provider_failure", {"query": query.query, "error": str(exc)})
        self.database.save(job_id, "sources", {"supplied": [asdict(s) for s in supplied], "discovered": [asdict(s) for s in discovered]})
        # Discovery records remain unverified. No incident or POI is invented from snippets.
        self.database.update_job(job_id, "complete", "completed")
        return {"job_id": job_id, "stages": list(STAGES), "committee_id": mandate["committeeId"], "targets": targets, "queries": len(queries), "sources": len(supplied) + len(discovered), "incidents": 0, "legal_frameworks": 0, "candidates": 0, "duplicates_rejected": 0, "evidence_failures": 0, "final_pois": []}
