from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.analysis import MatchAnalysisRequest, MatchAnalysisResponse
from app.services.matching_analyzer import analyze_match, get_cached_analysis

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze(request: MatchAnalysisRequest, db: Session = Depends(get_db)):
    if not request.force:
        cached = get_cached_analysis(db, request.resume_id, request.role_id)
        if cached:
            return cached

    try:
        return await analyze_match(db, request.resume_id, request.role_id, settings.openai_api_key)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.get("/analysis", response_model=MatchAnalysisResponse)
def read_analysis(
    resume_id: int = Query(...),
    role_id: int = Query(...),
    db: Session = Depends(get_db),
):
    cached = get_cached_analysis(db, resume_id, role_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="저장된 분석 결과가 없습니다.")
    return cached
