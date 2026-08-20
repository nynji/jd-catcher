"""원문 → 세부직무·역량·문항 구조화 (OpenAI)."""

import json

from openai import AsyncOpenAI


async def extract_industry(raw_text: str, api_key: str) -> str:
	if not raw_text or not api_key:
		return ""

	client = AsyncOpenAI(api_key=api_key)
	try:
		response = await client.chat.completions.create(
			model="gpt-4o",
			response_format={"type": "json_object"},
			messages=[
				{
					"role": "system",
					"content": "공고 원문에서 기업의 산업 분야를 하나의 짧은 한국어 명사구로 추출한다.",
				},
				{
					"role": "user",
					"content": (
						'JSON 형식 {"industry": "..."}으로만 답하라. '
						f"공고 원문:\n{raw_text[:12000]}"
					),
				},
			],
		)
		data = json.loads(response.choices[0].message.content or "{}")
		return str(data.get("industry", "")).strip()
	except Exception:
		return ""
