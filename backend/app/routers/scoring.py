import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_llm
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.score_result import ScoreResult
from app.schemas.candidate import CandidateParsed
from app.schemas.job import JobParsed
from app.schemas.scoring import ScoreRead
from app.services.cost_tracker import record_llm_call
from app.services.evidence import RequirementEvidence, compare_requirements, required_items
from app.services.llm_client import LLMProvider, LLMProviderUnavailableError
from app.services.parsing import ParsingFailedError
from app.services.scorer import score_fit

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/{candidate_id}/{job_id}/evidence", response_model=list[RequirementEvidence])
def review_evidence(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
):
    candidate = db.get(Candidate, candidate_id)
    job = db.get(Job, job_id)
    if candidate is None or job is None:
        raise HTTPException(status_code=404, detail="Candidate or job not found")
    if not job.parsed or not candidate.raw_text.strip():
        raise HTTPException(status_code=422, detail="需要岗位解析结果和简历原文才能进行对照")
    items = required_items(JobParsed.model_validate(job.parsed))
    if not items:
        return []
    started = time.perf_counter()
    try:
        rows, result = compare_requirements(llm, items, candidate.raw_text)
    except ParsingFailedError as exc:
        record_llm_call(
            db, purpose="evidence", provider=llm.provider_name, model=llm.model,
            usage=exc.usage, attempts=exc.attempts, success=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            error="Invalid structured evidence response",
        )
        db.commit()
        raise HTTPException(status_code=422, detail="原文对照生成失败，请重试") from exc
    except LLMProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    record_llm_call(
        db, purpose="evidence", provider=llm.provider_name, model=llm.model,
        usage=result.usage, attempts=result.attempts, success=True,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    db.commit()
    return rows


@router.post("/{candidate_id}/{job_id}", response_model=ScoreRead, status_code=201)
def create_score(
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
    if not candidate.parsed:
        raise HTTPException(status_code=422, detail="Candidate has no parsed profile yet")
    if not job.parsed:
        raise HTTPException(status_code=422, detail="Job has no parsed profile yet")

    candidate_parsed = CandidateParsed.model_validate(candidate.parsed)
    job_parsed = JobParsed.model_validate(job.parsed)

    started = time.perf_counter()
    try:
        result = score_fit(llm, candidate_parsed, job_parsed)
    except ParsingFailedError as exc:
        record_llm_call(
            db, purpose="scoring", provider=llm.provider_name, model=llm.model,
            usage=exc.usage, attempts=exc.attempts,
            latency_ms=(time.perf_counter() - started) * 1000, success=False, error=exc.last_error,
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderUnavailableError as exc:
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record_llm_call(
        db, purpose="scoring", provider=llm.provider_name, model=llm.model,
        usage=result.usage, attempts=result.attempts,
        latency_ms=(time.perf_counter() - started) * 1000, success=True,
    )

    fit = result.value
    score_row = ScoreResult(
        candidate_id=candidate_id,
        job_id=job_id,
        score=fit.score,
        reasoning=fit.reasoning,
        matched_skills=fit.matched_skills,
        missing_skills=fit.missing_skills,
    )
    db.add(score_row)
    db.commit()
    db.refresh(score_row)
    return score_row


@router.get("/{candidate_id}/{job_id}", response_model=list[ScoreRead])
def list_scores(candidate_id: uuid.UUID, job_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(ScoreResult)
        .filter(ScoreResult.candidate_id == candidate_id, ScoreResult.job_id == job_id)
        .order_by(ScoreResult.created_at.desc())
        .all()
    )
