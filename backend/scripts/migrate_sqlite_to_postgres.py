"""
One-off migration: copies business data (customers, products, events, quotations,
quote_line_items) from the local dev.db SQLite database into a production Postgres
database, via a Railway CLI tunnel (`railway connect Postgres --tunnel-only`).

Deliberately does NOT migrate the `users` table — those are local dev credentials,
and production already has a real user created via /api/auth/register. Migrated
quotations get created_by_id = NULL rather than pointing at a user that doesn't
exist in production.

Usage:
    python migrate_sqlite_to_postgres.py postgresql://user:pass@127.0.0.1:PORT/railway

Safe to re-run: uses `ON CONFLICT (id) DO NOTHING`, so already-migrated rows are
skipped rather than duplicated or overwritten.
"""

import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg2

DEV_DB = Path(__file__).resolve().parent.parent / "dev.db"

# (table, columns-in-insert-order, columns-needing-datetime-parsing, columns-needing-date-parsing)
TABLES = [
    (
        "customers",
        [
            "id", "external_id", "company_name", "contact_name", "email", "phone",
            "address", "country", "notes", "created_at", "updated_at",
        ],
        ["created_at", "updated_at"],
        [],
    ),
    (
        "products",
        [
            "id", "product_type", "name", "description", "unit_price", "unit",
            "is_active", "created_at", "updated_at",
        ],
        ["created_at", "updated_at"],
        [],
    ),
    (
        "events",
        [
            "id", "name", "venue", "default_start_date", "default_end_date",
            "created_at", "updated_at",
        ],
        ["created_at", "updated_at"],
        ["default_start_date", "default_end_date"],
    ),
    (
        "quotations",
        [
            "id", "quote_number", "customer_id", "created_by_id", "event_name",
            "event_venue", "event_start_date", "event_end_date", "event_dates_text",
            "installation_days", "status", "currency", "tax_rate_percent",
            "advance_payment_percent", "notes", "valid_until", "contact_name",
            "contact_email", "service_description", "discount_amount",
            "historical_total_amount", "quotation_date_text", "created_at", "updated_at",
        ],
        ["created_at", "updated_at"],
        ["event_start_date", "event_end_date", "valid_until"],
    ),
    (
        "quote_line_items",
        [
            "id", "quotation_id", "product_id", "description", "quantity",
            "unit_price", "sort_order",
        ],
        [],
        [],
    ),
]

NUMERIC_COLUMNS = {
    "unit_price", "quantity", "tax_rate_percent", "advance_payment_percent",
    "discount_amount", "historical_total_amount",
}


def parse_dt(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value
    return datetime.fromisoformat(str(value))


def parse_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def main():
    if len(sys.argv) != 2:
        print("Usage: python migrate_sqlite_to_postgres.py <postgres-connection-string>")
        sys.exit(1)

    pg_url = sys.argv[1]

    sconn = sqlite3.connect(DEV_DB)
    sconn.row_factory = sqlite3.Row
    pconn = psycopg2.connect(pg_url)
    pcur = pconn.cursor()

    for table, columns, dt_cols, date_cols in TABLES:
        scur = sconn.execute(f"SELECT {', '.join(columns)} FROM {table}")
        rows = scur.fetchall()

        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT (id) DO NOTHING"
        )

        inserted = 0
        for row in rows:
            values = []
            for col in columns:
                v = row[col]
                if col == "created_by_id" and table == "quotations":
                    # Local dev user IDs don't exist in production — never carry them over.
                    v = None
                elif col in dt_cols:
                    v = parse_dt(v)
                elif col in date_cols:
                    v = parse_date(v)
                elif col in NUMERIC_COLUMNS and v is not None:
                    v = Decimal(str(v))
                elif col == "is_active" and v is not None:
                    v = bool(v)
                values.append(v)

            pcur.execute(sql, values)
            inserted += pcur.rowcount

        pconn.commit()
        print(f"{table}: {len(rows)} rows in source, {inserted} newly inserted")

    sconn.close()
    pcur.close()
    pconn.close()
    print("Done.")


if __name__ == "__main__":
    main()
