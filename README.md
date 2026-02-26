# CFAI

CFAI is moving through a hard cutover from legacy Motia/NextAuth paths to a backend-authoritative frontend/backend split.

## Runtime Entry Points

- `frontend/`: primary frontend executable boundary
- `backend/`: primary backend executable boundary (FastAPI service on port 3001)

Temporary bridge directories still present for migration safety:

- `packages/db`
- `packages/types`

## Current Module 1 State

- Turborepo runtime orchestration removed from root scripts.
- Motia runtime artifacts pruned and legacy backend folder removed.
- Frontend no longer owns NextAuth or direct DB mutation paths.
- Backend workflow logic was documented before pruning in `.cursor/memories/backend-analysis-workflow.md`.

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm
- Python 3.10+
- uv

### Install

```bash
pnpm --dir frontend install
uv sync --directory backend
cp .env.example .env.local
```

### Run

```bash
# Frontend (primary)
pnpm --dir frontend dev

# Backend (primary)
uv run --directory backend uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
```

### Service URLs

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:3001`

## Migration Notes

- `packages/db` and `packages/types` are temporary bridges and must be retired after backend/domain contracts are fully moved.
- Track progress and checkpoints in `.cursor/memories/roadmap.md`.

## License

Private - All rights reserved.
