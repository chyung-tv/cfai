# CFAI Roadmap and Progress Tracker

Last updated: 2026-02-26
Source: migrated from `.cursor/roadmap.md`

## Progress Tracker

Use this section as the live execution board.

### Module Status

- [~] Module 1 - Hard Cutover and Pruning (in progress)
- [ ] Module 2 - Containerized Runtime Foundation (Docker + PostgreSQL)
- [ ] Module 3 - Backend Core (FastAPI Workflow, Auth, RBAC, Quota)
- [ ] Module 4 - Frontend Adaptation (Readability and UX Integration)
- [ ] Module 5 - Phase 1 Completion Gate

### Current Focus

- Active module: Module 1 - Hard Cutover and Pruning
- Current owner: user + coding agent
- Next acceptance checkpoint: resolve `MOD1-VAL-001` then verify end-to-end frontend->backend flow on primary runtime entries (post-migration path layout)
- Blockers: see `./debuglog.md`
- Supporting track (current session): extracted and documented frontend UI/UX baseline in `./frontend-ui-ux.md` and standardized backend package management onto `uv`.

### Session Briefing (for every new agent session)

Use this response order:

1. Where we are at
2. What we need to implement next
3. What we just implemented

Keep this block updated so agents can answer quickly:

- Where we are at: Module 1 cutover remains in progress with executable roots physically aligned to `frontend` and `backend`, plus a documented frontend UI/UX baseline for Module 4 implementation continuity.
- What we need to implement next: resolve `MOD1-VAL-001`, run validation checks after dependency installation, and continue residual archival cleanup decisions.
- What we just implemented: documented frontend design/UX conventions in memory and shifted backend dependency management to `uv` as the sole package manager.

### Execution Notes

- Update this file whenever a module starts, changes state, or is completed.
- Record unresolved issues in `./debuglog.md`.
- Record solved patterns and lessons in `./memo.md`.
- At the beginning of each new agent chat, the agent should read memories and provide the Session Briefing before module planning.

---

## 0) Locked Product and Architecture Decisions

- Target structure in one repository:
  - `/frontend` (Next.js, latest stable)
  - `/backend` (Python FastAPI)
- Turborepo and Motia are dropped.
- Deployment is Docker-first with `docker compose` and PostgreSQL.
- Hard cut-over is intentional: legacy/redundant layers are removed once replacement module reaches acceptance criteria.
- Auth authority is backend-only with FastAPI-managed OAuth and DB sessions.
- RBAC is fixed:
  - `dev`: unlimited + dev routes
  - `free`: 3 triggers / rolling 30 days
  - `premium`: unlimited
- Workflow is state-machine-driven with granular substate visibility.
- Real-time updates use SSE.
- Cache strategy is fixed to key B: `symbol + input_hash + pipeline_version`, freshness 7 days.

## Module 1) Hard Cutover and Pruning

Goal: remove architecture paths not part of Phase 1 target so implementation does not drift.

### Scope

- Remove Turborepo/workspace coupling and obsolete shared layers not needed in the new split.
- Remove Motia runtime, step files, and workbench-specific artifacts.
- Remove NextAuth-centric auth ownership from frontend once backend auth is live.
- Retain only migration-safe assets needed for data transfer and parity verification.

### Hard cutover note

- Cutover is not a soft coexistence strategy.
- After replacement path is verified for a module, legacy path is deleted in the same wave.
- Any retained legacy code must be explicitly tagged as temporary migration bridge with an expiry checkpoint.

### Acceptance criteria

- No active runtime dependency on Motia/Turbo paths.
- Frontend no longer requires direct business DB access path for auth/analysis control.
- Repository tree reflects `/frontend` and `/backend` as primary executables.

## Module 2) Containerized Runtime Foundation (Docker + PostgreSQL)

Goal: establish a deterministic local and deployment runtime baseline before feature migration.

### Scope

