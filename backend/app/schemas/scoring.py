import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FitScoreParsed(BaseModel):
    """Structured output the LLM must produce when scoring a candidate against a job."""

    score: float = Field(ge=0, le=100, default=0)
    reasoning: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class ScoreRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    score: float
    reasoning: str
    matched_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
