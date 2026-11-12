import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.search import RankedCandidateRead, RankedJobRead
from app.services.search import search_candidates_for_job, search_jobs_for_candidate

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/jobs/{job_id}/candidates", response_model=list[RankedCandidateRead])
def candidates_for_job(job_id: uuid.UUID, top_n: int = 10, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    ranked = search_candidates_for_job(db, job, top_n=top_n)
    return [
        RankedCandidateRead(
            id=candidate.id,
            raw_text=candidate.raw_text,
            parsed=candidate.parsed,
            created_at=candidate.created_at,
            vector_similarity=result.vector_similarity,
            skill_overlap=result.skill_overlap,
            experience_fit=result.experience_fit,
            rerank_score=result.rerank_score,
        )
        for candidate, result in ranked
    ]


@router.get("/candidates/{candidate_id}/jobs", response_model=list[RankedJobRead])
def jobs_for_candidate(candidate_id: uuid.UUID, top_n: int = 10, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    ranked = search_jobs_for_candidate(db, candidate, top_n=top_n)
    return [
        RankedJobRead(
            id=job.id,
            raw_text=job.raw_text,
            parsed=job.parsed,
            created_at=job.created_at,
            vector_similarity=result.vector_similarity,
            skill_overlap=result.skill_overlap,
            experience_fit=result.experience_fit,
            rerank_score=result.rerank_score,
        )
        for job, result in ranked
    ]
