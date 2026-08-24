from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.posting import PostingDetail, PostingSummary
from app.services.posting_service import get_posting, list_postings
from app.services.posting_skill_extractor import backfill_posting_skills

router = APIRouter(prefix="/postings", tags=["postings"])


@router.post("/roles/extract-skills")
async def extract_posting_role_skills(db: Session = Depends(get_db)):
    """posting_skill이 비어있는 세부 직무에 대해 GPT-4o로 요구 역량을 추출해 채운다."""
    try:
        return await backfill_posting_skills(db, settings.openai_api_key)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"역량 추출에 실패했습니다: {error}") from error


@router.get("", response_model=list[PostingSummary])
def read_postings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: Literal["deadline", "collected_at"] = "collected_at",
    db: Session = Depends(get_db),
):
    return list_postings(db, page, size, order_by)


@router.get("/{posting_id}", response_model=PostingDetail)
def read_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = get_posting(db, posting_id)
    if posting is None:
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다.")
    return posting