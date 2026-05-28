#!/bin/bash
set -e

echo "[entrypoint] Waiting for PostgreSQL..."
until python -c "from db.database import get_connection; get_connection()" 2>/dev/null; do
  echo "[entrypoint]   DB not ready, retrying in 3s..."
  sleep 3
done
echo "[entrypoint] PostgreSQL is ready."

echo "[entrypoint] Checking legal_articles table..."
COUNT=$(python -c "
from db.database import get_connection
try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM legal_articles')
            print(cur.fetchone()[0])
except Exception:
    print(0)
" 2>/dev/null || echo "0")

echo "[entrypoint] Articles in DB: $COUNT"

if [ "$COUNT" -lt "100" ]; then
  echo "[entrypoint] Seeding legal articles (no embeddings — run ingest --seed for vectors)..."
  python -m ingestion.ingest --seed --no-embed
  echo "[entrypoint] Seed complete."
else
  echo "[entrypoint] Articles already present, skipping seed."
fi

echo "[entrypoint] Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
