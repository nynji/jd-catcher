from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(300), nullable=True)
    name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemberResume(Base):
    __tablename__ = "member_resume"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    skills: Mapped[list["MemberSkill"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class MemberSkill(Base):
    __tablename__ = "member_skill"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("member_resume.id", ondelete="CASCADE"))
    skill_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    competency: Mapped[str | None] = mapped_column(String(300), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    resume: Mapped[MemberResume] = relationship(back_populates="skills")
