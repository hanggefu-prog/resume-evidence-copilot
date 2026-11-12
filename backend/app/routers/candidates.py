import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_embedder, get_llm
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreateRequest, CandidateRead
from app.services.cost_tracker import record_llm_call
from app.services.cv_parser import parse_cv
from app.services.embeddings import EmbeddingProvider
from app.services.file_extraction import UnsupportedFileTypeError, extract_text
from app.services.llm_client import LLMProvider, LLMProviderUnavailableError
from app.services.parsing import ParsingFailedError

router = APIRouter(prefix="/candidates", tags=["candidates"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB


def _create_candidate_from_text(
    raw_text: str, db: Session, llm: LLMProvider, embedder: EmbeddingProvider
) -> Candidate:
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the input")

    started = time.perf_counter()
    try:
        result = parse_cv(llm, raw_text)
    except ParsingFailedError as exc:
        record_llm_call(
            db, purpose="candidate.parse", provider=llm.provider_name, model=llm.model,
            usage=exc.usage, attempts=exc.attempts,
            latency_ms=(time.perf_counter() - started) * 1000, success=False, error=exc.last_error,
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMProviderUnavailableError as exc:
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record_llm_call(
        db, purpose="candidate.parse", provider=llm.provider_name, model=llm.model,
        usage=result.usage, attempts=result.attempts,
        latency_ms=(time.perf_counter() - started) * 1000, success=True,
    )

    parsed = result.value
    embedding = embedder.embed(raw_text)

    candidate = Candidate(raw_text=raw_text, parsed=parsed.model_dump(), embedding=embedding)
    db.add(candidate)
    db.flush()

    db.add(
        AuditLog(
            action="candidate.parsed",
            resource_type="candidate",
            resource_id=str(candidate.id),
            meta={"skills_found": len(parsed.skills)},
        )
    )
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("", response_model=CandidateRead, status_code=201)
def create_candidate(
    payload: CandidateCreateRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm),
    embedder: EmbeddingProvider = Depends(get_embedder),
):
    return _create_candidate_from_text(payload.raw_text, db, llm, embedder)


@router.post("/upload", response_model=CandidateRead, status_code=201)
async def upload_candidate(
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

    return _create_candidate_from_text(raw_text, db, llm, embedder)


@router.get("", response_model=list[CandidateRead])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: uuid.UUID, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
