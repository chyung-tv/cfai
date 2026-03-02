# CFAI Roadmap and Progress Tracker

Last updated: 2026-03-02 (workflow prototype satisfactory milestone reached)
Purpose: execution tracker only (progress, sequencing, checkpoints, acceptance).

---

## Progress Tracker

### Module Status

- [x] Module 1 - Hard Cutover and Pruning (completed)
- [x] Module 2 - Containerized Runtime Foundation (Docker + PostgreSQL) (completed)
- [ ] Module 3 - Backend Core (FastAPI Workflow, Auth, RBAC, Quota)
- [ ] Module 4 - Frontend Adaptation (Readability and UX Integration)
- [ ] Module 5 - Phase 1 Completion Gate

### Current Focus

- Active module: Module 3 - Backend Core
- Current owner: user + coding agent
- Next acceptance checkpoint: finalize strict trigger/access contracts, then implement `persist_artifacts` to close the workflow pipeline.
- Blockers: see `./debuglog.md`

### Session Briefing (for every new agent session)

Use this response order:

1. Where we are at
2. What we need to implement next
3. What we just implemented

Keep this block updated:

- Where we are at: Modules 1 and 2 are complete with stable Docker-first frontend/backend/postgres runtime.
- What we need to implement next: complete strict trigger/access split (lookup + result-access + trigger), then implement `persist_artifacts` and finalize completion path.
- What we just implemented: reached a satisfactory workflow prototype with DB-backed demo rendering, fixed structured output UI shape, reverse DCF/audit/advisor integration, and profile-by-case advisor matrix semantics.

### Execution Notes

- `roadmap.md` tracks execution state only.
- Architecture snapshot lives in `./architecture.md`.
- Architecture decision rationale log lives in `./architecture-decisions.md`.
- Record unresolved issues in `./debuglog.md`.
- Record resolved lessons in `./memo.md`.

---

## Phase-to-Architecture Mapping

- Module 2 runtime foundation -> `./architecture.md#2-component-topology`
- Module 3.1 auth/rbac/quota -> `./architecture.md#6-auth-rbac-and-quota-boundary`
- Module 3.1B maintenance workflow -> `./architecture.md#31-maintenance-workflow-domain`
- Module 3.3 analysis workflow -> `./architecture.md#32-analysis-workflow-domain`
- Module 3.4 persistence/cache -> `./architecture.md#4-data-architecture`
- Module 4 frontend adaptation -> `./architecture.md#2-component-topology`

## Phase-to-Decision Mapping

- Workflow isolation decision -> `./architecture-decisions.md#adr-0001-split-runtime-into-maintenance-and-analysis-workflow-domains`
- Ingestion-first sequencing -> `./architecture-decisions.md#adr-0002-ingestion-first-sequencing-before-resolve_query-implementation`
- S&P500-first seed scope -> `./architecture-decisions.md#adr-0003-v1-catalog-seed-scope-is-sp500-first`
- Starter-plan top500-us seed proxy -> `./architecture-decisions.md#adr-0006-starter-plan-seed-universe-uses-directoryscreener-top-500-us-proxy`
- Deep-research payload persistence v1 -> `./architecture-decisions.md#adr-0007-v1-deep-research-payload-persists-as-markdown-first-with-embedded-citations`
- Auth sequencing -> `./architecture-decisions.md#adr-0004-auth-implementation-sequencing-defers-firebase-option-b-pivot`
- Hybrid read-path direction -> `./architecture-decisions.md#adr-0005-read-path-direction-is-hybrid-projection-table-is-target-read-model`

---

## Module 1) Hard Cutover and Pruning

Status: completed

### Acceptance criteria (completed)

- No active runtime dependency on Motia/Turbo paths.
- Frontend no longer requires direct business DB access path for auth/analysis control.
- Repository tree reflects `/frontend` and `/backend` as primary executables.

---

## Module 2) Containerized Runtime Foundation (Docker + PostgreSQL)

Status: completed

### Acceptance criteria (completed)

- Single command brings up all services.
- Backend can connect/migrate DB and pass health checks.
- Frontend can call backend over compose network/ingress.

