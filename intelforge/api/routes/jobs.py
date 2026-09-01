from datetime import date
from fastapi import APIRouter, HTTPException
from ...core.models import ResearchSettings
from ..dependencies import database, pipeline
from ..schemas import JobInput

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
def settings(body: JobInput) -> ResearchSettings:
    return ResearchSettings(**{**body.model_dump(), "freeze_date": date.fromisoformat(body.freeze_date) if body.freeze_date else None, "extra_links": tuple(body.extra_links), "target_countries": tuple(body.target_countries)})
@router.post("")
def create(body: JobInput):
    return {"job_id": database().create_job(settings(body).__dict__)}
@router.get("/{job_id}")
def get(job_id: int):
    value = database().status(job_id)
    if not value: raise HTTPException(404, "Job not found")
    return value
@router.post("/{job_id}/run")
def run(job_id: int):
    job = database().status(job_id)
    if not job: raise HTTPException(404, "Job not found")
    raw = job["payload"]; raw["freeze_date"] = date.fromisoformat(raw["freeze_date"]) if raw.get("freeze_date") else None
    raw["extra_links"], raw["target_countries"] = tuple(raw.get("extra_links", ())), tuple(raw.get("target_countries", ()))
    return pipeline().run(ResearchSettings(**raw), job_id=job_id)
@router.get("/{job_id}/status")
def status(job_id: int): return get(job_id)
@router.get("/{job_id}/{kind}")
def artifacts(job_id: int, kind: str): return database().artifacts(job_id, kind)
