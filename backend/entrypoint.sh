#!/bin/sh
set -e

echo "Warte auf Datenbank…"
alembic upgrade head

echo "Starte Backend…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
