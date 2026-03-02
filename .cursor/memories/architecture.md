# CFAI Architecture Snapshot

Last updated: 2026-03-01 (analysis workflow node and payload updates)
Purpose: latest agreed target-state architecture snapshot for Phase 1.

---

## 1) System Scope and Goals

- Deliver a Docker-first stock analysis platform with a clean split:
  - `frontend` for user UI
  - `backend` for APIs, orchestration, auth, and policy enforcement
  - `postgres` for durable storage
- Keep architecture modular so provider choices (FMP, model APIs, auth provider) can evolve without broad rewrites.

## 2) Component Topology

- Frontend:
  - Next.js App Router
  - shadcn/ui + Tailwind
  - Reads backend APIs only
- Backend:
  - FastAPI service as contract and orchestration authority
  - Hosts workflow domains and auth/rbac/quota enforcement
- Database:
  - PostgreSQL as source of truth for auth, workflow history, artifacts, and stock catalog
- External providers:
  - Market data/catalog provider adapters (currently planning for FMP endpoints)
  - AI/model providers for deep research and downstream reasoning nodes

## 3) Workflow Domains

### 3.1 Maintenance Workflow Domain

- Purpose: ingest and refresh foundational stock data in `stock_catalog`.
- Ownership: operational/batch workload, not user-facing analysis execution.
- Cadence:
  - immediate bootstrap seed run
  - weekly refresh cadence target
- Current v1 ingestion scope:
  - deterministic top-500 US active-common-stock seed (directory + screener proxy on Starter plan)
  - optional enrichment metadata (market cap/quote) when available
- Runtime characteristics:
  - idempotent upsert
  - retry/checkpoint-friendly
  - run-tracking for observability

### 3.2 Analysis Workflow Domain

- Purpose: run stock analysis state machine for user-driven or system-triggered analysis.
- Input model:
  - ticker or company-style query resolved to canonical stock identity
- Substate chain (v1 direction):
  - `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` ->
    `audit_growth_likelihood` -> `advisor_decision` -> `persist_artifacts` -> `publish_sse`
- Runtime characteristics:
  - persisted transitions
  - SSE progress visibility
  - artifact-oriented handoff (reference-heavy, payload-light context)

## 4) Data Architecture

### 4.1 Core Data Stores

- Auth and identity:
  - `users`
  - `user_sessions`
  - `oauth_accounts`
- Analysis orchestration:
  - `analysis_workflows` (workflow lifecycle state)
  - `analysis_workflow_events` (timeline/transition log, light payload)
  - `analysis_workflow_artifacts` (node output artifacts, heavy payload)
  - v1 deep-research payload shape: markdown-first report persisted in `analysis_workflows.result_payload`
- Catalog:
  - `stock_catalog` (canonical stock identity and resolver lookup base)

### 4.2 Read Model Direction

- Target direction: a dedicated projection/read-model table for stable frontend reads.
- Current status: deferred implementation; architecture direction is accepted, execution timing is roadmap-driven.

### 4.3 Cache and Artifact Contract

- Cache baseline: `symbol + input_hash + pipeline_version`
- Artifact key baseline:
  - `symbol + input_hash + pipeline_version + artifact_type + artifact_version`
- Heavy node outputs are stored in artifact persistence rather than passed through in-memory context.

## 5) API and Event Boundaries

- Backend API is the only frontend contract surface for auth and analysis.
- SSE is used for live analysis progress with machine-stable `state`/`substate`.
- Analysis trigger remains asynchronous:
  - immediate processing acknowledgement
  - follow-up via SSE and persisted status queries

### 5.1 Legacy Trigger/Completion Contract Parity

- Keep compatibility with legacy analysis expectations:
  - trigger returns immediate processing acknowledgment with trace/workflow ID
  - clients observe progress via state updates until terminal completion/failure
- Completion semantics should remain machine-stable and not rely on brittle human text matching.

## 6) Auth, RBAC, and Quota Boundary

- Backend remains authority for authorization and quota enforcement.
- Current auth scaffold can evolve, but guard order is stable:
  1. auth
  2. role
  3. analysis quota (trigger routes)
- Firebase Option B direction is accepted as a future pivot path:
  - frontend Firebase login
  - backend token verify + local session issuance

## 7) Provider Strategy and Constraints

- Catalog ingestion is provider-adapter based, currently planned around FMP MCP endpoint capabilities.
- Deep research remains model-provider based with cache-first cost controls.
- Provider-specific constraints (rate limits, paid endpoint availability) are handled in workflow/domain adapters, not in frontend contracts.

## 8) Open Items and Deferred Scope

- Final frontend read-model API contract is deferred.
- Final fuzzy threshold policy for query resolution is deferred until post-seed catalog validation.
- Full-market catalog expansion beyond S&P500 is deferred after prototype stabilization.
- Structured citation normalization from deep-research output is deferred; embedded citations in markdown are accepted for v1.

## 9) Integrated Baselines

### 9.1 Legacy Backend Analysis Baseline (Integrated)

- The prior Motia runtime behavior is treated as historical parity context, now integrated here:
  - asynchronous trigger contract
  - ordered long-running multi-step analysis pipeline
  - progress stream lifecycle and terminal completion signaling
  - packed final persistence payload behavior
- Modern FastAPI architecture is not required to preserve old implementation details,
  but it should preserve parity-critical user-visible behavior:
  - immediate traceable trigger response
  - visible ordered progress
  - durable result retrieval

### 9.2 Frontend UI/UX Baseline (Integrated)

- UI stack and conventions used as architecture-level guardrails:
  - Next.js App Router + shadcn/ui + Tailwind
  - route-group split (`marketing` vs `app`)
  - stock search as primary entrypoint into analysis flow
  - clear loading/error/access-state feedback patterns
- Frontend should continue consuming backend contracts only (auth/workflow/read paths),
  with consistent visual semantics for analysis lifecycle state.

## 10) Related References

- Execution tracker: `./roadmap.md`
- Decision rationale log: `./architecture-decisions.md`
