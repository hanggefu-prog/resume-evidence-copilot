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


class FollowUp(BaseModel):
    condition: str = Field(pattern=r"\S")
    question: str = Field(pattern=r"\S")


class GuideItem(BaseModel):
    outline_index: int = Field(ge=0)
    main_question: str = Field(pattern=r"\S")
    follow_ups: list[FollowUp] = Field(min_length=2, max_length=2)


class PrepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    evidence: list[RequirementEvidence]
    edits: Edits
    outline: list[Question] | None
    question_guide: list[GuideItem] | None
