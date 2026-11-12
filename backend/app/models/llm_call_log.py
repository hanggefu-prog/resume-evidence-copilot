import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class LLMCallLog(Base):
    """Observability record for every LLM call — the 'LangSmith-lite' layer.
    Free-tier OpenRouter calls are $0, but token/latency/success tracking is
    what lets you reason about cost and reliability once swapped to a paid
    model, and it's what recruiters mean by 'cost tracking' / 'observability'."""

    __tablename__ = "llm_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purpose = Column(String, nullable=False)  # e.g. "candidate.parse", "job.parse", "scoring", "interview_questions"
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=1)
    latency_ms = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
