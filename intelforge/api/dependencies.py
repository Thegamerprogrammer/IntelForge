from __future__ import annotations
import os
from ..core.pipeline import ResearchPipeline
from ..persistence import Database

def database() -> Database:
    return Database(os.getenv("INTELFORGE_DATABASE", "intelforge.db"))
def pipeline() -> ResearchPipeline:
    return ResearchPipeline(database=database())
