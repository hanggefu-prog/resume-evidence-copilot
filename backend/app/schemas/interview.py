from pydantic import BaseModel, Field


class InterviewQuestionsParsed(BaseModel):
    questions: list[str] = Field(default_factory=list)


class InterviewQuestionsRead(BaseModel):
    questions: list[str]
