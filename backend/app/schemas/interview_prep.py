from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.services.evidence import RequirementEvidence


class Review(BaseModel):
    decision: Literal["pending", "ask", "skip"] = "pending"
    note: str = ""


class Edits(BaseModel):
    reviews: dict[int, Review]
    manual_questions: list[str]


class Revision(BaseModel):
    version: int = Field(ge=1)


class SaveDraft(Revision):
    edits: Edits


class Question(BaseModel):
    text: str
    source: Literal["generated", "manual"]
    requirement_id: int | None = None
    reason: str | None = None


class PrepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    evidence: list[RequirementEvidence]
    edits: Edits
    outline: list[Question] | None
