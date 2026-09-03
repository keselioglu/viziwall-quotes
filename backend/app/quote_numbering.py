from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Quotation

STARTING_NUMBER = 9017


def generate_quote_number(db: Session) -> str:
    """Format: VZW-YYYY-0001, sequential per year, starting from STARTING_NUMBER."""
    year = datetime.utcnow().year
    prefix = f"VZW-{year}-"
    count = (
        db.query(func.count(Quotation.id))
        .filter(Quotation.quote_number.like(f"{prefix}%"))
        .scalar()
    ) or 0
    next_number = max(count + 1, STARTING_NUMBER)
    return f"{prefix}{next_number:04d}"
