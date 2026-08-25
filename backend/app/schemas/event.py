from pydantic import BaseModel


class EventCreate(BaseModel):
    event_name: str
    anonymous_id: str
    session_id: str
    path: str | None = None
    properties: dict = {}
    posting_id: int | None = None
    role_id: int | None = None
    resume_id: int | None = None


class EventCreateResponse(BaseModel):
    id: int | None


class EngagementUpdate(BaseModel):
    duration_ms: int | None = None
    max_scroll_depth_pct: int | None = None
