"""링커리어 인턴 공고 크롤러."""

from dataclasses import dataclass, field
from datetime import date
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from playwright.async_api import Page

from ai_parser import extract_industry, ocr_job_posting_images

_IMAGE_DOMAIN = "media-cdn.linkareer.com"
_OCR_TEXT_THRESHOLD = 200


@dataclass
class Posting:
	source_url: str
	company: str
	title: str
	job_type: str
	industry: str
	location: str
	deadline: date | None
	apply_url: str
	is_image_based: bool
	raw_text: str
	image_urls: list[str] = field(default_factory=list)
	submission_requirements: list[dict] = field(default_factory=list)
	questions: list[dict] = field(default_factory=list)


async def _text(page: Page, selectors: list[str]) -> str:
	for selector in selectors:
		locator = page.locator(selector).first
		if await locator.count():
			value = (await locator.inner_text()).strip()
			if value:
				return value
	return ""


async def _label_value(page: Page, labels: list[str]) -> str:
	for label in labels:
		matches = page.get_by_text(label, exact=True)
		for index in range(await matches.count()):
			label_node = matches.nth(index)
			parent = label_node.locator("xpath=..").first
			lines = [
				line.strip()
				for line in (await parent.inner_text()).splitlines()
				if line.strip() and line.strip() != label
			]
			if lines:
				return lines[-1]
	return ""


def _parse_date(value: str) -> date | None:
	if not value or "상시" in value:
		return None
	match = re.search(r"(20\d{2})[.\-/년\s]+(\d{1,2})[.\-/월\s]+(\d{1,2})", value)
	if not match:
		return None
	try:
		return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
	except ValueError:
		return None


async def _company(page: Page) -> str:
	selectors = [
		"h2",
		"[class*='company']",
		"[class*='organizer']",
	]
	blocked = {"기업정보 더보기", "기업정보", "더보기"}
	for selector in selectors:
		for locator in await page.locator(selector).all():
			value = (await locator.inner_text()).strip()
			if value and value not in blocked and not any(item in value for item in blocked):
				return value.splitlines()[0].strip()
	return ""


def _is_deadline_badge(line: str) -> bool:
	return bool(re.fullmatch(r"D-\d+", line)) or "마감" in line or "상시" in line


def _title_from_raw_text(raw_text: str) -> str:
	"""첫 줄은 D-day 배지(D-6, 오늘마감, 상시모집 등)이고 그 다음 줄이 공고 제목이다."""
	lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
	if not lines:
		return ""
	if _is_deadline_badge(lines[0]) and len(lines) > 1:
		return lines[1]
	return lines[0]


async def _title(page: Page, raw_text: str) -> str:
	page_title = (await page.title()).strip()
	page_title = re.sub(r"\s*[|\-–]\s*(공모전 대외활동|링커리어).*$", "", page_title).strip()
	if page_title:
		return page_title
	return _title_from_raw_text(raw_text)


_DETAIL_CONTENT_SELECTORS = [
	".ActivityDetailTabContent__StyledWrapper-sc-5c325a81-0.fcnVga .responsive-element",
	".ActivityDetailTabContent__StyledWrapper-sc-5c325a81-0.fcnVga",
	"article#DETAIL .responsive-element",
]


async def _detail_content(detail: Page) -> tuple[str, list[str]]:
	"""'상세내용' 탭 영역만 잡는다. 채팅방/스터디모집/합격후기/추천공고는 형제 섹션이라 자동 제외된다."""
	container = None
	for selector in _DETAIL_CONTENT_SELECTORS:
		candidate = detail.locator(selector).first
		if await candidate.count():
			container = candidate
			break
	if container is None:
		heading = detail.locator("h2").filter(has_text=re.compile(r"^상세내용$"))
		if await heading.count():
			candidate = heading.first.locator("xpath=following-sibling::*[1]")
			if await candidate.count():
				container = candidate
	if container is None:
		return "", []

	text = (await container.inner_text()).strip()
	image_urls: list[str] = []
	for img in await container.locator("img").all():
		src = await img.get_attribute("src")
		if src and _IMAGE_DOMAIN in src and src not in image_urls:
			image_urls.append(src)
	return text, image_urls


