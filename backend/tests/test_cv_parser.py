import json

import pytest

from app.services.cv_parser import parse_cv
from app.services.llm_client import MockLLMProvider
from app.services.parsing import ParsingFailedError

VALID_CV_JSON = json.dumps(
    {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1 555 0100",
        "skills": ["Python", "FastAPI"],
        "years_experience": 4,
        "education": ["BSc Computer Science"],
        "summary": "Backend engineer with 4 years of experience.",
    }
)


def test_parse_cv_valid_first_try():
    llm = MockLLMProvider(responses=[VALID_CV_JSON])
    result = parse_cv(llm, "Jane Doe, backend engineer, 4 years Python/FastAPI")

    assert result.value.name == "Jane Doe"
    assert "Python" in result.value.skills
    assert len(llm.calls) == 1
    assert result.attempts == 1
    assert result.usage.total_tokens == 20  # mock returns 10+10 per call


def test_parse_cv_retries_after_invalid_json():
    llm = MockLLMProvider(responses=["not json at all", VALID_CV_JSON])
    result = parse_cv(llm, "some cv text")

    assert result.value.name == "Jane Doe"
    assert len(llm.calls) == 2  # first attempt failed, second succeeded
    assert result.attempts == 2
    assert result.usage.total_tokens == 40  # aggregated across both attempts


def test_parse_cv_retries_after_schema_violation():
    invalid_schema = json.dumps({"skills": "not a list"})  # wrong type
    llm = MockLLMProvider(responses=[invalid_schema, VALID_CV_JSON])
    result = parse_cv(llm, "some cv text")

    assert result.value.name == "Jane Doe"
    assert len(llm.calls) == 2


def test_parse_cv_gives_up_after_max_attempts():
    llm = MockLLMProvider(responses=["garbage", "garbage", "garbage"])
    with pytest.raises(ParsingFailedError) as exc_info:
        parse_cv(llm, "some cv text")

    assert len(llm.calls) == 3
    assert exc_info.value.attempts == 3
    assert exc_info.value.usage.total_tokens == 60  # usage tracked even on failure


def test_parse_cv_missing_fields_default_to_empty():
    minimal_json = json.dumps({"name": "Minimal Candidate"})
    llm = MockLLMProvider(responses=[minimal_json])
    result = parse_cv(llm, "sparse cv")

    assert result.value.name == "Minimal Candidate"
    assert result.value.skills == []
    assert result.value.years_experience == 0
