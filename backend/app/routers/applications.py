from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.database import get_db
from app.models.matching import Application, PostingRole
from app.models.member import MemberSkill
from app.schemas.matching import ExplainResponse
from app.services.explain_service import explain_match

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/{application_id}/explain", response_model=ExplainResponse)
async def explain_application(application_id: int, db: Session = Depends(get_db)):
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="지원 기록을 찾을 수 없습니다.")

    role = db.get(PostingRole, application.role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="공고 직무를 찾을 수 없습니다.")

    member_skills = [
        skill.skill_name
        for skill in db.query(MemberSkill).filter(MemberSkill.resume_id == application.resume_id).all()
        if skill.skill_name
    ]
    posting_skills = [skill.skill_name for skill in role.skills if skill.skill_name]

    try:
        explanation = await explain_match(
            member_skills=member_skills,
            role_name=role.role_name or "",
            posting_skills=posting_skills,
            match_score=application.match_score or 0,
            api_key=settings.openai_api_key,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return ExplainResponse(application_id=application.id, explanation=explanation)
