from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.event import EngagementUpdate, EventCreate, EventCreateResponse
from app.services.event_service import record_event, update_engagement

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventCreateResponse, status_code=201)
def create_event(payload: EventCreate, request: Request, db: Session = Depends(get_db)):
    event_id = record_event(db, payload, request.headers.get("referer"), request.headers.get("user-agent"))
    return EventCreateResponse(id=event_id)


@router.post("/{event_id}/engagement", status_code=204)
def post_engagement(event_id: int, payload: EngagementUpdate, db: Session = Depends(get_db)):
    update_engagement(db, event_id, payload)
