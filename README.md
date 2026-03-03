# EXACT — Clinical Trial Matching Engine

EXACT (EXtracting Attributes from Clinical Trials) is a standalone Django
service that owns the trial catalog, patient profile management, and the
eligibility-matching engine extracted from the CancerBot platform.

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/overview.md](docs/overview.md) | Architecture, key components, data flow |
| [docs/setup.md](docs/setup.md) | Local development setup |
| [docs/api.md](docs/api.md) | REST API reference |
| [docs/data-migration.md](docs/data-migration.md) | Migrating trial data from CancerBot |

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_reference_data
python manage.py runserver
```

See [docs/setup.md](docs/setup.md) for full instructions including database
setup, environment variables, and test configuration.
