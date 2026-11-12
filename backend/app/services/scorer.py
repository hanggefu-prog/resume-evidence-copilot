from app.schemas.candidate import CandidateParsed
from app.schemas.job import JobParsed
from app.schemas.scoring import FitScoreParsed
from app.services.llm_client import LLMProvider
from app.services.parsing import ParsedResult, parse_structured

SYSTEM_PROMPT = (
    "You are a recruiting fit-scoring assistant. Given a candidate profile and a job's "
    "requirements, produce a transparent fit assessment. Respond with ONLY a single JSON "
    "object with keys: score (0-100, weighted mostly by required_skills overlap and "
    "years of experience vs min_years_experience), reasoning (2-3 sentences explaining the "
    "score, mentioning specific skills), matched_skills (list of required skills the "
    "candidate has), missing_skills (list of required skills the candidate lacks). "
    "Be specific and grounded in the given data — do not invent skills not listed."
)


def score_fit(llm: LLMProvider, candidate: CandidateParsed, job: JobParsed) -> ParsedResult:
    user_prompt = (
        f"Candidate profile:\n{candidate.model_dump_json(indent=2)}\n\n"
        f"Job requirements:\n{job.model_dump_json(indent=2)}"
    )
    result = parse_structured(llm, SYSTEM_PROMPT, user_prompt, FitScoreParsed)
    assert isinstance(result.value, FitScoreParsed)
    return result
