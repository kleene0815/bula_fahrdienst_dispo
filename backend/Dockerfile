FROM python:3.12-slim

WORKDIR /app

# Abhängigkeiten zuerst (Layer-Caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# App-Code kopieren
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
