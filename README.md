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

- Node.js 18+
- pnpm
- Python 3.10+
- uv
- Neon Postgres database

### 1) Configure environment

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

Set Neon URLs from your Neon project in `backend/.env`:

- `DATABASE_URL`: pooled Neon URL (runtime)
- `DATABASE_URL_DIRECT`: direct Neon URL (migrations)

### 2) Install dependencies

```bash
pnpm --dir frontend install
uv sync --directory backend
```

### 3) Run services from terminal

```bash
pnpm --dir frontend dev
set -a; source backend/.env; set +a
uv run --directory backend uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
```

### Manual migrations (Alembic)

Migrations are intentionally manual (not auto-run on backend startup). Load backend env vars in your terminal first:

```bash
set -a; source backend/.env; set +a

# Create a migration
uv run --directory backend alembic revision --autogenerate -m "describe_change"

# Apply latest migrations
uv run --directory backend alembic upgrade head
```

## Notes

- Frontend dependencies and scripts are managed with `pnpm` in `frontend/`.
- Backend dependencies and runtime are managed with `uv` in `backend/`.
- Backend DB stack uses Neon Postgres + async SQLAlchemy + Alembic.
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
