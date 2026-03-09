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
  - Module 3 backend core hardening (projection read-model + workflow runtime checks)
  - Module 4 frontend results UX glow-up (`/demo/analysis`, tabs-first IA)

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
docker compose run --rm backend uv run alembic revision --autogenerate -m "describe_change"

# Apply latest migrations
docker compose run --rm backend uv run alembic upgrade head
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
- Workflow runtime/domain layout:
  - shared runtime primitives: `backend/app/core/workflow/`
  - analysis workflow domain: `backend/app/workflows/analysis/`
  - maintenance seed/sync domain: `backend/app/workflows/maintenance/`
- Progress and module checkpoints live in `.cursor/memories/roadmap.md`.

### Test/CI Knob (analysis)

- Set `SKIP_DEEP_RESEARCH_IN_TESTS=true` to bypass live deep-research calls in integration tests.
- In skip mode, workflow seeds `reportMarkdown` from latest persisted completed payload for the same symbol and emits `deep_research_skipped_fixture`.
- Keep at least one periodic/manual full live run without this flag to detect provider drift.

## License

Private - All rights reserved.
