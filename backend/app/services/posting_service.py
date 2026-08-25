from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.posting import JobPosting

# 마감일이 없는(상시모집) 공고는 계속 보여주고, 마감일이 지난 공고만 제외한다.
_NOT_EXPIRED = or_(JobPosting.deadline.is_(None), JobPosting.deadline >= date.today())


def list_postings(
    db: Session,
    page: int,
    size: int,
    order_by: str,
) -> list[JobPosting]:
    ordering = (
        JobPosting.deadline.asc().nulls_last()
        if order_by == "deadline"
        else JobPosting.collected_at.desc().nulls_last()
    )
    statement = (
        select(JobPosting)
        .where(_NOT_EXPIRED)
        # id를 2차 정렬 기준으로 둬서 collected_at/deadline 값이 같은 행이 있어도
        # 페이지마다 순서가 흔들리지 않게(중복/누락 없이) 한다.
        .order_by(ordering, JobPosting.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(statement).all())


def count_postings(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(JobPosting).where(_NOT_EXPIRED)) or 0


def get_posting(db: Session, posting_id: int) -> JobPosting | None:
    statement = (
        select(JobPosting)
        .options(
            selectinload(JobPosting.submission_requirements),
            selectinload(JobPosting.cover_letter_questions),
        )
        .where(JobPosting.id == posting_id)
    )
    return db.scalar(statement)