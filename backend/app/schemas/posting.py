from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PostingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    title: str | None
    job_type: str
    industry: str
    location: str | None
    deadline: date | None
    has_cover_letter: bool
    linkareer_url: str
    apply_url: str | None
    collected_at: datetime | None


class SubmissionRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    posting_id: int
    type: str
    is_required: bool
    detail: str | None


class CoverLetterQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    posting_id: int
    role_name: str
    question_text: str
    char_limit: int | None
    question_order: int


class PostingDetail(PostingSummary):
    raw_text: str
    is_image_based: bool
    image_urls: list[str]
    submission_requirements: list[SubmissionRequirementResponse]
    cover_letter_questions: list[CoverLetterQuestionResponse]