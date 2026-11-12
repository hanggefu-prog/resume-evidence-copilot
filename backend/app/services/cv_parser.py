from app.services.llm_client import LLMProvider
from app.services.parsing import ParsedResult, parse_structured
from app.schemas.candidate import CandidateParsed

SYSTEM_PROMPT = (
    "You are a CV/resume parser. Extract structured fields from raw CV text. "
    "Respond with ONLY a single JSON object with keys: "
    "name, email, phone, skills (list of strings), years_experience (number), "
    "education (list of strings), summary (one paragraph). "
    "If a field is missing from the text, use an empty string, empty list, or 0."
)


def parse_cv(llm: LLMProvider, raw_text: str) -> ParsedResult:
    user_prompt = f"CV text:\n\n{raw_text}"
    result = parse_structured(llm, SYSTEM_PROMPT, user_prompt, CandidateParsed)
    assert isinstance(result.value, CandidateParsed)
    return result