---

## Module 3) Backend Core (FastAPI Workflow, Auth, RBAC, Quota)

Status: active

Architecture mapping: `./architecture.md#3-workflow-domains`, `./architecture.md#4-data-architecture`, `./architecture.md#6-auth-rbac-and-quota-boundary`  
Decision references: `./architecture-decisions.md#accepted-decisions`

### 3.1 Auth and Session Submodule

Execution goal:

- Maintain current backend session-based auth path while analysis workflow is being materialized.
- Enforce backend auth/rbac/quota boundary contracts.

Current sequencing note:

- Firebase Option B pivot is deferred until workflow core stability checkpoint.

### 3.1B Maintenance Workflow Submodule (catalog ingestion)

Execution goal:

- Implement standalone `maintenance` workflow domain for stock catalog ingestion.

Immediate step order:

1. Implement seed run path for S&P500 universe (~500 symbols).
2. Persist stock catalog with deterministic normalization and idempotent upsert.
3. Validate seeded catalog quality (uniqueness, normalization, active/search fitness).
4. Define weekly refresh run contract.

Acceptance checkpoint:

- one-time seed run contract is implemented and verifiable
- seeded catalog quality gate passes
- maintenance run is isolated from analysis orchestration path

### 3.3 Analysis Workflow Submodule

Execution goal:

- Materialize analysis state machine after catalog seed validation.

Immediate step order:

1. Implement `resolve_query` against seeded catalog shape. (completed)
2. Implement `deep_research` node and persist report payload. (completed)
3. Implement `structured_output` on top of deep research output. (completed)
3b. Finalize fixed UI-first `structured_output` schema and remove dynamic runtime shape. (completed)
4. Implement `reverse_dcf` and continue node-by-node sequence. (completed)
5. Implement `audit_growth_likelihood` and continue node-by-node sequence. (completed)
6. Implement `advisor_decision` and continue node-by-node sequence. (completed)
7. Preserve event persistence + SSE semantics. (in progress)
8. Prototype milestone: workflow output and demo rendering are satisfactory for current iteration. (completed)

Acceptance checkpoint:

- trigger -> transitions -> SSE -> persisted results works end-to-end
- resolver behavior is deterministic for v1 scope
- deep research report payload is persisted and reusable by downstream nodes

### 3.4 Persistence and Cache Submodule

Execution goal:

- Complete persistence model required by maintenance + analysis domains.

Immediate step order:

1. Finalize `stock_catalog` for maintenance workflow.
2. Finalize analysis tables/contracts (`analysis_workflows`, `events`, `artifacts`).
3. Keep cache-key/artifact-key contracts consistent with architecture snapshot.

### 3.5 RBAC and Quota Submodule

Execution goal:

- Enforce backend policy controls for analysis trigger paths.

Guard order:

1. `require_auth`
2. `require_role`
3. `require_analysis_quota` (trigger route)

### Module 3 acceptance criteria

- Authenticated user can trigger workflow via backend API.
- Workflow transitions persist and stream via SSE.
- Final results persist and are queryable.
- RBAC/quota enforcement is active and observable.

---

## Module 4) Frontend Adaptation (Readability and UX Integration)

Status: pending

Architecture mapping: `./architecture.md#2-component-topology`, `./architecture.md#5-api-and-event-boundaries`, `./architecture.md#92-frontend-uiux-baseline-integrated`

Execution goal:

- Frontend consumes backend auth and workflow outputs with no legacy ownership paths.

### Acceptance criteria

- Frontend can trigger analysis and display live progress.
- Frontend can fetch and render final readable result payload.
- Frontend authorization logic remains backend-contract driven.

---

## Module 5) Phase 1 Completion Gate

Status: pending

Phase 1 is complete only when all module criteria are met end-to-end:

- trigger analysis -> observe SSE states -> read final result
- auth/rbac/quota enforced at backend boundary
- cache behavior consistent with key contract
- legacy paths pruned per hard cutover policy

---

## Phase 2 (Vision Only)

- Portfolio builder vision and recommendation loops begin after Phase 1 stabilization.