- Define `docker-compose` services for:
  - `postgres`
  - `backend`
  - `frontend`
- Standardize environment contracts (database URL, backend URL, OAuth callback domains, cookie settings).
- Ensure backend is authoritative writer for business/auth tables.

### Acceptance criteria

- Single command brings up all services.
- Backend can connect/migrate DB and pass health checks.
- Frontend can call backend over compose network/ingress.

## Module 3) Backend Core (FastAPI Workflow, Auth, RBAC, Quota)

Goal: deliver the full Phase 1 backend capability behind stable APIs.

### 3.1 Auth and Session Submodule

- FastAPI-managed Google OAuth flow:
  - `GET /auth/oauth/google/start`
  - `GET /auth/oauth/google/callback`
  - `GET /auth/me`
  - `POST /auth/logout`
- Backend DB session lifecycle in `user_sessions`.
- Frontend consumes session cookie and `/auth/me`.

### 3.2 Workflow Engine Submodule (Base Node + Base Workflow)

- Implement reusable base node abstraction:
  - typed input/output
  - retry/timeout policy
  - normalized error handling
  - transition hooks
- Implement base workflow orchestrator:
  - ordered graph/pipeline execution
  - transition rules and persistence
  - SSE event emission

### 3.3 State Machine Submodule (Granular Visibility)

- Coarse states:
  - `queued`, `running`, `completed`, `failed`, `cancelled`, `completed_cached`
- Granular substates:
  - `validate_input`, `resolve_cache`, `fetch_market_data`, `qualitative_analysis`,
    `reverse_dcf`, `growth_judgement`, `dcf`, `rating`, `assemble_result`,
    `persist_result`, `publish_sse`
- Persist transitions in workflow tables and emit SSE from structured events.

### 3.4 Persistence and Cache Submodule

- Core target tables:
  - `users`
  - `user_sessions`
  - `oauth_accounts`
  - `analysis_workflows`
  - `analysis_workflow_events` (recommended)
  - `stock_analysis_results`
- Cache reuse policy:
  - lookup by `symbol + input_hash + pipeline_version`
  - freshness window 7 days

### 3.5 RBAC and Quota Submodule

- Guard chain order:
  1. `require_auth`
  2. `require_role`
  3. `require_analysis_quota` (trigger route only)
- Quota policy:
  - free users limited to 3 triggers per rolling 30 days
  - dev/premium unlimited
- Quota count event:
  - count successful trigger creations (idempotency-safe)

### Acceptance criteria

- Authenticated user can trigger workflow via backend API.
- Workflow transitions are persisted and stream to frontend via SSE.
- Final results are persisted and queryable.
- RBAC/quota enforcement is active and observable in API responses.

## Module 4) Frontend Adaptation (Readability and UX Integration)

Goal: make frontend consume backend-auth and backend-workflow outputs without legacy ownership.

### Scope

- Switch auth consumption to backend session + `/auth/me`.
- Replace old stream/status coupling with SSE payload contract from backend.
- Render granular progress using state/substate model.
- Read final results through backend APIs only.
- Implement cache-hit and cache-miss UX consistency for analysis page.

### Acceptance criteria

- Frontend can trigger analysis and display live progress until terminal state.
- Frontend can fetch and render final readable result payload.
- No frontend-side direct business authorization logic outside backend contract.

## Module 5) Phase 1 Completion Gate

Phase 1 is complete only when all module criteria are met end-to-end:

- trigger analysis -> observe SSE states -> read final result
- auth/rbac/quota enforced at backend boundary
- cache behavior consistent with 7-day key-B policy
- legacy paths pruned according to hard cutover rule

## Phase 2 (Vision Only, No Detailed Plan Yet)

Portfolio builder vision:

- user defines target portfolio shape/preferences
- system suggests candidate stocks aligned to desired profile
- analysis outputs become core signals for recommendation loop

Detailed planning for Phase 2 starts after Phase 1 stabilization.
