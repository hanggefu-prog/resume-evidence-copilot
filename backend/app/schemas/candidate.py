import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CandidateParsed(BaseModel):
    """Structured output the LLM must produce from raw CV text."""

    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = Field(default_factory=list)
    years_experience: float = 0
    education: list[str] = Field(default_factory=list)
    summary: str = ""


class CandidateCreateRequest(BaseModel):
    raw_text: str = Field(min_length=1)


class CandidateRead(BaseModel):
    id: uuid.UUID
    raw_text: str
    parsed: CandidateParsed | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
