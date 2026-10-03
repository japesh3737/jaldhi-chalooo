#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1 --timeout 120
