import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_embedder, get_llm
from app.models.audit_log import AuditLog
from app.models.job import Job
from app.schemas.job import JobCreateRequest, JobRead
from app.services.cost_tracker import record_llm_call
from app.services.embeddings import EmbeddingProvider
from app.services.file_extraction import UnsupportedFileTypeError, extract_text
from app.services.jd_parser import parse_jd
from app.services.llm_client import LLMProvider, LLMProviderUnavailableError
from app.services.parsing import ParsingFailedError

router = APIRouter(prefix="/jobs", tags=["jobs"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB


def _create_job_from_text(
    raw_text: str, db: Session, llm: LLMProvider, embedder: EmbeddingProvider
) -> Job:
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the input")

    started = time.perf_counter()
    try:
        result = parse_jd(llm, raw_text)
    except ParsingFailedError as exc:
        record_llm_call(
            db, purpose="job.parse", provider=llm.provider_name, model=llm.model,
            usage=exc.usage, attempts=exc.attempts,
            latency_ms=(time.perf_counter() - started) * 1000, success=False, error=exc.last_error,
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderUnavailableError as exc:
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record_llm_call(
        db, purpose="job.parse", provider=llm.provider_name, model=llm.model,
        usage=result.usage, attempts=result.attempts,
        latency_ms=(time.perf_counter() - started) * 1000, success=True,
    )

    parsed = result.value
    embedding = embedder.embed(raw_text)

    job = Job(raw_text=raw_text, parsed=parsed.model_dump(), embedding=embedding)
    db.add(job)
    db.flush()

    db.add(
        AuditLog(
            action="job.parsed",
            resource_type="job",
            resource_id=str(job.id),
            meta={"required_skills_found": len(parsed.required_skills)},
        )
    )
    db.commit()
    db.refresh(job)
    return job


@router.post("", response_model=JobRead, status_code=201)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    embedder: EmbeddingProvider = Depends(get_embedder),
):
    return _create_job_from_text(payload.raw_text, db, llm, embedder)


@router.post("/upload", response_model=JobRead, status_code=201)
async def upload_job(
    file: UploadFile,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    embedder: EmbeddingProvider = Depends(get_embedder),
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    try:
        raw_text = extract_text(file.filename or "upload.txt", content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _create_job_from_text(raw_text, db, llm, embedder)


@router.get("", response_model=list[JobRead])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
