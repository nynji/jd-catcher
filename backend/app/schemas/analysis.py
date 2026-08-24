from pydantic import BaseModel, ConfigDict


class MatchedPoint(BaseModel):
    applicant_capability: str
    jd_requirement: str
    explanation: str
    strength: str


class GapPoint(BaseModel):
    jd_requirement: str
    current_state: str
    suggestion: str


class MatchAnalysisRequest(BaseModel):
    resume_id: int
    role_id: int
    force: bool = False


class MatchAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: int
    role_id: int
    ai_match_score: int | None
    score_reason: str | None
    matched_points: list[MatchedPoint]
    gap_points: list[GapPoint]
    summary: str | None
    recommended_emphasis: list[str]
