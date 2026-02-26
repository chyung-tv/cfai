# CFAI Roadmap and Progress Tracker

Last updated: 2026-02-26 (Phase 3.3 documentation expansion)
Source: migrated from `.cursor/roadmap.md`

## Progress Tracker

Use this section as the live execution board.

### Module Status

- [x] Module 1 - Hard Cutover and Pruning (completed)
- [x] Module 2 - Containerized Runtime Foundation (Docker + PostgreSQL) (completed)
- [ ] Module 3 - Backend Core (FastAPI Workflow, Auth, RBAC, Quota)
- [ ] Module 4 - Frontend Adaptation (Readability and UX Integration)
- [ ] Module 5 - Phase 1 Completion Gate

### Current Focus

- Active module: Module 3 - Backend Core (FastAPI Workflow, Auth, RBAC, Quota)
- Current owner: user + coding agent
- Next acceptance checkpoint: complete Module 3.3 documentation expansion (linear node state machine + artifact persistence model), then implement nodes in phased order starting with resolver/deep-research/artifact-store foundations.
- Blockers: see `./debuglog.md`
- Supporting track (current session): documenting backend analysis redesign for Module 3.3 (ticker/company input, deep-research-first linear chain, thin workflow context, artifact-per-node persistence, and schema-TBD markers for rapid iteration).

### Session Briefing (for every new agent session)

Use this response order:

1. Where we are at
2. What we need to implement next
3. What we just implemented

Keep this block updated so agents can answer quickly:

- Where we are at: Modules 1 and 2 are complete with a stable Docker-first frontend/backend/postgres runtime and verified compose migration path.
- What we need to implement next: execute Module 3.3 phases in order (3.3A state/context contract, 3.3B node contracts, 3.3C persistence/cache schema, then implementation), keeping structured output schema explicitly TBD until stabilized.
- What we just implemented: finalized Module 3.3 documentation plan decisions (strictly linear node chain, resolver ambiguity auto-pick policy, stock catalog + artifact store split, and Deep Research cost-control via cache-first reuse).

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
- v1 design constraint:
  - keep execution strictly linear (no parallel branches) to simplify orchestration and failure semantics.
- v1 linear substate sequence:
  - `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` ->
    `audit_growth_likelihood` -> `advisor_decision` -> `persist_artifacts` -> `publish_sse`
- Thin orchestration context contract:
  - workflow context carries control-plane metadata and artifact references only.
  - heavy payloads are persisted per-node in artifact storage and loaded by reference in downstream nodes.
- Persist transitions in workflow tables and emit SSE from structured events.

#### 3.3A) State Machine and Context Model

- Input contract accepts both:
  - ticker symbol (e.g., `AAPL`)
  - company-name query (e.g., `Apple`)
- Resolution strategy:
  - hybrid lookup (external provider + local stock catalog cache)
  - ambiguity policy: deterministic auto-pick best candidate in v1, while storing candidate list/confidence for observability.
- Context handoff policy:
  - pass `artifact_id`/`cache_key` references between nodes
  - avoid large in-memory payload propagation

#### 3.3B) Node-by-Node Responsibility Contracts

- `resolve_query`:
  - normalize user query and resolve canonical symbol/company identity.
- `deep_research`:
  - produce long-form research report (highest-latency, highest-cost node) and persist as artifact.
- `structured_output`:
  - extract/classify report into backend schema for downstream reasoning and rendering inputs.
  - schema status: TBD (rapid iteration expected).
- `reverse_dcf`:
  - compute required growth matrix across discount-rate scenarios.
- `auditor`:
  - evaluate growth materialization likelihood from deep-research report + reverse-DCF outputs.
- `advisor`:
  - produce action/role/risk/tier recommendation from prior node outputs.
- `persist_artifacts`:
  - finalize artifact linkage + workflow summary payload for retrieval endpoints.

#### 3.3C) Persistence, Cache, and Retrieval Design

- Storage split:
  - `analysis_workflow_events` = timeline/transition log (light payload only)
  - `analysis_workflow_artifacts` = one row per node output artifact (heavy payload allowed)
  - `stock_catalog` = canonical stock identity + resolver memory cache
- Rationale:
  - keep event queries fast and stable
  - support artifact versioning/cache reuse independently from event retention
- Cache policy (analysis artifacts):
  - key by `symbol + input_hash + pipeline_version` (+ node/version dimensions where needed)
  - freshness baseline: 7 days, with stricter policy for expensive deep-research artifacts if needed.

#### 3.3D) Provider and Cost Strategy

- Deep Research provider path:
  - primary check: Pydantic AI pathway if it can cleanly invoke Gemini Deep Research Interactions.
  - fallback/default: Google GenAI SDK using Interactions API (`deep-research-pro-preview-12-2025`).
- Cost controls:
  - cache-first behavior for deep-research artifacts
  - use lower-cost/faster models for downstream structured nodes where precision profile allows.

#### 3.3E) Failure Semantics and Observability

- Define per-node error taxonomy and terminal mapping to `failed`.
- Events must include machine-stable `state/substate` and concise diagnostic metadata.
- Support partial rerun strategy from valid cached artifacts where upstream outputs are still fresh.
- Structured output and selected artifact schemas remain TBD until design iteration stabilizes.

#### 3.3F) Artifact Taxonomy and Cache-Key Contract

- Canonical artifact types (v1):
  - `query_resolution`
  - `deep_research_report`
  - `structured_output` (schema_tbd)
  - `reverse_dcf_matrix`
  - `auditor_assessment`
  - `advisor_recommendation`
  - `workflow_summary`
- Artifact row contract (v1 baseline):
  - one row per node output artifact
  - required identity fields: `workflow_id`, `stock_id`, `artifact_type`, `artifact_version`, `cache_key`
  - payload fields: `payload_json` and optional `payload_text` for long reports
- Cache-key template (v1 baseline):
  - `symbol + input_hash + pipeline_version + artifact_type + artifact_version`
  - for deep research, include prompt/research profile version in `input_hash` derivation.

#### 3.3G) Acceptance Criteria by Phase

- 3.3A acceptance criteria:
  - roadmap documents linear chain and canonical substate names.
  - context contract explicitly limits handoff to references/metadata.
- 3.3B acceptance criteria:
  - each node has documented responsibility, expected inputs, expected outputs, and failure mode.
  - structured output schema marked TBD with version placeholder.
- 3.3C acceptance criteria:
  - storage split is explicit (`events` timeline vs `artifacts` heavy payload vs `stock_catalog` identity).
  - cache key and artifact versioning policy is documented.
- 3.3D acceptance criteria:
  - deep research provider path and fallback/default are documented.
  - cost-control policy documents cache-first requirement for deep research.
- 3.3E acceptance criteria:
  - terminal failure mapping and required event diagnostics are documented.
  - partial rerun behavior from valid cached artifacts is documented.

### 3.4 Persistence and Cache Submodule

- Core target tables:
  - `users`
  - `user_sessions`
  - `oauth_accounts`
  - `analysis_workflows`
  - `analysis_workflow_events` (timeline + transitions)
  - `analysis_workflow_artifacts` (node outputs, cacheable)
  - `stock_catalog` (canonical symbol/company cache)
  - `stock_analysis_results` (optional terminal projection table; TBD based on read-path needs)
- Cache reuse policy:
  - lookup by `symbol + input_hash + pipeline_version`
  - freshness window baseline 7 days
  - deep-research artifacts should enforce cache-first reuse due to cost profile

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
