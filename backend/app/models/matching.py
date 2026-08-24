from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PostingRole(Base):
    __tablename__ = "posting_role"

    id: Mapped[int] = mapped_column(primary_key=True)
    posting_id: Mapped[int] = mapped_column(ForeignKey("job_posting.id", ondelete="CASCADE"))
    role_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(300), nullable=True)
    role_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    posting: Mapped["JobPosting"] = relationship()
    skills: Mapped[list["PostingSkill"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class PostingSkill(Base):
    __tablename__ = "posting_skill"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("posting_role.id", ondelete="CASCADE"))
    skill_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    competency: Mapped[str | None] = mapped_column(String(300), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(50), nullable=True)

    role: Mapped[PostingRole] = relationship(back_populates="skills")


class Application(Base):
    __tablename__ = "application"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("posting_role.id", ondelete="CASCADE"))
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("member_resume.id"), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MatchAnalysis(Base):
    __tablename__ = "match_analysis"
    __table_args__ = (UniqueConstraint("resume_id", "role_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("member_resume.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("posting_role.id", ondelete="CASCADE"))
    ai_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_points: Mapped[list[dict]] = mapped_column(JSON, default=list)
    gap_points: Mapped[list[dict]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_emphasis: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
