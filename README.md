# EXACT — Clinical Trial Matching Engine

EXACT (EXtracting Attributes from Clinical Trials) is a stateless search and
matching engine for clinical trials. It connects to an external database that
holds the trial catalog and reference data — EXACT does not own or manage that
data. Patient profiles are passed inline with each API request; nothing is
persisted.

The only data EXACT stores locally is authentication (users and tokens).

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/overview.md](docs/overview.md) | Architecture, key components, data flow |
| [docs/setup.md](docs/setup.md) | Local development setup |
| [docs/api.md](docs/api.md) | REST API reference |
| [docs/data-migration.md](docs/data-migration.md) | Migrating trial data from CancerBot |

## Quick start (connecting to an existing trials database)

```bash
pip install -r requirements.txt

# Local DB for auth/tokens only
python manage.py migrate

# Point to the external trials database
export TRIALS_DATABASE_NAME=cancerbot_trials
export TRIALS_DATABASE_HOST=trials-db.example.com
export TRIALS_DATABASE_USER=readonly
export TRIALS_DATABASE_PASSWORD=secret

python manage.py runserver
```

## Quick start (standalone / local development)

When no external trials database is configured, EXACT falls back to a single
local database for everything — useful for development and testing:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_reference_data
python manage.py runserver
```

See [docs/setup.md](docs/setup.md) for full instructions including database
setup, environment variables, and test configuration.
