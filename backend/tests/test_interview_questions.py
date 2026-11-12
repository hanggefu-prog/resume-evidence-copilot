import json

import pytest

from app.schemas.candidate import CandidateParsed
from app.schemas.job import JobParsed
from app.services.interview_questions import generate_questions
from app.services.llm_client import MockLLMProvider
from app.services.parsing import ParsingFailedError

VALID_QUESTIONS_JSON = json.dumps(
    {
        "questions": [
            "Walk me through a production FastAPI service you built.",
            "How do you handle database migrations under load?",
            "Describe a time you debugged a performance regression.",
            "What's your approach to API versioning?",
            "How would you design rate limiting for a public API?",
        ]
    }
)


def test_generate_questions_returns_five():
    llm = MockLLMProvider(responses=[VALID_QUESTIONS_JSON])
    candidate = CandidateParsed(name="Jane Doe", skills=["Python", "FastAPI"], years_experience=5)
    job = JobParsed(title="Backend Engineer", required_skills=["Python", "FastAPI"], min_years_experience=3)

    result = generate_questions(llm, candidate, job)

    assert len(result.value.questions) == 5


def test_generate_questions_retries_on_invalid_json():
    llm = MockLLMProvider(responses=["garbage", VALID_QUESTIONS_JSON])
    candidate = CandidateParsed(name="Jane Doe")
    job = JobParsed(title="Backend Engineer")

    result = generate_questions(llm, candidate, job)

    assert len(result.value.questions) == 5
    assert len(llm.calls) == 2


def test_generate_questions_gives_up_after_max_attempts():
    llm = MockLLMProvider(responses=["nope", "nope", "nope"])
    with pytest.raises(ParsingFailedError):
        generate_questions(llm, CandidateParsed(), JobParsed())
