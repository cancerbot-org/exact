# cancerbot/exact

**EXACT** (EXtracting Attributes from Clinical Trials) — a stateless search
and matching engine for clinical trials.

For architecture, env vars, and advanced setup see the full docs:
<https://github.com/cancerbot-org/exact/blob/main/docs/setup.md>

## Quick start

Copy the file below as `docker-compose.yml` and run `docker compose up`. On
first start the trials database is automatically seeded from a public
snapshot (a few minutes, one-time). The seeding step drops and recreates
the `public` schema of the trials DB, so it is gated behind the opt-in
`TRIALS_DATABASE_INIT_FROM_BACKUP=1` variable — safe for the dedicated
`trials_db` service below, **do not enable it against a database you don't
want wiped**.

```yaml
services:
  main_db:
    image: postgis/postgis:16-3.5
    platform: linux/amd64
    environment:
      POSTGRES_DB: exact
      POSTGRES_USER: exact
      POSTGRES_PASSWORD: exact
    volumes:
      - exact_main_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U exact -d exact"]
      interval: 5s
      timeout: 5s
      retries: 15

  trials_db:
    image: postgis/postgis:16-3.5
    platform: linux/amd64
    environment:
      POSTGRES_DB: trials
      POSTGRES_USER: trials
      POSTGRES_PASSWORD: trials
    volumes:
      - exact_trials_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trials -d trials"]
      interval: 5s
      timeout: 5s
      retries: 15

  exact:
    image: cancerbot/exact:dev
    depends_on:
      main_db:
        condition: service_healthy
      trials_db:
        condition: service_healthy
    environment:
      SECRET_KEY: change-me
      DATABASE_HOST: main_db
      DATABASE_NAME: exact
      DATABASE_USER: exact
      DATABASE_PASSWORD: exact
      DATABASE_PORT: "5432"
      TRIALS_DATABASE_URL: postgresql://trials:trials@trials_db:5432/trials
      TRIALS_DATABASE_INIT_FROM_BACKUP: "1"
    ports:
      - "8000:8000"

volumes:
  exact_main_db_data:
  exact_trials_db_data:
```

```bash
docker compose up
```

Once up, the API is available at <http://localhost:8000> and interactive
docs at <http://localhost:8000/swagger/>.

## Create a user and API token

```bash
docker compose exec exact python manage.py createsuperuser
docker compose exec exact python manage.py drf_create_token <username>
```

Use the token as `Authorization: Token <token>`.

## Smoke test

```bash
curl -s http://localhost:8000/trials/ \
  -H "Authorization: Token <token>" | head
```

---

More: <https://github.com/cancerbot-org/exact/blob/main/docs/setup.md>
