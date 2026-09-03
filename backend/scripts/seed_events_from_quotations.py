"""
One-off seed of the events picklist from distinct (event_name, event_venue)
pairs already present in imported quotations, plus each event's earliest
start/end date as its default. Run from backend/: python scripts/seed_events_from_quotations.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Event, Quotation


def main():
    db = SessionLocal()
    try:
        rows = (
            db.query(Quotation.event_name, Quotation.event_venue,
                     Quotation.event_start_date, Quotation.event_end_date)
            .filter(Quotation.event_name.isnot(None), Quotation.event_name != "")
            .all()
        )

        seen = {}
        for name, venue, start, end in rows:
            key = (name, venue)
            if key not in seen or (start and (seen[key][0] is None or start < seen[key][0])):
                seen[key] = (start, end)

        existing = {(e.name, e.venue) for e in db.query(Event.name, Event.venue).all()}

        created = 0
        for (name, venue), (start, end) in seen.items():
            if (name, venue) in existing:
                continue
            db.add(Event(name=name, venue=venue, default_start_date=start, default_end_date=end))
            created += 1

        db.commit()
        print(f"Done. Created {created} event(s), skipped {len(seen) - created} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
