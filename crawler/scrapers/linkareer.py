"""링커리어 인턴 공고 크롤러."""

from dataclasses import dataclass, field
from datetime import date
import re
from urllib.parse import urljoin

from playwright.async_api import Page

from ai_parser import extract_industry


@dataclass
class Posting:
	source_url: str
	company: str
	job_type: str
	industry: str
	deadline: date | None
	apply_url: str
	is_image_based: bool
	raw_text: str
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


async def crawl(
	page: Page,
	url: str,
	max_pages: int = 5,
	openai_api_key: str = "",
) -> list[Posting]:
	"""목록에서 상세 페이지를 찾아 공고 원문을 수집한다."""
	postings: list[Posting] = []
	seen_urls: set[str] = set()
	current_url = url

	for _ in range(max_pages):
		await page.goto(current_url, wait_until="domcontentloaded", timeout=60_000)
		await page.wait_for_timeout(1_500)
		detail_urls = await _links(page)

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
				deadline_text = await _label_value(detail, ["마감일", "접수기간"])
				raw_text = await _text(
					detail,
					["main", "article", "[class*='content']", "[class*='description']"],
				)
				if not industry:
					industry = await extract_industry(raw_text, openai_api_key)
				if raw_text:
					postings.append(
						Posting(
							source_url=detail_url,
							company=company,
							job_type=job_type,
							industry=industry,
							deadline=_parse_date(deadline_text),
							apply_url=await _apply_url(detail),
							is_image_based=await detail.locator("main img, article img").count() > 0,
							raw_text=raw_text,
							submission_requirements=await _submission_requirements(detail),
							questions=await _questions(detail),
						)
					)
			finally:
				await detail.close()

		next_button = page.locator("button.button-arrow-next").last
		if await next_button.count():
			if await next_button.is_disabled():
				break
			await next_button.click()
			await page.wait_for_timeout(1_500)
			continue

		next_link = page.locator("a[aria-label*='다음'], a:has-text('다음')").last
		if not await next_link.count():
			break
		next_href = await next_link.get_attribute("href")
		if not next_href:
			break
		current_url = urljoin(page.url, next_href)

	return postings
