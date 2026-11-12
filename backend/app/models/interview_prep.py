import uuid

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class InterviewPrep(Base):
    __tablename__ = "interview_preps"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    job_id = Column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    evidence = Column(JSONB, nullable=False, default=list)
    edits = Column(JSONB, nullable=False, default=dict)
    outline = Column(JSONB(none_as_null=True), nullable=True)
