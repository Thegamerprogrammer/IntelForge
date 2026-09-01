from __future__ import annotations

from dataclasses import asdict
from datetime import date
from time import perf_counter
from urllib.parse import urlparse

from ..committees import CommitteeRegistry, MandateResolver
from ..context import ContextBuilder
from ..models.ollama import OllamaProxy
from ..persistence import Database
from ..research.acquisition import Crawl4AIProxy
from ..research.evidence import EvidenceVerifier
from ..research.incidents import IncidentExtractor
from ..research.planner import DynamicResearchPlanner
from ..search import SearXNGProxy
from ..sources import SourceCapabilityRegistry
from .errors import ProviderError
from .models import LegalFramework, MandateFit, POICandidate, ResearchSettings
from .stages import STAGE_DEFINITIONS, StageState, StageStatus


class ResearchPipeline:
    """Live persisted stage engine. Each stage only consumes earlier artifacts."""
    def __init__(self, database: Database | None = None, registry: CommitteeRegistry | None = None, search: SearXNGProxy | None = None, crawler: Crawl4AIProxy | None = None) -> None:
        self.database = database or Database()
        self.registry = registry or CommitteeRegistry()
        self.resolver = MandateResolver(self.registry)
        self.context_builder = ContextBuilder(local_analyzer=OllamaProxy())
        self.planner = DynamicResearchPlanner(SourceCapabilityRegistry())
        self.search, self.crawler = search or SearXNGProxy(), crawler or Crawl4AIProxy()
        self.extractor, self.verifier = IncidentExtractor(), EvidenceVerifier()

    def _stage(self, job_id: int, stage_id: str, fn):
        state = StageStatus(stage_id); state.start(); self.database.save_stage(job_id, stage_id, state.as_dict())
        try:
            result = fn()
            artifact_id = self.database.save(job_id, stage_id, result)
            state.artifact_ids.append(artifact_id); state.finish(StageState.COMPLETED)
            self.database.save_stage(job_id, stage_id, state.as_dict())
            return result
        except ProviderError as exc:
            state.finish(StageState.BLOCKED, str(exc)); self.database.save_stage(job_id, stage_id, state.as_dict()); raise
        except Exception as exc:
            state.finish(StageState.FAILED, str(exc)); self.database.save_stage(job_id, stage_id, state.as_dict()); raise

    def _blocked(self, job_id: int, from_stage: str, reason: str) -> None:
        ids = [identifier for identifier, _, _ in STAGE_DEFINITIONS]
        for stage_id in ids[ids.index(from_stage) + 1:]:
            state = StageStatus(stage_id); state.finish(StageState.BLOCKED, reason); self.database.save_stage(job_id, stage_id, state.as_dict())

    def run(self, settings: ResearchSettings, job_id: int | None = None) -> dict:
        job_id = job_id or self.database.create_job(asdict(settings))
        try:
            # Context ingestion is deliberately independent of mandate interpretation.
            context = self._stage(job_id, "context", lambda: self.context_builder.build(settings, {"committeeId": settings.committee, "legalFrameworks": []}).as_dict())
            mandate = self._stage(job_id, "mandate", lambda: self.resolver.resolve(settings.committee))
            portfolio = self._stage(job_id, "portfolio", lambda: {"portfolio": settings.portfolio, "research_notes": settings.research_notes, "exclusions": [settings.portfolio]})
            plan = self._stage(job_id, "planning", lambda: self.planner.as_json(self.planner.plan_from_dict(context, settings)))
            targets = self._stage(job_id, "targets", lambda: [target for target in context["target_hypotheses"] if target.casefold() != settings.portfolio.casefold()])
            queries = self._stage(job_id, "queries", lambda: plan)
            def discover():
                hits = []
                for query in plan["queries"]:
                    started = perf_counter()
                    try:
                        rows = self.search.search(query["query"], limit=10)
                        self.database.record_provider_call(job_id, "searxng", "discovery", latency_ms=int((perf_counter()-started)*1000))
                        hits.extend(asdict(row) for row in rows)
                    except Exception as exc:
                        self.database.record_provider_call(job_id, "searxng", "discovery", latency_ms=int((perf_counter()-started)*1000), success=False, error=str(exc))
                        raise ProviderError(f"SearXNG unavailable: {exc}") from exc
                return hits
            hits = self._stage(job_id, "discovery", discover)
            def acquire():
                documents = []
                for row in hits:
                    from .models import Source
                    source = Source(**row)
                    document = self.crawler.retrieve(source)
                    if settings.freeze_date and document.publication_date and document.publication_date > settings.freeze_date: continue
                    documents.append(document.as_dict())
                return documents
            documents = self._stage(job_id, "documents", acquire)
            incidents = self._stage(job_id, "incidents", lambda: [asdict(i) for target in targets for i in self.extractor.extract([self._document(d) for d in documents], target, settings.freeze_date)])
            claims = self._stage(job_id, "evidence", lambda: self._claims(incidents, settings.freeze_date))
            # Legal discovery intentionally only accepts a retrieved authoritative legal instrument, never model guesses.
            legal = self._stage(job_id, "legal", lambda: self._legal_from_documents(documents, settings.freeze_date))
            if not incidents or not claims or not legal:
                reason = "No verified incident, evidence claim, and authoritative legal instrument were jointly available."
                self._blocked(job_id, "legal", reason)
                self.database.update_job(job_id, "legal", "blocked")
                return self.summary(job_id)
            # Further candidate steps are deliberately gated pending a matching legal applicability record.
            self._blocked(job_id, "applicability", "Legal element matching requires an implemented treaty-status adapter.")
            self.database.update_job(job_id, "applicability", "blocked")
            return self.summary(job_id)
        except Exception:
            self.database.update_job(job_id, "failed", "failed")
            raise

    @staticmethod
    def _document(data):
        from ..research.acquisition import RetrievedDocument
        return RetrievedDocument(**data)
    def _claims(self, incidents: list[dict], freeze_date: date | None) -> list[dict]:
        from .models import Incident, Source
        values = [Incident(**{**item, "sources": [Source(**source) for source in item["sources"]]}) for item in incidents]
        return [claim.as_dict() for claim in self.verifier.verify(values, freeze_date)]
    @staticmethod
    def _legal_from_documents(documents: list[dict], freeze_date: date | None) -> list[dict]:
        import re
        frameworks = []
        for document in documents:
            authoritative = any(host in document["url"].casefold() for host in ("treaties.un.org", "legal.un.org", "icj-cij.org", "icc-cpi.int"))
            article = re.search(r"\bArticle\s+(\d+[A-Za-z]?)\b", document["content"], re.I)
            if authoritative and article:
                title = document["title"] or document["url"]
                frameworks.append(asdict(LegalFramework(f"LAW-{len(frameworks)+1:06d}", title, f"Article {article.group(1)}", "Obligation requires legal element analysis from the cited instrument.", document["url"], False, "Instrument and provision were retrieved; party, temporal, material, and territorial applicability remain unverified.", .5)))
        return frameworks
    def summary(self, job_id: int) -> dict:
        stages = self.database.stages(job_id)
        artifacts = {kind: self.database.artifacts(job_id, kind) for kind in ("incidents", "legal", "evidence", "finalized")}
        return {"job_id": job_id, "stages": stages, "incidents": len(artifacts["incidents"][-1]["payload"]) if artifacts["incidents"] else 0, "legal_frameworks": len(artifacts["legal"][-1]["payload"]) if artifacts["legal"] else 0, "evidence_claims": len(artifacts["evidence"][-1]["payload"]) if artifacts["evidence"] else 0, "final_pois": artifacts["finalized"][-1]["payload"] if artifacts["finalized"] else []}
