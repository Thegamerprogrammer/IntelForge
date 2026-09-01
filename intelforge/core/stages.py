from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

class StageState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"

@dataclass
class StageStatus:
    stage_id: str
    status: StageState = StageState.PENDING
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    artifact_ids: list[int] = field(default_factory=list)

    def start(self) -> None:
        self.status = StageState.RUNNING
        self.started_at = datetime.now(timezone.utc).isoformat()

    def finish(self, state: StageState, error: str | None = None) -> None:
        self.status, self.error = state, error
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def as_dict(self) -> dict:
        return asdict(self)

STAGE_DEFINITIONS = (
    ("context", "Context Intelligence", ()),
    ("mandate", "Mandate Resolution", ("context",)),
    ("portfolio", "Portfolio Context", ("mandate",)),
    ("planning", "Research Planning", ("portfolio",)),
    ("targets", "Target Discovery", ("planning",)),
    ("queries", "Query Generation", ("targets",)),
    ("discovery", "Web / Official Source Discovery", ("queries",)),
    ("documents", "Document Retrieval", ("discovery",)),
    ("incidents", "Incident Extraction", ("documents",)),
    ("evidence", "Evidence Verification", ("incidents",)),
    ("legal", "Legal Framework Discovery", ("evidence",)),
    ("applicability", "Legal Applicability", ("legal",)),
    ("relationships", "Relationship Analysis", ("applicability",)),
    ("candidates", "POI Candidates", ("relationships",)),
    ("generation", "Gemini Generation", ("candidates",)),
    ("uniqueness", "Uniqueness", ("generation",)),
    ("validation", "Validation", ("uniqueness",)),
    ("scoring", "Scoring", ("validation",)),
    ("finalized", "Finalized", ("scoring",)),
)
