import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobParsed(BaseModel):
    """Structured output the LLM must produce from raw job description text."""

    title: str = ""
    company: str = ""
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    min_years_experience: float = 0
    summary: str = ""


class JobCreateRequest(BaseModel):
    raw_text: str = Field(min_length=1)


class JobRead(BaseModel):
    id: uuid.UUID
    raw_text: str
    parsed: JobParsed | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
