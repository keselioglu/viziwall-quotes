from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Event
from app.schemas.schemas import EventCreate, EventOut, EventUpdate

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.name).all()


@router.post("", response_model=EventOut, status_code=201)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)):
    event = Event(**event_in.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: str, event_in: EventUpdate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in event_in.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event
