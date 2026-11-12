from app.schemas.candidate import CandidateRead
from app.schemas.job import JobRead


class RankedCandidateRead(CandidateRead):
    vector_similarity: float
    skill_overlap: float
    experience_fit: float
    rerank_score: float


class RankedJobRead(JobRead):
    vector_similarity: float
    skill_overlap: float
    experience_fit: float
    rerank_score: float
