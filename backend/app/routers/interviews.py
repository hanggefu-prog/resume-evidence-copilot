import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_llm
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.candidate import CandidateParsed
from app.schemas.interview import InterviewQuestionsRead
from app.schemas.job import JobParsed
from app.services.cost_tracker import record_llm_call
from app.services.interview_questions import generate_questions
from app.services.llm_client import LLMProvider, LLMProviderUnavailableError
from app.services.parsing import ParsingFailedError

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/{candidate_id}/{job_id}/questions", response_model=InterviewQuestionsRead)
def create_interview_questions(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not candidate.parsed or not job.parsed:
        raise HTTPException(status_code=422, detail="Candidate and job must be parsed first")

    candidate_parsed = CandidateParsed.model_validate(candidate.parsed)
    job_parsed = JobParsed.model_validate(job.parsed)

    started = time.perf_counter()
    try:
        result = generate_questions(llm, candidate_parsed, job_parsed)
    except ParsingFailedError as exc:
        record_llm_call(
            db, purpose="interview_questions", provider=llm.provider_name, model=llm.model,
            usage=exc.usage, attempts=exc.attempts,
            latency_ms=(time.perf_counter() - started) * 1000, success=False, error=exc.last_error,
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderUnavailableError as exc:
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record_llm_call(
        db, purpose="interview_questions", provider=llm.provider_name, model=llm.model,
        usage=result.usage, attempts=result.attempts,
        latency_ms=(time.perf_counter() - started) * 1000, success=True,
    )
    db.add(
        AuditLog(
            action="interview.questions_generated",
            resource_type="candidate",
            resource_id=str(candidate_id),
            meta={"job_id": str(job_id), "question_count": len(result.value.questions)},
        )
    )
    db.commit()
    return InterviewQuestionsRead(questions=result.value.questions)
