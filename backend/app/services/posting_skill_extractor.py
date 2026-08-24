"""공고 세부직무(posting_role) → 요구 역량 구조화 (GPT-4o). posting_skill 백필용."""

import asyncio
import json

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.matching import PostingRole, PostingSkill
from app.models.posting import JobPosting

_PROMPT_TEMPLATE = """아래는 채용 공고의 세부 직무 정보다. 이 직무가 요구하는 역량을 추출해줘.
반드시 JSON으로만 응답하고 다른 텍스트는 쓰지 마.

각 항목:
{{
  "skill_name": "구체적 스킬명 (SQL, 코호트분석, GA4, Python 등, 이력서 역량명과 비교 가능한 형태)",
  "competency": "대분류 (데이터분석/마케팅/개발/기획/디자인 중 하나)",
  "importance": "required 또는 preferred"
}}

세부 직무명: {role_name}
공고 직무 카테고리: {job_type}
공고 산업: {industry}
공고 원문: {raw_text}

반드시 {{"skills": [...]}} 형태의 JSON 객체로 감싸서 응답하라. 근거가 부족하면 빈 배열을 반환하라.
"""


async def extract_posting_skills(
    role_name: str,
    job_type: str,
    industry: str,
    raw_text: str,
    api_key: str,
) -> list[dict]:
    if not api_key:
        return []

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "채용 공고에서 직무 요구 역량을 JSON으로 추출하는 어시스턴트입니다.",
                },
                {
                    "role": "user",
                    "content": _PROMPT_TEMPLATE.format(
                        role_name=role_name or "",
                        job_type=job_type or "",
                        industry=industry or "",
                        raw_text=(raw_text or "")[:8000],
                    ),
                },
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return []

    skills = data.get("skills", [])
    result = []
    for item in skills:
        skill_name = str(item.get("skill_name", "")).strip()
        if not skill_name:
            continue
        importance = str(item.get("importance", "")).strip().lower()
        if importance not in {"required", "preferred"}:
            importance = "required"
        result.append(
            {
                "skill_name": skill_name,
                "competency": str(item.get("competency", "")).strip(),
                "importance": importance,
            }
        )
    return result


async def backfill_posting_skills(db: Session, api_key: str) -> dict:
    """posting_skill이 비어있는 posting_role에 대해 역량을 추출해서 채운다."""
    statement = (
        select(PostingRole)
        .options(selectinload(PostingRole.skills), selectinload(PostingRole.posting))
        .where(~PostingRole.skills.any())
    )
    roles = list(db.scalars(statement).all())
    if not roles:
        return {"roles_processed": 0, "skills_created": 0}

    extracted = await asyncio.gather(
        *(
            extract_posting_skills(
                role_name=role.role_name or "",
                job_type=role.posting.job_type if role.posting else "",
                industry=role.posting.industry if role.posting else "",
                raw_text=role.posting.raw_text if role.posting else "",
                api_key=api_key,
            )
            for role in roles
        )
    )

    skills_created = 0
    for role, skills in zip(roles, extracted):
        for skill in skills:
            db.add(
                PostingSkill(
                    role_id=role.id,
                    skill_name=skill["skill_name"],
                    competency=skill["competency"],
                    importance=skill["importance"],
                )
            )
            skills_created += 1
    db.commit()

    return {"roles_processed": len(roles), "skills_created": skills_created}
