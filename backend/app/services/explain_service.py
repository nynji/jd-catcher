"""매칭 이유 자연어 설명 생성 (GPT-4o)."""

from openai import AsyncOpenAI

_PROMPT_TEMPLATE = """지원자의 역량과 공고 요구사항을 비교해서
왜 매칭됐는지 2~3문장으로 설명해줘. 한국어로.

지원자 역량: {member_skills}
공고 직무: {role_name}
공고 요구역량: {posting_skills}
매칭 점수: {match_score}%
"""


async def explain_match(
    member_skills: list[str],
    role_name: str,
    posting_skills: list[str],
    match_score: int,
    api_key: str,
) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in backend/.env")

    client = AsyncOpenAI(api_key=api_key)
    prompt = _PROMPT_TEMPLATE.format(
        member_skills=", ".join(member_skills) or "없음",
        role_name=role_name or "미상",
        posting_skills=", ".join(posting_skills) or "없음",
        match_score=match_score,
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as error:
        raise RuntimeError(f"매칭 이유 생성에 실패했습니다: {error}") from error
