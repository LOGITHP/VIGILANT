#!/bin/sh
set -e

echo "=========================================================="
echo "      VIGILANT - AI CCTV Surveillance Intelligence        "
echo "=========================================================="

echo "[VIGILANT INIT] Running Alembic database migrations..."
alembic upgrade head

# Check and execute ephemeral bootstrap seed script
if [ -f /app/scripts/seed_first_user.py ]; then
    echo "[VIGILANT INIT] Found first-run seed script. Initializing default admin..."
    python /app/scripts/seed_first_user.py || true
    echo "[VIGILANT INIT] Ensuring seed script is wiped out..."
    rm -f /app/scripts/seed_first_user.py
else
    echo "[VIGILANT INIT] No seed script detected (already wiped on prior run). Preserving volume data."
fi

echo "[VIGILANT INIT] Launching ASGI Uvicorn production server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

