from datetime import date

from pydantic import BaseModel


class MatchResult(BaseModel):
    application_id: int | None = None
    role_id: int
    role_name: str | None
    posting_id: int
    company: str
    title: str | None
    deadline: date | None
    linkareer_url: str
    apply_url: str | None
    match_score: int


class ExplainResponse(BaseModel):
    application_id: int
    explanation: str
