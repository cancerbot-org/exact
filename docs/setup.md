# Local Development Setup

## Prerequisites

- Python 3.12+
- PostgreSQL 16 with PostGIS
- GDAL and GEOS libraries (required by PostGIS)
- Redis (optional — only needed for async geolocation tasks)

### macOS (Homebrew)

```bash
brew install postgresql@16 postgis gdal
brew services start postgresql@16
```

---

## First-time setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd exact
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create the database and user

```bash
psql postgres <<SQL
CREATE USER exact WITH CREATEDB PASSWORD '';
ALTER ROLE exact SUPERUSER;   -- needed to create PostGIS extension
CREATE DATABASE exact OWNER exact;
SQL

psql -d exact -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

> **Note**: Superuser is only required so that Django can create the `postgis`
> extension during migrations. You can revoke it afterwards if your security
> policy requires it.

### 3. Configure environment variables

Copy the example env file and edit as needed:

```bash
cp .env.example .env   # or create .env from scratch
```

Minimum required variables for local development (defaults are usually fine):

```dotenv
SECRET_KEY=any-local-secret-key
DATABASE_NAME=exact
DATABASE_USER=exact
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

On macOS the GDAL/GEOS fallback paths in `settings.py` point to
`/opt/homebrew/lib/`. If your Homebrew prefix differs, override them:

```dotenv
GDAL_LIBRARY_PATH=/usr/local/lib/libgdal.dylib
GEOS_LIBRARY_PATH=/usr/local/lib/libgeos_c.dylib
```

On Linux (e.g. Ubuntu) the typical paths are:

```dotenv
GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1
```

### 4. Run migrations

```bash
make migrate
# or: python manage.py migrate
```

### 5. Seed reference data

Reference data (diseases, therapies, markers, trial types, etc.) must be seeded
once before any matching will work:

```bash
make seed
# or: python manage.py seed_reference_data
```

### 6. Create a superuser (optional, for Django admin)

```bash
make createsuperuser
```

### 7. Start the dev server

```bash
make runserver
# or: python manage.py runserver
```

The API is available at `http://localhost:8000/`.
Interactive API docs: `http://localhost:8000/swagger/`

---

## Running tests

```bash
make pytest
# or: python -m pytest
```

Tests reuse the existing test database schema between runs (`--reuse-db`).
To force a fresh schema:

```bash
python -m pytest --create-db
```

### Test database setup

The test suite uses `conftest.py` to seed static reference data once per session.
The PostgreSQL user must be a superuser so that the test runner can create the
`postgis` extension if needed.

---

## Makefile reference

| Target | Description |
|--------|-------------|
| `make pytest` | Run the full test suite |
| `make migrate` | Apply database migrations |
| `make migrations` | Create new migration files |
| `make shell` | Open a Django interactive shell |
| `make runserver` | Start the development server |
| `make createsuperuser` | Create a Django admin superuser |
| `make seed` | Seed static reference data |

---

## Environment variable reference

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-…` | Django secret key — **change in production** |
| `DEBUG` | `true` | Debug mode; set to `false` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed host names |
| `CSRF_TRUSTED_ORIGINS` | _(empty)_ | Comma-separated CSRF-trusted origins |
| `DATABASE_NAME` | `exact` | PostgreSQL database name |
| `DATABASE_USER` | `exact` | PostgreSQL user |
| `DATABASE_PASSWORD` | _(empty)_ | PostgreSQL password |
| `DATABASE_HOST` | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `PATIENT_DB_URL` | _(unset)_ | Optional separate DB for PatientInfo; PostGIS URL (`postgis://`) |
| `REDIS_URL` | `redis://localhost:6379` | Redis URL for Celery (only needed for async tasks) |
| `GDAL_LIBRARY_PATH` | `/opt/homebrew/lib/libgdal.dylib` | Path to GDAL shared library |
| `GEOS_LIBRARY_PATH` | `/opt/homebrew/lib/libgeos_c.dylib` | Path to GEOS shared library |
| `ENVIRONMENT` | `local` | Environment name (`local` / `dev` / `staging` / `prod`) |
| `ADD_SEARCH_TRIALS_TRACES` | `false` | Set to `true` to log detailed trial-search reasoning |

---

## Optional: split PatientInfo database

`PatientInfo` records can be stored in a separate PostgreSQL database — useful
when patient data must be isolated for compliance reasons.

1. Provision a second PostGIS database.
2. Set `PATIENT_DB_URL=postgis://user:pass@host:5432/patients` in your `.env`.
3. Run `python manage.py migrate --database=patients` to create the schema.

The `PatientInfoRouter` in `exact/routers.py` routes all `PatientInfo` reads
and writes to the `patients` DB automatically. Everything else stays in
`default`.

---

## Optional: async geolocation tasks

When a `PatientInfo` record has `longitude`/`latitude` but no `geo_point`, the
`pre_save` signal can dispatch a Celery task to perform the lookup
asynchronously.

To enable:
1. Start Redis: `redis-server`
2. Start a Celery worker: `celery -A exact worker -l info`
3. Set `REDIS_URL` in your `.env`.

For local testing without Celery, set `PULL_COUNTRY_AND_POSTAL_CODE_INLINE=true`
to run geolocation synchronously during save.
