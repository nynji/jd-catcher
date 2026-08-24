from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_posting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(300), default="")
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    job_type: Mapped[str] = mapped_column(String(300), default="")
    industry: Mapped[str] = mapped_column(String(300), default="")
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    has_cover_letter: Mapped[bool] = mapped_column(Boolean, default=False)
    linkareer_url: Mapped[str] = mapped_column(String(1000), unique=True)
    apply_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    is_image_based: Mapped[bool] = mapped_column(Boolean, default=False)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    submission_requirements: Mapped[list["SubmissionRequirement"]] = relationship(
        back_populates="posting", cascade="all, delete-orphan"
    )
    cover_letter_questions: Mapped[list["CoverLetterQuestion"]] = relationship(
        back_populates="posting", cascade="all, delete-orphan"
    )


class SubmissionRequirement(Base):
    __tablename__ = "submission_requirement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    posting_id: Mapped[int] = mapped_column(ForeignKey("job_posting.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(30))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    posting: Mapped[JobPosting] = relationship(back_populates="submission_requirements")


class CoverLetterQuestion(Base):
    __tablename__ = "cover_letter_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    posting_id: Mapped[int] = mapped_column(ForeignKey("job_posting.id", ondelete="CASCADE"))
    role_name: Mapped[str] = mapped_column(String(300), default="")
    question_text: Mapped[str] = mapped_column(Text)
    char_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_order: Mapped[int] = mapped_column(Integer)

    posting: Mapped[JobPosting] = relationship(back_populates="cover_letter_questions")