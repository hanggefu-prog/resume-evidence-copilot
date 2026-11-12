"""Semantic search: pgvector cosine-similarity retrieval + heuristic re-rank.

This is the RAG retrieval layer. Two-stage design:
1. Retrieval: pgvector cosine-distance search narrows the full pool to
   RETRIEVAL_K candidates — this is the "R" in RAG, cheap and scales.
2. Re-rank: within that pool, re-order using structured signals (required-
   skill overlap, minimum experience fit) that raw embedding similarity can't
   see — two candidates can read as semantically similar to a JD while only
   one actually has the required skills.

A cross-encoder model is the standard upgrade path for stage 2, and is the
honest answer to "why not a real re-ranker": skipped here for extra
dependency/latency cost with no labeled relevance data yet to prove it
beats this heuristic. See docs/architecture.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.candidate import CandidateParsed
from app.schemas.job import JobParsed

RETRIEVAL_K = 20
DEFAULT_TOP_N = 10

# Re-rank weights: tunable, not learned. Vector similarity dominates (it's the
# semantic-fit signal) but skill overlap and minimum experience fit correct for
# cases the embedding alone misses.
WEIGHT_VECTOR_SIMILARITY = 0.5
WEIGHT_SKILL_OVERLAP = 0.3
WEIGHT_EXPERIENCE_FIT = 0.2


@dataclass
class RankedResult:
    id: str
    vector_similarity: float
    skill_overlap: float
    experience_fit: float
    rerank_score: float


def _skill_overlap(have: list[str], required: list[str]) -> float:
    if not required:
        return 0.0
    have_lower = {s.lower() for s in have}
    matched = sum(1 for s in required if s.lower() in have_lower)
    return matched / len(required)


def _experience_fit(years: float, min_years: float) -> float:
    if min_years <= 0:
        return 1.0
    return min(1.0, max(0.0, years) / min_years)


def _rerank_score(vector_similarity: float, skill_overlap: float, experience_fit: float) -> float:
    return (
        WEIGHT_VECTOR_SIMILARITY * vector_similarity
        + WEIGHT_SKILL_OVERLAP * skill_overlap
        + WEIGHT_EXPERIENCE_FIT * experience_fit
    )


def search_candidates_for_job(db: Session, job: Job, top_n: int = DEFAULT_TOP_N) -> list[tuple[Candidate, RankedResult]]:
    if job.embedding is None:
        return []

    distance_col = Candidate.embedding.cosine_distance(job.embedding).label("distance")
    rows = (
        db.query(Candidate, distance_col)
        .filter(Candidate.embedding.isnot(None))
        .order_by(distance_col)
        .limit(RETRIEVAL_K)
        .all()
    )

    job_parsed = JobParsed.model_validate(job.parsed) if job.parsed else JobParsed()

    ranked: list[tuple[Candidate, RankedResult]] = []
    for candidate, distance in rows:
        candidate_parsed = (
            CandidateParsed.model_validate(candidate.parsed) if candidate.parsed else CandidateParsed()
        )
        vector_similarity = 1.0 - float(distance)
        skill_overlap = _skill_overlap(candidate_parsed.skills, job_parsed.required_skills)
        experience_fit = _experience_fit(candidate_parsed.years_experience, job_parsed.min_years_experience)
        score = _rerank_score(vector_similarity, skill_overlap, experience_fit)
        ranked.append((
            candidate,
            RankedResult(
                id=str(candidate.id),
                vector_similarity=round(vector_similarity, 4),
                skill_overlap=round(skill_overlap, 4),
                experience_fit=round(experience_fit, 4),
                rerank_score=round(score, 4),
            ),
        ))

    ranked.sort(key=lambda pair: pair[1].rerank_score, reverse=True)
    return ranked[:top_n]


def search_jobs_for_candidate(db: Session, candidate: Candidate, top_n: int = DEFAULT_TOP_N) -> list[tuple[Job, RankedResult]]:
    if candidate.embedding is None:
        return []

    distance_col = Job.embedding.cosine_distance(candidate.embedding).label("distance")
    rows = (
        db.query(Job, distance_col)
        .filter(Job.embedding.isnot(None))
        .order_by(distance_col)
        .limit(RETRIEVAL_K)
        .all()
    )

    candidate_parsed = (
        CandidateParsed.model_validate(candidate.parsed) if candidate.parsed else CandidateParsed()
    )

    ranked: list[tuple[Job, RankedResult]] = []
    for job, distance in rows:
        job_parsed = JobParsed.model_validate(job.parsed) if job.parsed else JobParsed()
        vector_similarity = 1.0 - float(distance)
        skill_overlap = _skill_overlap(candidate_parsed.skills, job_parsed.required_skills)
        experience_fit = _experience_fit(candidate_parsed.years_experience, job_parsed.min_years_experience)
        score = _rerank_score(vector_similarity, skill_overlap, experience_fit)
        ranked.append((
            job,
            RankedResult(
                id=str(job.id),
                vector_similarity=round(vector_similarity, 4),
                skill_overlap=round(skill_overlap, 4),
                experience_fit=round(experience_fit, 4),
                rerank_score=round(score, 4),
            ),
        ))

    ranked.sort(key=lambda pair: pair[1].rerank_score, reverse=True)
    return ranked[:top_n]
