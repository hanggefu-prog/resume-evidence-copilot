import uuid

from sqlalchemy import Column, DateTime, Float, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class ScoreResult(Base):
    __tablename__ = "score_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    reasoning = Column(Text, nullable=False)
    matched_skills = Column(JSONB, nullable=True)
    missing_skills = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
