#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --run-syncdb

bash /app/docker/init_trials_db.sh

cat <<'EOF'

============================================================
  Server is starting. To create a superuser and API token:

    docker compose exec exact python manage.py createsuperuser
    docker compose exec exact python manage.py drf_create_token <username>
============================================================

EOF

echo "Migrations done. Starting: $*"
exec "$@"
