# Local Development Setup

## Prerequisites

- Python 3.12+
- PostgreSQL 16 with PostGIS 3.5+
- GDAL and GEOS libraries (required by GeoDjango / PostGIS)
- Redis (optional — only needed for async geolocation tasks)

> **Why PostGIS?** EXACT uses geographic queries to match patients with nearby
> trial sites (distance calculations, point-in-region filters). The database
> engine is `django.contrib.gis.db.backends.postgis`, so PostGIS must be
> installed and enabled before migrations can run.

### macOS (Homebrew)

```bash
brew install postgresql@16 postgis gdal geos
brew services start postgresql@16
```

### Linux (Debian / Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y postgresql-16 postgresql-16-postgis-3 \
    gdal-bin libgdal-dev libgeos-dev
```

### Docker

If you prefer Docker, the official PostGIS image has everything pre-installed:

```bash
docker run -d --name exact-db \
  -e POSTGRES_USER=exact -e POSTGRES_PASSWORD=exact -e POSTGRES_DB=exact \
  -p 5432:5432 postgis/postgis:16-3.5
```

### Verifying PostGIS

After installing, confirm the extension is available:

```bash
psql -d exact -c "SELECT PostGIS_Version();"
# Expected output: 3.5 ...
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

On Linux the system GDAL/GEOS libraries are found automatically — no env
vars needed.

On macOS (Homebrew) Django cannot auto-detect the library paths, so you must
set them explicitly.  Find the right paths with `brew --prefix gdal` /
`brew --prefix geos`, then add to your `.env`:

```dotenv
# Apple Silicon (default Homebrew prefix)
GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib
GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib

# Intel Macs (older Homebrew prefix)
# GDAL_LIBRARY_PATH=/usr/local/lib/libgdal.dylib
# GEOS_LIBRARY_PATH=/usr/local/lib/libgeos_c.dylib
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
| `TRIALS_DATABASE_URL` | _(unset)_ | External trials DB URL — enables split-database mode (`postgresql://user:pass@host:5432/db`) |
| `PATIENT_DATABASE_URL` | _(unset)_ | External patient DB URL — used by `search_trials_for_patients` CLI command |
| `REDIS_URL` | `redis://localhost:6379` | Redis URL for Celery (only needed for async tasks) |
| `GDAL_LIBRARY_PATH` | `/opt/homebrew/lib/libgdal.dylib` | Path to GDAL shared library |
| `GEOS_LIBRARY_PATH` | `/opt/homebrew/lib/libgeos_c.dylib` | Path to GEOS shared library |
| `ENVIRONMENT` | `local` | Environment name (`local` / `dev` / `staging` / `prod`) |
| `ADD_SEARCH_TRIALS_TRACES` | `false` | Set to `true` to log detailed trial-search reasoning |

---

## External trials database (production mode)

In production, EXACT is a **stateless matching engine** that reads trial data
from an external database. It does not own or manage the trial schema — the
external database must already have the correct tables and data.

EXACT's local `default` database is used **only** for authentication
(users and tokens). All `trials` app model reads are routed to the external
database automatically by `exact.db_router.TrialsDatabaseRouter`.

### Setup

Set the `TRIALS_DATABASE_URL` environment variable (or add it to `.env`):

```dotenv
TRIALS_DATABASE_URL=postgresql://readonly_user:secret@trials-db.example.com:5432/trials
```

Then migrate only the local database (auth tables):

```bash
python manage.py migrate          # creates auth/token tables in default DB
python manage.py runserver
```

**Do not** run `migrate --database=trials` — the external schema is managed by
its owner.

### Standalone / local development

When `TRIALS_DATABASE_URL` is **not set**, the router is inactive and
everything uses the single `default` database. This is the mode used for local
development and testing:

```bash
python manage.py migrate
python manage.py seed_reference_data   # populates reference data locally
python manage.py runserver
```

