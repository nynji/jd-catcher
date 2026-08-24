"""이력서 x 공고 직무 심층 매칭 분석 (GPT-4o)."""

import json

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.matching import PostingRole, PostingSkill
from app.models.member import MemberResume, MemberSkill

_PROMPT_TEMPLATE = """당신은 채용 매칭 분석 전문가입니다.
지원자의 이력서와 채용공고 JD를 비교 분석해주세요.

## 지원자 정보
[이력서 원문]
{resume_text}

[추출된 역량]
{member_skills}

## 채용공고 정보
[기업/직무]
{company} - {role_name}

[공고 원문 JD]
{jd_text}

[추출된 요구역량]
{posting_skills}

## 분석 요구사항

아래 JSON 형식으로만 응답하세요. 다른 텍스트는 쓰지 마세요.

{{
  "match_score": 0~100 사이 정수,
  "score_reason": "매칭률 산정 근거 1~2문장",
  "matched_points": [
    {{
      "applicant_capability": "지원자가 보유한 구체적 역량/경험",
      "jd_requirement": "이에 대응하는 JD의 요구사항",
      "explanation": "두 항목이 왜 매칭되는지 구체적 설명 (2~3문장). 지원자의 실제 경험을 인용할 것",
      "strength": "high | medium | low"
    }}
  ],
  "gap_points": [
    {{
      "jd_requirement": "JD가 요구하지만 지원자에게 부족한 역량",
      "current_state": "지원자의 현재 관련 수준 (전혀 없음/유사 경험 있음 등)",
      "suggestion": "보완 방법 또는 대체 어필 포인트 (1~2문장)"
    }}
  ],
  "summary": "전체 매칭 평가 3~4문장. 지원 추천 여부와 이유 포함",
  "recommended_emphasis": [
    "자소서/면접에서 강조하면 좋을 포인트 3개"
  ]
}}

## 분석 지침

1. matched_points는 최소 2개, 최대 5개
   - 단순히 "SQL 있음/필요함" 수준이 아니라
   - "코호트 분석 프로젝트에서 SQL로 사용자 리텐션을 계산한 경험"처럼
     구체적 경험을 근거로 들 것
   - JD 원문의 실제 문구를 인용해서 대응 관계를 명확히 할 것

2. gap_points는 최대 3개
   - 치명적인 격차부터 우선 서술
   - 단순 나열이 아니라 "어떻게 보완할지"까지 제시

3. match_score 산정 기준
   - 필수 요건 충족도 (60%)
   - 우대 사항 충족도 (20%)
   - 경험의 직무 연관성 (20%)
   - 직무 타이틀이 달라도 실제 요구 역량이 맞으면 높게 평가할 것
     (예: "마케터" 공고여도 데이터 분석 역량을 요구하면
      데이터 분석가 지원자에게 높은 점수)

4. 과장하지 말 것
   - 지원자에게 없는 역량을 있는 것처럼 쓰지 말 것
   - 매칭률을 억지로 높이지 말 것
   - 낮으면 낮다고 정직하게 평가

5. 모든 설명은 한국어로 작성
"""

_UPSERT_SQL = text(
    """
    INSERT INTO match_analysis
      (resume_id, role_id, ai_match_score, score_reason, matched_points,
       gap_points, summary, recommended_emphasis, created_at)
    VALUES
      (:resume_id, :role_id, :ai_match_score, :score_reason, :matched_points,
       :gap_points, :summary, :recommended_emphasis, now())
    ON CONFLICT (resume_id, role_id) DO UPDATE SET
      ai_match_score = EXCLUDED.ai_match_score,
      score_reason = EXCLUDED.score_reason,
      matched_points = EXCLUDED.matched_points,
      gap_points = EXCLUDED.gap_points,
      summary = EXCLUDED.summary,
      recommended_emphasis = EXCLUDED.recommended_emphasis,
      created_at = now()
    RETURNING resume_id, role_id, ai_match_score, score_reason, matched_points,
      gap_points, summary, recommended_emphasis
    """
)

_SELECT_SQL = text(
    """
    SELECT resume_id, role_id, ai_match_score, score_reason, matched_points,
      gap_points, summary, recommended_emphasis
    FROM match_analysis
    WHERE resume_id = :resume_id AND role_id = :role_id
    """
)


def get_cached_analysis(db: Session, resume_id: int, role_id: int) -> dict | None:
    row = db.execute(_SELECT_SQL, {"resume_id": resume_id, "role_id": role_id}).mappings().first()
    return dict(row) if row else None


def _format_member_skills(skills: list[MemberSkill]) -> str:
    if not skills:
        return "없음"
    return "\n".join(
        f"- {skill.skill_name} ({skill.competency}): {skill.evidence or ''}" for skill in skills
    )


def _format_posting_skills(skills: list[PostingSkill]) -> str:
    if not skills:
        return "없음"
    return "\n".join(
        f"- {skill.skill_name} ({skill.competency}, {skill.importance})" for skill in skills
    )


async def analyze_match(db: Session, resume_id: int, role_id: int, api_key: str) -> dict:
    resume = db.get(MemberResume, resume_id)
    if resume is None:
        raise ValueError("이력서를 찾을 수 없습니다.")

    role = db.get(PostingRole, role_id)
    if role is None:
        raise ValueError("공고 직무를 찾을 수 없습니다.")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in backend/.env")

    posting = role.posting
    prompt = _PROMPT_TEMPLATE.format(
        resume_text=(resume.raw_text or "")[:8000],
        member_skills=_format_member_skills(resume.skills),
        company=posting.company if posting else "",
        role_name=role.role_name or "",
        jd_text=(posting.raw_text or "")[:6000] if posting else "",
        posting_skills=_format_posting_skills(role.skills),
    )

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception as error:
        raise RuntimeError(f"매칭 분석에 실패했습니다: {error}") from error

    score = data.get("match_score")
    score = max(0, min(100, int(score))) if score is not None else None

    params = {
        "resume_id": resume_id,
        "role_id": role_id,
        "ai_match_score": score,
        "score_reason": str(data.get("score_reason", "")).strip() or None,
        "matched_points": json.dumps(data.get("matched_points", []), ensure_ascii=False),
        "gap_points": json.dumps(data.get("gap_points", []), ensure_ascii=False),
        "summary": str(data.get("summary", "")).strip() or None,
        "recommended_emphasis": json.dumps(data.get("recommended_emphasis", []), ensure_ascii=False),
    }
    row = db.execute(_UPSERT_SQL, params).mappings().first()
    db.commit()
    return dict(row)
