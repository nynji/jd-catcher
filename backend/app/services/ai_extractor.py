"""이력서 원문 → 보유 역량 구조화 (GPT-4o)."""

import json

from openai import AsyncOpenAI

_PROMPT_TEMPLATE = """아래 이력서/포트폴리오 텍스트에서 보유 역량을 추출해줘.
반드시 JSON 배열로만 응답하고 다른 텍스트는 쓰지 마.

각 항목:
{{
  "skill_name": "구체적 스킬명 (SQL, 코호트분석, GA4, Python 등)",
  "competency": "대분류 (데이터분석/마케팅/개발/기획/디자인 중 하나)",
  "evidence": "이 스킬의 근거가 된 이력서 원문 스니펫 (1~2문장)"
}}

이력서:
{raw_text}
"""


async def extract_skills_from_resume(raw_text: str, api_key: str) -> list[dict]:
    if not raw_text or not api_key:
        return []

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "이력서에서 역량을 JSON으로 추출하는 어시스턴트입니다.",
                },
                {
                    "role": "user",
                    "content": (
                        _PROMPT_TEMPLATE.format(raw_text=raw_text[:12000])
                        + '\n\n반드시 {"skills": [...]} 형태의 JSON 객체로 감싸서 응답하라.'
                    ),
                },
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception as error:
        raise RuntimeError(f"역량 추출에 실패했습니다: {error}") from error

    skills = data.get("skills", data if isinstance(data, list) else [])
    result = []
    for item in skills:
        skill_name = str(item.get("skill_name", "")).strip()
        if not skill_name:
            continue
        result.append(
            {
                "skill_name": skill_name,
                "competency": str(item.get("competency", "")).strip(),
                "evidence": str(item.get("evidence", "")).strip() or None,
            }
        )
    return result
