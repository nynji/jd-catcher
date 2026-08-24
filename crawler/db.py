"""Supabase 저장소와 공고 하위 데이터 저장."""

from collections.abc import Iterable
from datetime import date, datetime, timezone
import re

from supabase import Client, create_client

from scrapers.linkareer import Posting


TABLE_NAME = "job_posting"


def _parse_deadline(value: date | str | None) -> str | None:
	"""링커리어의 날짜 문자열을 Supabase DATE 입력값으로 변환한다."""
	if not value:
		return None
	if isinstance(value, date):
		return value.isoformat()

	match = re.search(r"(20\d{2})[.\-/년\s]+(\d{1,2})[.\-/월\s]+(\d{1,2})", value)
	if not match:
		return None

	try:
		return date(
			int(match.group(1)),
			int(match.group(2)),
			int(match.group(3)),
		).isoformat()
	except ValueError:
		return None


def get_client(supabase_url: str, service_role_key: str) -> Client:
	if not supabase_url or not service_role_key:
		raise ValueError(
			"SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 환경변수가 필요합니다."
		)
	return create_client(supabase_url, service_role_key)


def _save_roles(client: Client, posting_id: int, questions: list[dict]) -> dict[str, int]:
	"""공고의 직무를 posting_role에 만들고 role_name별 실제 ID를 반환한다."""
	role_names = list(dict.fromkeys(
		item["role_name"].strip()
		for item in questions
		if item.get("role_name", "").strip()
	))
	if not role_names:
		return {}

	existing = (
		client.table("posting_role")
		.select("id, role_name")
		.eq("posting_id", posting_id)
		.execute()
		.data
		or []
	)
	role_ids = {
		row["role_name"]: row["id"]
		for row in existing
		if row.get("role_name")
	}
	empty_role = next((row for row in existing if not row.get("role_name")), None)

	for role_name in role_names:
		if role_name in role_ids:
			continue
		if empty_role:
			updated = (
				client.table("posting_role")
				.update({"role_name": role_name})
				.eq("id", empty_role["id"])
				.execute()
				.data
				or []
			)
			role_id = updated[0]["id"] if updated else empty_role["id"]
			empty_role = None
		else:
			created = (
				client.table("posting_role")
				.insert({"posting_id": posting_id, "role_name": role_name})
				.execute()
				.data
				or []
			)
			if not created:
				continue
			role_id = created[0]["id"]
		role_ids[role_name] = role_id
	return role_ids


def save_postings(
	supabase_url: str,
	service_role_key: str,
	postings: Iterable[Posting],
) -> int:
	client = get_client(supabase_url, service_role_key)
	postings = list(postings)
	rows = [
		{
			"linkareer_url": posting.source_url,
			"company": posting.company,
			"title": posting.title or None,
			"job_type": posting.job_type,
			"industry": posting.industry,
			"location": posting.location or None,
			"apply_url": posting.apply_url or None,
			"is_image_based": posting.is_image_based,
			"raw_text": posting.raw_text,
			"image_urls": posting.image_urls,
			"deadline": _parse_deadline(posting.deadline),
			"collected_at": datetime.now(timezone.utc).isoformat(),
		}
		for posting in postings
	]
	if not rows:
		return 0

	# linkareer_url에 UNIQUE 제약이 있어야 기존 공고를 건너뛸 수 있다.
	response = client.table(TABLE_NAME).upsert(
		rows, on_conflict="linkareer_url", ignore_duplicates=True
	).execute()
	posting_rows = (
		client.table(TABLE_NAME)
		.select("id, linkareer_url")
		.in_("linkareer_url", [posting.source_url for posting in postings])
		.execute()
		.data
		or []
	)
	posting_ids = {row["linkareer_url"]: row["id"] for row in posting_rows}
	for posting in postings:
		posting_id = posting_ids.get(posting.source_url)
		if posting_id is None:
			continue
		client.table("submission_requirement").delete().eq("posting_id", posting_id).execute()
		client.table("cover_letter_question").delete().eq("posting_id", posting_id).execute()
		role_ids = _save_roles(client, posting_id, posting.questions)
		requirements = [
			{
				"posting_id": posting_id,
				"type": item["type"],
				"is_required": item["is_required"],
				"detail": item.get("detail"),
			}
			for item in posting.submission_requirements
		]
		if requirements:
			client.table("submission_requirement").insert(requirements).execute()
		questions = [
			{
				"posting_id": posting_id,
				"role_id": role_ids.get(item["role_name"]),
				"role_name": item["role_name"],
				"question_text": item["question_text"],
				"char_limit": item.get("char_limit"),
				"question_order": item["question_order"],
			}
			for item in posting.questions
			if role_ids.get(item["role_name"]) is not None
		]
		if questions:
			client.table("cover_letter_question").insert(questions).execute()
	return len(response.data or [])
