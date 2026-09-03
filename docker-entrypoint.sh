#!/bin/sh
set -e

# Idempotent — a no-op if the DB is already at head, so it's safe to run on every deploy.
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
