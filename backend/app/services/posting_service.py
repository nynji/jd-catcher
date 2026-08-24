from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.posting import JobPosting


def list_postings(
    db: Session,
    page: int,
    size: int,
    order_by: str,
) -> list[JobPosting]:
    ordering = (
        JobPosting.deadline.desc().nulls_last()
        if order_by == "deadline"
        else JobPosting.collected_at.desc()
    )
    statement = (
        select(JobPosting)
        .order_by(ordering)
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(statement).all())


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