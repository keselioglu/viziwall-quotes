from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Quotation


def generate_quote_number(db: Session) -> str:
    """Format: VZW-YYYY-0001, sequential per year."""
    year = datetime.utcnow().year
    prefix = f"VZW-{year}-"
    count = (
        db.query(func.count(Quotation.id))
        .filter(Quotation.quote_number.like(f"{prefix}%"))
        .scalar()
    ) or 0
    return f"{prefix}{count + 1:04d}"
