import json

import pytest

from app.services.jd_parser import parse_jd
from app.services.llm_client import MockLLMProvider
from app.services.parsing import ParsingFailedError

VALID_JD_JSON = json.dumps(
    {
        "title": "Full-Stack AI Engineer",
        "company": "Acme AI",
        "required_skills": ["Python", "React"],
        "nice_to_have_skills": ["LangGraph"],
        "min_years_experience": 3,
        "summary": "Build production AI features end to end.",
    }
)


def test_parse_jd_valid_first_try():
    llm = MockLLMProvider(responses=[VALID_JD_JSON])
    result = parse_jd(llm, "Full-Stack AI Engineer at Acme AI, 3+ years")

    assert result.value.title == "Full-Stack AI Engineer"
    assert "Python" in result.value.required_skills


def test_parse_jd_retries_after_invalid_json():
    llm = MockLLMProvider(responses=["```markdown\nnot json\n```", VALID_JD_JSON])
    result = parse_jd(llm, "some jd text")

    assert result.value.company == "Acme AI"
    assert len(llm.calls) == 2


def test_parse_jd_strips_code_fences():
    fenced = f"```json\n{VALID_JD_JSON}\n```"
    llm = MockLLMProvider(responses=[fenced])
    result = parse_jd(llm, "some jd text")

    assert result.value.title == "Full-Stack AI Engineer"


def test_parse_jd_gives_up_after_max_attempts():
    llm = MockLLMProvider(responses=["nope", "still nope", "nope again"])
    with pytest.raises(ParsingFailedError):
        parse_jd(llm, "some jd text")
