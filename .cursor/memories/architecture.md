# CFAI Architecture Snapshot

Last validated: 2026-03-09 (product specs delegated to blueprint)
Purpose: concise target-state + current-state architecture for Phase 1.

## 1) System Shape

- `frontend` (Next.js App Router, shadcn/ui, Tailwind) consumes backend APIs only.
- `backend` (FastAPI) owns orchestration, auth/policy boundary, and provider integration.
- `postgres` is source of truth for auth, workflow state/events/artifacts, projections, and catalog.

## 2) Workflow Domains

- Shared runtime primitives: `backend/app/core/workflow`.
- Domain packages: `backend/app/workflows/maintenance` and `backend/app/workflows/analysis`.

### Maintenance (implemented)
- Purpose: deterministic catalog seed/refresh into `stock_catalog`.
- Current shape: top-500 US seed workflow with run tracking and admin APIs.

### Analysis (implemented core)
- Purpose: async user-driven stock analysis pipeline.
- Node chain: `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` -> `audit_growth_likelihood` -> `advisor_decision` -> persistence + SSE.
- Contract: trigger returns processing + trace ID; progress is SSE + persisted events.

## 3) Data and Read Model

- Source-of-truth operational tables:
  - `analysis_workflows`
  - `analysis_workflow_events`
  - `analysis_workflow_artifacts`
- Frontend read model:
  - `analysis_workflow_projections` (event/artifact-driven updates)
  - versioned normalization boundary via `contract_version`
- Current API read path:
  - `/analysis/latest` reads projection first, then fallback to workflow row.

## 4) Auth/RBAC/Quota Boundary

- Accepted boundary order: auth -> role -> quota (trigger flows).
- Current reality:
  - `require_auth` exists and is used on trigger paths.
  - role guard exists and is used for maintenance admin routes.
  - quota guard is not implemented yet.
  - analysis read/event routes need explicit final auth policy decision and enforcement.

## 5) Provider and Payload Strategy

- Catalog data path is adapter-based and provider-constrained.
- Deep research is model-provider based; v1 persisted payload remains markdown-first with embedded citations.
- Heavy node outputs are stored as artifacts/projections, not threaded as large in-memory context.

## 6) Deferred / Open

- Quota implementation and policy observability (deferred in local-first milestone).
- Finalized auth policy for analysis read/event endpoints (deferred in local-first milestone).
- Reprojection tooling + stronger projection contract hardening.
- Seed universe expansion beyond current top-500 proxy set.

## 7) Product Experience Reference

- Product intent, UX hierarchy, and staged rollout are canonicalized in `./product-blueprint.md`.
- This file should only capture system architecture constraints required to deliver that blueprint.

## 8) References

- Execution tracker: `./roadmap.md`
- Decisions: `./architecture-decisions.md`
- Product blueprint: `./product-blueprint.md`
