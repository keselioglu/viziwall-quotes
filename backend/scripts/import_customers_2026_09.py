"""
Import the Sep 2026 Viziwall customer list into the database.
Source: scripts/data/customers-09_26.csv
Run from backend/: python scripts/import_customers_2026_09.py
"""
import csv
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Customer

CSV_PATH = Path(__file__).resolve().parent / "data" / "customers-09_26.csv"


def main():
    db = SessionLocal()
    created, skipped = 0, 0
    try:
        with CSV_PATH.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        seen_external_ids = {
            row[0] for row in db.query(Customer.external_id).filter(Customer.external_id.isnot(None)).all()
        }

        for row in rows:
            external_id = row["Customer ID"].strip()
            if external_id in seen_external_ids:
                print(f"SKIP (external_id already exists): {external_id} {row['Company Name']}")
                skipped += 1
                continue

            db.add(Customer(
                external_id=external_id,
                company_name=row["Company Name"].strip() or None,
                contact_name=row["Contact Name"].strip() or None,
                email=row["E-mail"].strip() or None,
                phone=row["Phone"].strip() or None,
                address=row["Address"].strip() or None,
            ))
            seen_external_ids.add(external_id)
            created += 1

        db.commit()
        print(f"\nDone. Created {created} customer(s), skipped {skipped} duplicate(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
