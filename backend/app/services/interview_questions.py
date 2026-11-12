from app.schemas.candidate import CandidateParsed
from app.schemas.interview import InterviewQuestionsParsed
from app.schemas.job import JobParsed
from app.services.llm_client import LLMProvider
from app.services.parsing import ParsedResult, parse_structured

SYSTEM_PROMPT = (
    "You are an interview panel assistant. Given a candidate profile and a job's "
    "requirements, generate 5 targeted interview questions that probe the candidate's "
    "specific claimed skills and experience against what the job actually requires — "
    "especially any gaps. Respond with ONLY a single JSON object with key: "
    "questions (list of 5 strings)."
)


def generate_questions(llm: LLMProvider, candidate: CandidateParsed, job: JobParsed) -> ParsedResult:
    user_prompt = (
        f"Candidate profile:\n{candidate.model_dump_json(indent=2)}\n\n"
        f"Job requirements:\n{job.model_dump_json(indent=2)}"
    )
    result = parse_structured(llm, SYSTEM_PROMPT, user_prompt, InterviewQuestionsParsed)
    assert isinstance(result.value, InterviewQuestionsParsed)
    return result
