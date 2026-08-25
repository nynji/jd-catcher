from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_name: Mapped[str] = mapped_column(String(200))
    anonymous_id: Mapped[str] = mapped_column(String(100))
    session_id: Mapped[str] = mapped_column(String(100))
    posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_posting.id", ondelete="SET NULL"), nullable=True
    )
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("posting_role.id", ondelete="SET NULL"), nullable=True
    )
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("member_resume.id", ondelete="SET NULL"), nullable=True
    )
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_scroll_depth_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
