#!/bin/sh
set -e

echo "Warte auf Datenbank…"
alembic upgrade head

python /app/scripts/init_keycloak.py || echo "Keycloak-Init fehlgeschlagen – Backend startet trotzdem."

echo "Starte Backend…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
