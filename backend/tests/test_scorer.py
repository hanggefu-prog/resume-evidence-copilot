import json

import pytest

from app.schemas.candidate import CandidateParsed
from app.schemas.job import JobParsed
from app.services.llm_client import MockLLMProvider
from app.services.parsing import ParsingFailedError
from app.services.scorer import score_fit

VALID_SCORE_JSON = json.dumps(
    {
        "score": 85,
        "reasoning": "Strong match on Python and FastAPI, meets experience bar.",
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": ["AWS"],
    }
)


def _candidate() -> CandidateParsed:
    return CandidateParsed(name="Jane Doe", skills=["Python", "FastAPI"], years_experience=5)


def _job() -> JobParsed:
    return JobParsed(title="Backend Engineer", required_skills=["Python", "FastAPI", "AWS"], min_years_experience=3)


def test_score_fit_valid_first_try():
    llm = MockLLMProvider(responses=[VALID_SCORE_JSON])
    result = score_fit(llm, _candidate(), _job())

    assert result.value.score == 85
    assert "Python" in result.value.matched_skills
    assert "AWS" in result.value.missing_skills


def test_score_fit_retries_on_invalid_json():
    llm = MockLLMProvider(responses=["not json", VALID_SCORE_JSON])
    result = score_fit(llm, _candidate(), _job())

    assert result.value.score == 85
    assert len(llm.calls) == 2


def test_score_fit_rejects_out_of_range_score():
    out_of_range = json.dumps({"score": 150, "reasoning": "x", "matched_skills": [], "missing_skills": []})
    llm = MockLLMProvider(responses=[out_of_range, VALID_SCORE_JSON])
    result = score_fit(llm, _candidate(), _job())

    assert result.value.score == 85  # first response rejected by score<=100 constraint


def test_score_fit_gives_up_after_max_attempts():
    llm = MockLLMProvider(responses=["nope", "nope", "nope"])
    with pytest.raises(ParsingFailedError):
        score_fit(llm, _candidate(), _job())
