#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --run-syncdb

echo "Migrations done. Starting: $*"
exec "$@"
