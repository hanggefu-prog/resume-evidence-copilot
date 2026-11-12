from app.models.candidate import Candidate
from app.models.job import Job
from app.services.embeddings import FakeHashEmbedding
from app.services.search import (
    DEFAULT_TOP_N,
    RETRIEVAL_K,
    _experience_fit,
    _skill_overlap,
    search_candidates_for_job,
    search_jobs_for_candidate,
)

# --- pure heuristic math -----------------------------------------------------


def test_skill_overlap_full_match():
    assert _skill_overlap(["Python", "FastAPI", "AWS"], ["Python", "FastAPI"]) == 1.0


def test_skill_overlap_partial_match_case_insensitive():
    assert _skill_overlap(["python", "docker"], ["Python", "FastAPI"]) == 0.5


def test_skill_overlap_no_required_skills_is_zero():
    assert _skill_overlap(["Python"], []) == 0.0


def test_skill_overlap_no_overlap():
    assert _skill_overlap(["Photoshop"], ["Python", "FastAPI"]) == 0.0


def test_experience_fit_exact_match():
    assert _experience_fit(years=3, min_years=3) == 1.0


def test_experience_fit_zero_min_years_always_full_fit():
    assert _experience_fit(years=0, min_years=0) == 1.0


def test_experience_fit_above_minimum_gets_full_credit():
    assert _experience_fit(years=6, min_years=3) == 1.0


def test_experience_fit_below_minimum_scales_proportionally():
    assert _experience_fit(years=1.5, min_years=3) == 0.5
    assert _experience_fit(years=0, min_years=3) == 0.0


# --- DB-backed plumbing -------------------------------------------------------


def _make_candidate(db_session, raw_text: str, skills: list[str], years: float) -> Candidate:
    embedder = FakeHashEmbedding()
    c = Candidate(
        raw_text=raw_text,
        parsed={"name": raw_text, "skills": skills, "years_experience": years},
        embedding=embedder.embed(raw_text),
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _make_job(db_session, raw_text: str, required_skills: list[str], min_years: float) -> Job:
    embedder = FakeHashEmbedding()
    j = Job(
        raw_text=raw_text,
        parsed={"title": raw_text, "required_skills": required_skills, "min_years_experience": min_years},
        embedding=embedder.embed(raw_text),
    )
    db_session.add(j)
    db_session.commit()
    db_session.refresh(j)
    return j


def test_search_candidates_for_job_returns_sorted_by_rerank_score(db_session):
    job = _make_job(db_session, "Backend Engineer needing Python", ["Python", "FastAPI"], 3)
    _make_candidate(db_session, "candidate one", ["Python", "FastAPI"], 3)
    _make_candidate(db_session, "candidate two", ["Photoshop"], 1)

    ranked = search_candidates_for_job(db_session, job, top_n=DEFAULT_TOP_N)

    assert len(ranked) == 2
    scores = [result.rerank_score for _, result in ranked]
    assert scores == sorted(scores, reverse=True)


def test_search_candidates_for_job_respects_top_n(db_session):
    job = _make_job(db_session, "Some job", ["Python"], 1)
    for i in range(5):
        _make_candidate(db_session, f"candidate {i}", ["Python"], 1)

    ranked = search_candidates_for_job(db_session, job, top_n=2)

    assert len(ranked) == 2


def test_search_candidates_for_job_with_no_embedding_returns_empty(db_session):
    job = Job(raw_text="no embedding job", parsed={}, embedding=None)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert search_candidates_for_job(db_session, job) == []


def test_search_jobs_for_candidate_returns_sorted(db_session):
    candidate = _make_candidate(db_session, "Python dev", ["Python", "FastAPI"], 4)
    _make_job(db_session, "job one", ["Python", "FastAPI"], 3)
    _make_job(db_session, "job two", ["Rust"], 8)

    ranked = search_jobs_for_candidate(db_session, candidate, top_n=DEFAULT_TOP_N)

    assert len(ranked) == 2
    scores = [result.rerank_score for _, result in ranked]
    assert scores == sorted(scores, reverse=True)


def test_retrieval_k_bounds_pool_size():
    assert RETRIEVAL_K >= DEFAULT_TOP_N  # sanity: retrieval pool can't be smaller than what we return
