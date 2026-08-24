"""원문 → 세부직무·역량·문항 구조화 (OpenAI)."""

import json

from openai import AsyncOpenAI

_OCR_PROMPT = (
	"이 채용공고 이미지에서 텍스트를 그대로 추출해줘.\n"
	"모집분야, 지원자격, 우대사항, 전형절차 등 JD 내용만.\n"
	"링커리어 UI 요소(채팅, 스터디 등)는 제외."
)
_MAX_OCR_IMAGES = 6


async def ocr_job_posting_images(image_urls: list[str], api_key: str) -> str:
	"""이미지로만 된 공고에서 매칭용 텍스트를 뽑아낸다 (gpt-4o Vision)."""
	if not image_urls or not api_key:
		return ""

	client = AsyncOpenAI(api_key=api_key)
	content: list[dict] = [{"type": "text", "text": _OCR_PROMPT}]
	for url in image_urls[:_MAX_OCR_IMAGES]:
		content.append({"type": "image_url", "image_url": {"url": url}})

	try:
		response = await client.chat.completions.create(
			model="gpt-4o",
			messages=[{"role": "user", "content": content}],
		)
		return (response.choices[0].message.content or "").strip()
	except Exception:
		return ""


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
