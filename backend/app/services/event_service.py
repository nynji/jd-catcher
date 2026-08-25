import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.event import EventLog
from app.schemas.event import EngagementUpdate, EventCreate

logger = logging.getLogger(__name__)

_ENGAGEMENT_UPDATE_SQL = text(
    """
    UPDATE event_log
    SET
      duration_ms = CASE
        WHEN :duration_ms IS NULL THEN duration_ms
        WHEN duration_ms IS NULL OR :duration_ms > duration_ms THEN :duration_ms
        ELSE duration_ms
      END,
      max_scroll_depth_pct = CASE
        WHEN :max_scroll_depth_pct IS NULL THEN max_scroll_depth_pct
        WHEN max_scroll_depth_pct IS NULL OR :max_scroll_depth_pct > max_scroll_depth_pct
          THEN :max_scroll_depth_pct
        ELSE max_scroll_depth_pct
      END
    WHERE id = :event_id
    """
)


def record_event(db: Session, payload: EventCreate, referrer: str | None, user_agent: str | None) -> int | None:
    """이벤트를 저장하고 생성된 id를 반환한다. 실패해도 예외를 밖으로 던지지 않는다."""
    try:
        event = EventLog(
            event_name=payload.event_name,
            anonymous_id=payload.anonymous_id,
            session_id=payload.session_id,
            posting_id=payload.posting_id,
            role_id=payload.role_id,
            resume_id=payload.resume_id,
            path=payload.path,
            properties=payload.properties,
            referrer=referrer,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event.id
    except Exception:
        db.rollback()
        logger.exception("이벤트 저장 실패: %s", payload.event_name)
        return None


def update_engagement(db: Session, event_id: int, payload: EngagementUpdate) -> None:
    """체류 시간/스크롤 깊이를 갱신한다. 기존 값보다 작으면 무시한다(단조 증가 보호)."""
    try:
        db.execute(
            _ENGAGEMENT_UPDATE_SQL,
            {
                "event_id": event_id,
                "duration_ms": payload.duration_ms,
                "max_scroll_depth_pct": payload.max_scroll_depth_pct,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("참여도 업데이트 실패: event_id=%s", event_id)
