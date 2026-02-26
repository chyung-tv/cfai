# CFAI

CFAI is currently structured as a frontend/backend split:

- `frontend/` - Next.js application
- `backend/` - FastAPI service (managed with `uv`)

## Runtime Entry Points

- `frontend/` (port 3000)
- `backend/` (port 3001)

## Current Delivery State

- Module 1 (Hard Cutover and Pruning) is closed.
- Execution focus has shifted to:
  - Module 2 runtime foundation (docker compose + async DB baseline)
  - Module 4 frontend flow rebuild on the new scaffold baseline

## Quick Start

### Prerequisites

- Docker + Docker Compose
- (Optional host-side fallback) Node.js 18+, pnpm, Python 3.10+, uv

### Docker-First Dev (Recommended)

```bash
cp .env.example .env
docker compose up --build
```

This starts:

- frontend: `http://localhost:3000` (Next.js dev with bind-mounted source)
- backend: `http://localhost:3001` (FastAPI uvicorn reload)
- postgres: `localhost:5432`

### Manual Migrations (Alembic)

Migrations are intentionally manual (not auto-run on backend startup):

```bash
# Create a migration
docker compose run --rm backend alembic revision --autogenerate -m "describe_change"

# Apply latest migrations
docker compose run --rm backend alembic upgrade head
```

### Host-Side Fallback (Without Docker)

```bash
pnpm --dir frontend install
uv sync --directory backend
pnpm --dir frontend dev
uv run --directory backend uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
```

## Notes

- Frontend dependencies and scripts are managed with `pnpm` in `frontend/`.
- Backend dependencies and runtime are managed with `uv` in `backend/`.
- Backend DB stack uses async SQLAlchemy + Alembic.
- Progress and module checkpoints live in `.cursor/memories/roadmap.md`.

## License

Private - All rights reserved.
