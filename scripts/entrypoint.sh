#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Bootstrapping initial data..."
python -m scripts.bootstrap_db

echo "Starting application..."
exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
