"""크롤링 파이프라인 진입점 (GitHub Actions에서 실행)."""

import asyncio

from playwright.async_api import async_playwright

from config import (
    CRAWL_MAX_PAGES,
    LINKAREER_URLS,
    OPENAI_API_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)
from db import save_postings
from scrapers.linkareer import Posting, crawl


async def main() -> None:
    postings: list[Posting] = []
    seen_urls: set[str] = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(locale="ko-KR")
        page = await context.new_page()
        try:
            for url in LINKAREER_URLS:
                for posting in await crawl(page, url, CRAWL_MAX_PAGES, OPENAI_API_KEY):
                    if posting.source_url in seen_urls:
                        continue
                    seen_urls.add(posting.source_url)
                    postings.append(posting)
        finally:
            await context.close()
            await browser.close()

    inserted = save_postings(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, postings)
    print(f"수집 {len(postings)}건, 신규 저장 {inserted}건")

if __name__ == "__main__":
    asyncio.run(main())
