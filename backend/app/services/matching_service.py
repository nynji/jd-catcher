from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.matching import Application

MEMBER_ID = 1

_COMPUTE_MATCH_SQL = text(
    """
    SELECT
      pr.id AS role_id,
      pr.role_name,
      jp.id AS posting_id,
      jp.company,
      jp.title,
      jp.deadline,
      jp.linkareer_url,
      jp.apply_url,
      COUNT(ps.skill_name) AS total_required,
      COUNT(ms.skill_name) AS matched,
      ROUND(COUNT(ms.skill_name) * 100.0 /
        NULLIF(COUNT(ps.skill_name), 0)) AS match_score
    FROM posting_role pr
    JOIN job_posting jp ON jp.id = pr.posting_id
    JOIN posting_skill ps ON ps.role_id = pr.id
    LEFT JOIN member_skill ms
      ON LOWER(ms.skill_name) = LOWER(ps.skill_name)
      AND ms.resume_id = :resume_id
    GROUP BY pr.id, pr.role_name, jp.id, jp.company, jp.title, jp.deadline,
      jp.linkareer_url, jp.apply_url
    ORDER BY match_score DESC
    LIMIT 20
    """
)

_STORED_MATCH_SQL = text(
    """
    SELECT
      a.id AS application_id,
      a.role_id,
      pr.role_name,
      jp.id AS posting_id,
      jp.company,
      jp.title,
      jp.deadline,
      jp.linkareer_url,
      jp.apply_url,
      a.match_score
    FROM application a
    JOIN posting_role pr ON pr.id = a.role_id
    JOIN job_posting jp ON jp.id = pr.posting_id
    WHERE a.resume_id = :resume_id AND a.member_id = :member_id
    ORDER BY a.match_score DESC NULLS LAST
    """
)


def compute_matches(db: Session, resume_id: int) -> list[dict]:
    rows = db.execute(_COMPUTE_MATCH_SQL, {"resume_id": resume_id}).mappings().all()
    return [dict(row) for row in rows]


def upsert_applications(db: Session, resume_id: int, matches: list[dict]) -> dict[int, int]:
    """role_id -> application_id 매핑을 반환한다."""
    role_to_application_id: dict[int, int] = {}
    for match in matches:
        existing = (
            db.query(Application)
            .filter(
                Application.member_id == MEMBER_ID,
                Application.role_id == match["role_id"],
                Application.resume_id == resume_id,
            )
            .first()
        )
        score = int(match["match_score"]) if match["match_score"] is not None else 0
        if existing:
            existing.match_score = score
            application = existing
        else:
            application = Application(
                member_id=MEMBER_ID,
                role_id=match["role_id"],
                resume_id=resume_id,
                status="관심",
                match_score=score,
                created_at=datetime.now(timezone.utc),
            )
            db.add(application)
            db.flush()
        role_to_application_id[match["role_id"]] = application.id
    db.commit()
    return role_to_application_id


def get_stored_matches(db: Session, resume_id: int) -> list[dict]:
    rows = db.execute(
        _STORED_MATCH_SQL, {"resume_id": resume_id, "member_id": MEMBER_ID}
    ).mappings().all()
    return [dict(row) for row in rows]
