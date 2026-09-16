# ebag-catalog

A product catalog service for eBag built with Django (Django REST Framework) and Postgres.

## How it was built

1. A design session captured in [`docs/design.md`](docs/design.md).
2. Work split into small steps (one commit each).
3. Each step prompted to an AI assistant, then reviewed and iterated until done.

## Run it

Prerequisites: [Docker](https://docs.docker.com/get-docker/) and [uv](https://docs.astral.sh/uv/).

```
cp .env.example .env              # local settings
docker compose up -d --wait       # Postgres
uv sync --frozen                  # Python dependencies
uv run manage.py migrate          # schema
uv run manage.py flush --no-input && uv run manage.py loaddata demo    # seed (or reset) categories and products
uv run manage.py runserver        # API at http://localhost:8000/api/v1/
uv run manage.py test
```

## Try it

[`docs/api.http`](docs/api.http) — CRUD and searches
