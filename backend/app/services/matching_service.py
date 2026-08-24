"""이력서 x 공고 세부직무 매칭 점수 계산 (GPT-4o 기반 의미 추론).

기존에는 이력서 역량과 공고 요구역량의 문자열이 완전히 같아야만(LOWER 비교) 점수가
붙는 SQL 매칭이었는데, 표현이 조금만 달라도(예: "엑셀" vs "Excel") 전부 0점이 되는
문제가 있었다. 이제는 LLM이 의미적으로 비슷한 경험/역량까지 인정해서 점수를 매긴다.
"""

import asyncio
import json
from datetime import datetime, timezone

from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.models.matching import Application, PostingRole
from app.models.member import MemberResume, MemberSkill

MEMBER_ID = 1
_BATCH_SIZE = 20
_TOP_N = 30
_RESUME_CHAR_LIMIT = 4000
_JD_CHAR_LIMIT = 600

_SYSTEM_PROMPT = (
    "당신은 이력서와 채용 공고 세부 직무 간의 적합도를 평가하는 채용 컨설턴트입니다. "
    "직무명이나 스킬명의 글자가 완전히 똑같지 않아도, 의미적으로 비슷하거나 관련 있는 "
    "경험/역량이면 유사하다고 보고 점수를 매기세요 "
    "(예: '엑셀'과 'Excel', '데이터 분석 경험'과 'SQL 기반 분석'은 서로 관련 있다고 판단). "
    "근거 없이 점수를 후하게 주지는 마세요. 반드시 JSON으로만 답하세요."
)

_STORED_MATCH_SQL = text(
    """
    SELECT
      a.id AS application_id,
      a.role_id,
      pr.role_name,
      jp.id AS posting_id,
      jp.company,
      jp.title,
      jp.deadline,
      jp.linkareer_url,
      jp.apply_url,
      a.match_score,
      a.match_reason
    FROM application a
    JOIN posting_role pr ON pr.id = a.role_id
    JOIN job_posting jp ON jp.id = pr.posting_id
    WHERE a.resume_id = :resume_id AND a.member_id = :member_id
    ORDER BY a.match_score DESC NULLS LAST
    """
)


def _format_member_skills(skills: list[MemberSkill]) -> str:
    names = [f"{skill.skill_name}({skill.competency})" for skill in skills if skill.skill_name]
    return ", ".join(names) if names else "없음"


def _role_block(role: PostingRole) -> str:
    posting = role.posting
    skill_names = [skill.skill_name for skill in role.skills if skill.skill_name]
    lines = [
        f"[role_id={role.id}]",
        f"회사: {posting.company if posting else ''}",
        f"세부 직무: {(role.role_name or '').strip()}",
        f"직무 카테고리: {posting.job_type if posting else ''}",
        f"업종: {posting.industry if posting else ''}",
    ]
    if skill_names:
        lines.append(f"요구 역량(참고): {', '.join(skill_names)}")
    if posting and posting.raw_text:
        lines.append(f"공고 원문 일부: {posting.raw_text[:_JD_CHAR_LIMIT]}")
    return "\n".join(lines)


async def _score_batch(
    client: AsyncOpenAI, resume_text: str, member_skills_text: str, roles: list[PostingRole]
) -> dict[int, dict]:
    role_blocks = "\n\n".join(_role_block(role) for role in roles)
    user_content = (
        f"지원자 이력서:\n{resume_text[:_RESUME_CHAR_LIMIT]}\n\n"
        f"지원자 보유 역량: {member_skills_text}\n\n"
        f"평가할 공고 직무 목록:\n{role_blocks}\n\n"
        '각 직무에 대해 JSON 형식 {"matches": [{"role_id": 정수, "match_score": 0~100 사이 정수, '
        '"reason": "왜 이 점수인지 1문장 한국어 설명"}]}로만 답하라. '
        "모든 role_id를 빠짐없이 포함하라."
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return {}

    result: dict[int, dict] = {}
    for item in data.get("matches", []):
        try:
            role_id = int(item["role_id"])
            score = max(0, min(100, int(item["match_score"])))
        except (KeyError, TypeError, ValueError):
            continue
        result[role_id] = {
            "match_score": score,
            "reason": str(item.get("reason", "")).strip(),
        }
    return result


async def compute_matches(db: Session, resume_id: int, api_key: str) -> list[dict]:
    resume = db.get(MemberResume, resume_id)
    if resume is None:
        raise ValueError("이력서를 찾을 수 없습니다.")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in backend/.env")

    statement = select(PostingRole).options(
        selectinload(PostingRole.posting), selectinload(PostingRole.skills)
    )
    roles = list(db.scalars(statement).all())
    roles = [role for role in roles if role.posting is not None]
    if not roles:
        return []

    member_skills_text = _format_member_skills(resume.skills)
    client = AsyncOpenAI(api_key=api_key)
    batches = [roles[i : i + _BATCH_SIZE] for i in range(0, len(roles), _BATCH_SIZE)]
    batch_results = await asyncio.gather(
        *(
            _score_batch(client, resume.raw_text or "", member_skills_text, batch)
            for batch in batches
        )
    )

    scores: dict[int, dict] = {}
    for batch_result in batch_results:
        scores.update(batch_result)

    matches = []
    for role in roles:
        info = scores.get(role.id)
        if info is None:
            continue
        posting = role.posting
        matches.append(
            {
                "role_id": role.id,
                "role_name": role.role_name,
                "posting_id": posting.id,
                "company": posting.company,
                "title": posting.title,
                "deadline": posting.deadline,
                "linkareer_url": posting.linkareer_url,
                "apply_url": posting.apply_url,
                "match_score": info["match_score"],
                "reason": info["reason"],
            }
        )
    matches.sort(key=lambda match: match["match_score"], reverse=True)
    return matches[:_TOP_N]


def upsert_applications(db: Session, resume_id: int, matches: list[dict]) -> dict[int, int]:
    """role_id -> application_id 매핑을 반환한다."""
    role_to_application_id: dict[int, int] = {}
    for match in matches:
        existing = (
            db.query(Application)
            .filter(
                Application.member_id == MEMBER_ID,
                Application.role_id == match["role_id"],
                Application.resume_id == resume_id,
            )
            .first()
        )
        if existing:
            existing.match_score = match["match_score"]
            existing.match_reason = match["reason"]
            application = existing
        else:
            application = Application(
                member_id=MEMBER_ID,
                role_id=match["role_id"],
                resume_id=resume_id,
                status="관심",
                match_score=match["match_score"],
                match_reason=match["reason"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(application)
            db.flush()
        role_to_application_id[match["role_id"]] = application.id
    db.commit()
    return role_to_application_id


def get_stored_matches(db: Session, resume_id: int) -> list[dict]:
    rows = db.execute(
        _STORED_MATCH_SQL, {"resume_id": resume_id, "member_id": MEMBER_ID}
    ).mappings().all()
    return [dict(row) for row in rows]
