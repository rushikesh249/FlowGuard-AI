#!/bin/bash
set -e

echo "=== FlowGuard AI Backend ==="

# Create required directories
mkdir -p /app/datasets/raw
mkdir -p /app/datasets/cleaned
mkdir -p /app/ai/models
mkdir -p /app/ai/results

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
python -c "
import time, sys
sys.path.insert(0, '/app')
from database import engine
from sqlalchemy import text

for i in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('PostgreSQL is ready.')
        break
    except Exception:
        time.sleep(2)
else:
    print('ERROR: Could not connect to PostgreSQL after 60s.')
    sys.exit(1)
"

# Run Alembic migrations
echo "Running database migrations..."
cd /app
alembic upgrade head
echo "Migrations complete."

# Execute the main command (uvicorn or celery)
echo "Starting: $@"
exec "$@"
