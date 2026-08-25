from datetime import datetime, timezone

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.database import get_db
from app.models.member import MemberResume, MemberSkill
from app.schemas.matching import MatchResult
from app.schemas.resume import MemberSkillResponse, ResumeUploadResponse
from app.services.ai_extractor import extract_skills_from_resume
from app.services.matching_service import (
    MEMBER_ID,
    compute_matches,
    get_stored_matches,
    upsert_applications,
)
from app.services.resume_extractor import extract_file_text

router = APIRouter(prefix="/resumes", tags=["resumes"])

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_FILES = 5


@router.post("", response_model=ResumeUploadResponse)
async def upload_resume(
    files: list[UploadFile] = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="파일을 하나 이상 업로드해주세요.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"파일은 한 번에 최대 {MAX_FILES}개까지 업로드할 수 있습니다.")

    combined_parts: list[str] = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, detail=f"'{file.filename}' 파일 크기는 10MB를 넘을 수 없습니다."
            )
        try:
            text = await extract_file_text(file.filename or "", content, settings.openai_api_key)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=400, detail=f"'{file.filename}' 파일을 처리하지 못했습니다: {error}"
            ) from error
        if text.strip():
            combined_parts.append(f"=== {file.filename} ===\n{text}")

    raw_text = "\n\n".join(combined_parts).strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출하지 못했습니다.")

    try:
        skills = await extract_skills_from_resume(raw_text, settings.openai_api_key)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    try:
        resume = MemberResume(
            member_id=MEMBER_ID,
            title=title,
            raw_text=raw_text,
            created_at=datetime.now(timezone.utc),
        )
        db.add(resume)
        db.flush()

        for skill in skills:
            db.add(
                MemberSkill(
                    resume_id=resume.id,
                    skill_name=skill["skill_name"],
                    competency=skill["competency"],
                    evidence=skill["evidence"],
                    created_at=datetime.now(timezone.utc),
                )
            )
        db.commit()
        db.refresh(resume)
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"이력서 저장에 실패했습니다: {error}") from error

    return ResumeUploadResponse(
        id=resume.id,
        title=resume.title,
        skills=[MemberSkillResponse.model_validate(s) for s in resume.skills],
    )


@router.get("/{resume_id}/skills", response_model=list[MemberSkillResponse])
def get_resume_skills(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(MemberResume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")
    return list(resume.skills)


@router.post("/{resume_id}/match", response_model=list[MatchResult])
async def match_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(MemberResume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")

    try:
        matches = await compute_matches(db, resume_id, settings.openai_api_key)
        role_to_application_id = upsert_applications(db, resume_id, matches)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"매칭 계산에 실패했습니다: {error}") from error

    return [
        MatchResult(
            application_id=role_to_application_id.get(match["role_id"]),
            role_id=match["role_id"],
            role_name=match["role_name"],
            posting_id=match["posting_id"],
            company=match["company"],
            title=match["title"],
            deadline=match["deadline"],
            linkareer_url=match["linkareer_url"],
            apply_url=match["apply_url"],
            match_score=match["match_score"],
            reason=match["reason"],
        )
        for match in matches
    ]


@router.get("/{resume_id}/matches", response_model=list[MatchResult])
def read_stored_matches(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(MemberResume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")

    rows = get_stored_matches(db, resume_id)
    return [
        MatchResult(
            application_id=row["application_id"],
            role_id=row["role_id"],
            role_name=row["role_name"],
            posting_id=row["posting_id"],
            company=row["company"],
            title=row["title"],
            deadline=row["deadline"],
            linkareer_url=row["linkareer_url"],
            apply_url=row["apply_url"],
            match_score=row["match_score"] or 0,
            reason=row["match_reason"] or "",
        )
        for row in rows
    ]