async def _apply_url(detail: Page) -> str:
	button = detail.locator(".apply-button").first
	if not await button.count():
		return ""
	original_url = detail.url
	try:
		await button.click(timeout=10_000)
		await detail.wait_for_timeout(1_500)
	except Exception:
		return ""

	for opened_page in detail.context.pages:
		if opened_page != detail and opened_page.url not in {"", "about:blank"}:
			return opened_page.url
	return detail.url if detail.url != original_url else ""


async def _questions(detail: Page) -> list[dict]:
	questions: list[dict] = []
	items = detail.locator("ul.duty-list li[class*='ActivityDutyItem__StyledWrapper']")
	for duty_index in range(await items.count()):
		duty = items.nth(duty_index)
		header = await _text(duty, ["header", "h3", "h4"])
		question_items = duty.locator("div.question-list li.item")
		for question_index in range(await question_items.count()):
			text = (await question_items.nth(question_index).inner_text()).strip()
			if text:
				limit_match = re.search(r"(\d[\d,]*)\s*자", text)
				questions.append(
					{
						"role_id": duty_index + 1,
						"role_name": header,
						"question_text": text,
						"char_limit": int(limit_match.group(1).replace(",", "")) if limit_match else None,
						"question_order": len(questions) + 1,
					}
				)
	return questions


async def _submission_requirements(detail: Page) -> list[dict]:
	text = (await detail.locator("body").inner_text()).strip()
	requirements: list[dict] = []
	for requirement_type in ("자소서", "이력서", "포트폴리오"):
		if requirement_type in text:
			requirements.append(
				{"type": requirement_type, "is_required": True, "detail": None}
			)
	return requirements


async def _links(page: Page) -> list[str]:
	links: list[str] = []
	for locator in await page.locator("a[href]").all():
		href = await locator.get_attribute("href")
		if href and ("/activity/" in href or "/activities/" in href):
			absolute = urljoin(page.url, href).split("#", 1)[0]
			if absolute not in links:
				links.append(absolute)
	return links


def _with_page_number(url: str, page_number: int) -> str:
	"""목록 URL의 page 쿼리파라미터를 지정한 값으로 바꾼다."""
	parts = urlsplit(url)
	query = dict(parse_qsl(parts.query))
	query["page"] = str(page_number)
	return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def crawl(
	page: Page,
	url: str,
	max_pages: int = 5,
	openai_api_key: str = "",
) -> list[Posting]:
	"""목록에서 상세 페이지를 찾아 공고 원문을 수집한다. page=N 쿼리파라미터로 직접 페이지를 이동한다."""
	postings: list[Posting] = []
	seen_urls: set[str] = set()

	for page_number in range(1, max_pages + 1):
		await page.goto(_with_page_number(url, page_number), wait_until="domcontentloaded", timeout=60_000)
		await page.wait_for_timeout(1_500)
		detail_urls = await _links(page)
		if not detail_urls:
			break

		for detail_url in detail_urls:
			if detail_url in seen_urls:
				continue
			seen_urls.add(detail_url)
			detail = await page.context.new_page()
			try:
				await detail.goto(detail_url, wait_until="domcontentloaded", timeout=60_000)
				await detail.wait_for_timeout(800)
				company = await _company(detail)
				job_type = await _label_value(detail, ["모집직무", "직무"])
				industry = await _label_value(detail, ["상세업종", "업종"])
				location = await _label_value(detail, ["근무지역", "근무 지역", "지역"])
				deadline_text = await _label_value(detail, ["마감일", "접수기간"])
				raw_text, image_urls = await _detail_content(detail)
				is_image_based = len(raw_text) < _OCR_TEXT_THRESHOLD or bool(image_urls)

				if is_image_based and len(raw_text) < _OCR_TEXT_THRESHOLD and image_urls:
					ocr_text = await ocr_job_posting_images(image_urls, openai_api_key)
					if ocr_text:
						raw_text = ocr_text

				if not industry:
					industry = await extract_industry(raw_text, openai_api_key)

				postings.append(
					Posting(
						source_url=detail_url,
						company=company,
						title=await _title(detail, raw_text),
						job_type=job_type,
						industry=industry,
						location=location,
						deadline=_parse_date(deadline_text),
						apply_url=await _apply_url(detail),
						is_image_based=is_image_based,
						raw_text=raw_text,
						image_urls=image_urls,
						submission_requirements=await _submission_requirements(detail),
						questions=await _questions(detail),
					)
				)
			finally:
				await detail.close()

	return postings
