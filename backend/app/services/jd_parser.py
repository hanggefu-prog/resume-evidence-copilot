from app.services.llm_client import LLMProvider
from app.services.parsing import ParsedResult, parse_structured
from app.schemas.job import JobParsed

SYSTEM_PROMPT = (
    "You are a job description parser. Extract structured fields from raw job "
    "description text. Respond with ONLY a single JSON object with keys: "
    "title, company, required_skills (list of strings), nice_to_have_skills "
    "(list of strings), min_years_experience (number), summary (one paragraph). "
    "If a field is missing from the text, use an empty string, empty list, or 0."
)


def parse_jd(llm: LLMProvider, raw_text: str) -> ParsedResult:
    user_prompt = f"Job description text:\n\n{raw_text}"
    result = parse_structured(llm, SYSTEM_PROMPT, user_prompt, JobParsed)
    assert isinstance(result.value, JobParsed)
    return result
