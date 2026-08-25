from pydantic import BaseModel, ConfigDict


class MemberSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_name: str
    competency: str
    evidence: str | None


class ResumeUploadResponse(BaseModel):
    id: int
    title: str | None
    skills: list[MemberSkillResponse]
