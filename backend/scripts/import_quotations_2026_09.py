"""
Import the Sep 2026 Viziwall quotation list into the database.
Source: scripts/data/quotes_09_26.csv

Skips rows whose Customer ID has no matching customer (260040, 260049,
260050, 260051 as of this sheet) rather than creating placeholders —
those customers are being supplied separately.

Run from backend/: python scripts/import_quotations_2026_09.py
"""
import csv
import io
import re
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Customer, Quotation, QuoteStatus

CSV_PATH = Path(__file__).resolve().parent / "data" / "quotes_09_26.csv"

STATUS_MAP = {
    "Approved": QuoteStatus.approved,
    "Declined": QuoteStatus.declined,
    "Cancelled": QuoteStatus.cancelled,
    "Waiting": QuoteStatus.waiting,
    "New Version Sent": QuoteStatus.new_version_sent,
    "Follow up sent": QuoteStatus.follow_up_sent,
}

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Matches "February 22-26, 2026", "Jan 16 - 18, 2026", "13-17 April 2026", "September 8-12, 2026"
DATE_RANGE_RE = re.compile(
    r'(?:(?P<month1>[A-Za-z]+)\s+)?(?P<day1>\d{1,2})\s*[-–]\s*(?:(?P<month2>[A-Za-z]+)\s+)?(?P<day2>\d{1,2})(?:,)?\s*(?:(?P<month3>[A-Za-z]+)\s+)?(?P<year>\d{4})'
)
SINGLE_DATE_RE = re.compile(r'(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})')


def parse_event_dates(text):
    """Best-effort parse of free-text event date ranges. Returns (start, end) or (None, None)."""
    if not text:
        return None, None

    m = DATE_RANGE_RE.search(text)
    if m:
        month_name = (m.group("month1") or m.group("month2") or m.group("month3") or "").lower()
        month = MONTHS.get(month_name)
        year = int(m.group("year"))
        day1, day2 = int(m.group("day1")), int(m.group("day2"))
        if month:
            try:
                return date(year, month, day1), date(year, month, day2)
            except ValueError:
                pass

    m = SINGLE_DATE_RE.search(text)
    if m:
        month = MONTHS.get(m.group("month").lower())
        if month:
            try:
                d = date(int(m.group("year")), month, int(m.group("day")))
                return d, d
            except ValueError:
                pass

    return None, None


def parse_money(text):
    if not text:
        return None
    cleaned = text.replace("€", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def main():
    db = SessionLocal()
    created, skipped_missing_customer, skipped_duplicate = 0, [], []
    unmapped_status, unparsed_dates = [], []

    try:
        with CSV_PATH.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        customers_by_external_id = {
            c.external_id: c for c in db.query(Customer).filter(Customer.external_id.isnot(None)).all()
        }
        seen_quote_numbers = {qn for (qn,) in db.query(Quotation.quote_number).all()}

        for row in rows:
            quote_number = row["Quote Number"].strip()
            customer_ext_id = row["Customer ID"].strip()

            customer = customers_by_external_id.get(customer_ext_id)
            if not customer:
                skipped_missing_customer.append((quote_number, customer_ext_id))
                continue

            if quote_number in seen_quote_numbers:
                skipped_duplicate.append(quote_number)
                continue

            status_text = row["Status"].strip()
            status = STATUS_MAP.get(status_text)
            if not status:
                unmapped_status.append((quote_number, status_text))
                status = QuoteStatus.draft

            dates_text = row["Event Dates"].strip() or None
            start_date, end_date = parse_event_dates(dates_text)
            if dates_text and not start_date:
                unparsed_dates.append((quote_number, dates_text))

            db.add(Quotation(
                quote_number=quote_number,
                customer_id=customer.id,
                event_name=row["Event Name"].strip() or None,
                event_venue=row["Venue"].strip() or None,
                event_start_date=start_date,
                event_end_date=end_date,
                event_dates_text=dates_text,
                status=status,
                currency="EUR",
                tax_rate_percent=Decimal("0"),
                service_description=row["Service Description"].strip() or None,
                discount_amount=parse_money(row["Discount Amount"]),
                historical_total_amount=parse_money(row["Total Amount"]),
                quotation_date_text=row["Date of Quotation"].strip() or None,
            ))
            seen_quote_numbers.add(quote_number)
            created += 1

        db.commit()
        print(f"Done. Created {created} quotation(s).")

        if skipped_missing_customer:
            print(f"\nSkipped {len(skipped_missing_customer)} row(s) with no matching customer:")
            for qn, ext_id in skipped_missing_customer:
                print(f"  {qn}: customer {ext_id} not found")

        if skipped_duplicate:
            print(f"\nSkipped {len(skipped_duplicate)} duplicate quote number(s): {skipped_duplicate}")

        if unmapped_status:
            print(f"\nUnmapped status values (defaulted to draft): {unmapped_status}")

        if unparsed_dates:
            print(f"\nCould not parse a structured date for {len(unparsed_dates)} row(s) (kept as event_dates_text):")
            for qn, dt in unparsed_dates:
                print(f"  {qn}: {dt!r}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
