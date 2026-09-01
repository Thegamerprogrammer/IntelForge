from fastapi import APIRouter, HTTPException
from ...committees import CommitteeRegistry
from ...models import GeminiModelRegistry
from ...sources import SourceCapabilityRegistry

router = APIRouter(prefix="/api", tags=["catalog"])
@router.get("/health")
def health(): return {"service": "intelforge", "status": "ready"}
@router.get("/committees")
def committees(): return [item.as_dict() for item in CommitteeRegistry().all()]
@router.get("/committees/{identifier}")
def committee(identifier: str):
    item = CommitteeRegistry().get(identifier)
    if not item: raise HTTPException(404, "Committee not found")
    return item.as_dict()
@router.get("/sources")
def sources(): return SourceCapabilityRegistry().all()
@router.get("/models")
def models(): return [model.__dict__ for model in GeminiModelRegistry().discover()]
