from time import perf_counter
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_llm
from app.models import Candidate, InterviewPrep, Job
from app.schemas.interview_prep import Edits, PrepRead, Review, Revision, SaveDraft
from app.schemas.job import JobParsed
from app.services.cost_tracker import record_llm_call
from app.services.evidence import compare_requirements, required_items
from app.services.interview_guide import generate_guide
from app.services.interview_prep_questions import questions_for_evidence
from app.services.llm_client import LLMAuthenticationError, LLMProvider, LLMProviderUnavailableError
from app.services.parsing import ParsingFailedError
from app.workflows.interview_prep import build_graph

router = APIRouter(prefix="/interview-prep", tags=["interview preparation"])


def commit_snapshot(db, row):
    # Return exactly the revision saved by this request, even if another tab
    # commits as soon as this transaction releases its row lock.
    snapshot = PrepRead.model_validate(row)
    db.commit()
    return snapshot


def locked_draft(db, prep_id):
    row = db.get(InterviewPrep, prep_id, with_for_update=True)
    if row is None:
        raise HTTPException(404, "准备记录不存在")
    return row


def check_version(row, version):
    if row.version != version:
        raise HTTPException(409, "草稿已在其他页面更新，请重新打开以读取最新版本")


def run_graph(db, row, llm, *, resume=False, items=None, resume_text=""):
    # The row lock, business record and checkpoints share a transaction. A failure
    # rolls them all back, so retrying resumes the same review checkpoint.
    conn = db.connection().connection.driver_connection
    saver = PostgresSaver(conn)
    purpose = "prep_questions" if resume else "prep_evidence"
    call = None
    started = perf_counter()

    def collect():
        nonlocal call
        if not items:
            return []
        rows, call = compare_requirements(llm, items, resume_text)
        return [item.model_dump() for item in rows]

    def generate(selected):
        nonlocal call
        call = questions_for_evidence(llm, selected)
        by_id = {q.requirement_id: q.model_dump() for q in call.value.questions}
        return [by_id[item["requirement_id"]] for item in selected]

    graph = build_graph(saver, collect, generate)
    config = {"configurable": {"thread_id": str(row.id)}}
    try:
        state = graph.invoke(
            Command(resume=row.edits) if resume else {}, config, durability="sync"
        )
    except (ParsingFailedError, LLMProviderUnavailableError) as exc:
        db.rollback()
        if isinstance(exc, ParsingFailedError):
            record_llm_call(
                db,
                purpose=purpose,
                provider=llm.provider_name,
                model=llm.model,
                usage=exc.usage,
                attempts=exc.attempts,
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                error="Invalid response",
            )
            db.commit()
            raise HTTPException(422, "模型返回的内容格式有误，请重试") from exc
        if isinstance(exc, LLMAuthenticationError):
            raise HTTPException(503, str(exc)) from exc
        raise HTTPException(503, "模型暂时不可用，请稍后重试") from exc

    if call:
        record_llm_call(
            db,
            purpose=purpose,
            provider=llm.provider_name,
            model=llm.model,
            usage=call.usage,
            attempts=call.attempts,
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
        )
    return state


@router.post("/open/{candidate_id}/{job_id}", response_model=PrepRead)
def open_draft(
    candidate_id: UUID,
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
):
    candidate = db.get(Candidate, candidate_id)
    job = db.get(Job, job_id)
    if candidate is None or job is None:
        raise HTTPException(404, "找不到候选人或岗位")
    if not job.parsed or not candidate.raw_text.strip():
        raise HTTPException(422, "需要岗位要求和简历原文")
    created = db.scalar(
        insert(InterviewPrep)
        .values(candidate_id=candidate_id, job_id=job_id)
        .on_conflict_do_nothing(index_elements=["candidate_id", "job_id"])
        .returning(InterviewPrep.id)
    )
    if created is None:
        return db.scalar(
            select(InterviewPrep).filter_by(candidate_id=candidate_id, job_id=job_id)
        )
    row = db.get(InterviewPrep, created)
    state = run_graph(
        db,
        row,
        llm,
        items=required_items(JobParsed.model_validate(job.parsed)),
        resume_text=candidate.raw_text,
    )
    row.evidence = state["evidence"]
    row.edits = Edits(
        reviews={
            i: Review()
            for i, item in enumerate(row.evidence)
            if item["status"] != "supported"
        },
        manual_questions=[],
    ).model_dump(mode="json")
    return commit_snapshot(db, row)


@router.put("/{prep_id}", response_model=PrepRead)
def save_draft(prep_id: UUID, body: SaveDraft, db: Annotated[Session, Depends(get_db)]):
    row = locked_draft(db, prep_id)
    check_version(row, body.version)
    if row.outline is not None:
        raise HTTPException(409, "提纲已生成")
    mandatory = {i for i, item in enumerate(row.evidence) if item["status"] != "supported"}
    submitted = set(body.edits.reviews)
    if not mandatory.issubset(submitted) or not submitted.issubset(range(len(row.evidence))):
        raise HTTPException(422, "复核条目与证据不一致")
    row.edits = body.edits.model_dump(mode="json")
    row.version += 1
    return commit_snapshot(db, row)


@router.post("/{prep_id}/generate", response_model=PrepRead)
def finish_draft(
    prep_id: UUID,
    body: Revision,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
):
    row = locked_draft(db, prep_id)
    if row.outline is not None:
        return row
    check_version(row, body.version)
    edits = Edits.model_validate(row.edits)
    if any(item.decision == "pending" for item in edits.reviews.values()):
        raise HTTPException(422, "请先决定每个待复核条目是否追问")
    if any(not q.strip() for q in edits.manual_questions):
        raise HTTPException(422, "请填写或移除空白手写题")
    row.outline = run_graph(db, row, llm, resume=True)["outline"]
    row.version += 1
    return commit_snapshot(db, row)


@router.post("/{prep_id}/question-guide", response_model=PrepRead)
def create_guide(
    prep_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[LLMProvider, Depends(get_llm)],
):
    row = locked_draft(db, prep_id)
    if row.question_guide is not None:
        return row
    if not row.outline:
        raise HTTPException(422, "请先生成包含问题的面试提纲")
    started = perf_counter()
    try:
        result = generate_guide(llm, row.outline, row.evidence, row.edits)
    except ParsingFailedError as exc:
        record_llm_call(db, purpose="interview_guide", provider=llm.provider_name, model=llm.model,
                        usage=exc.usage, attempts=exc.attempts, success=False,
                        latency_ms=(perf_counter() - started) * 1000, error="Invalid guide")
        db.commit()
        raise HTTPException(422, "提问稿格式有误，请重新生成") from exc
    except LLMProviderUnavailableError as exc:
        raise HTTPException(503, str(exc)) from exc
    row.question_guide = [group.model_dump() for group in result.value.groups]
    row.version += 1
    record_llm_call(db, purpose="interview_guide", provider=llm.provider_name, model=llm.model,
                    usage=result.usage, attempts=result.attempts, success=True,
                    latency_ms=(perf_counter() - started) * 1000)
    return commit_snapshot(db, row)
