#!/bin/sh
set -e
cd /app

mkdir -p /app/data /app/media

python manage.py migrate --noinput
exec gunicorn flightlog.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-1}" \
    --timeout 120
