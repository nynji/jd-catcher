from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemberSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_name: str
    competency: str
    evidence: str | None


class ResumeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime | None


class ResumeUploadResponse(BaseModel):
    id: int
    title: str | None
    skills: list[MemberSkillResponse]
