from pydantic import BaseModel, Field

class JobInput(BaseModel):
    committee: str
    agenda: str
    portfolio: str
    freeze_date: str | None = None
    background_guide: str | None = None
    research_notes: str = ""
    extra_links: list[str] = Field(default_factory=list)
    target_countries: list[str] = Field(default_factory=list)
    poi_count: int = 10
    aggression: int = 50
    controversy: int = 50
    diplomacy: int = 50
    gemini_model: str | None = None
    ollama_model: str | None = None
