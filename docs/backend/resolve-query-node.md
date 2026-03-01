# Resolve Query Node Architecture (Module 3.3A/3.3B Slice)

Last updated: 2026-02-27
Status: Design documented (implementation pending)
Scope: First production workflow node `resolve_query` and its immediate integration boundaries.

## 1) Objective

Define the first workflow node as `resolve_query` so the backend can accept ticker or company-name input, deterministically resolve a canonical stock identity, persist resolver artifacts, and pass reference-only context to downstream nodes.

This document is implementation guidance, not an implementation record.

## 2) Why This Node Is First

- It stabilizes the workflow trigger contract early (`query` + legacy `symbol` compatibility).
- It creates the canonical handoff fields (`stock_id`, `artifact_id`, `cache_key`) that downstream nodes depend on.
- It establishes the artifact/event split pattern before expensive nodes (especially `deep_research`) are introduced.
- It supports cache-key consistency from day one to avoid future migration churn.

## 3) Baseline Context

Current backend baseline before this node is implemented:

- Orchestrator exists with placeholder steps in `backend/app/workflow/orchestrator.py`.
- Workflow and event tables exist:
  - `analysis_workflows`
  - `analysis_workflow_events`
- Trigger route currently accepts `{ "symbol": string }`.
- `stock_catalog` and `analysis_workflow_artifacts` are required by roadmap but not yet implemented.

## 4) Input/Output Contract (Design)

### Trigger input (external API)

- Preferred field: `query` (ticker or company name).
- Legacy alias: `symbol` (accepted for backward compatibility).
- Internal normalization: convert to one `query_text` field before orchestration.

### Node input (internal)

- `query_text`: raw user input after alias normalization.
- `pipeline_version`: version tag used in cache-key derivation.
- Optional request metadata used only for tracing and diagnostics.

### Node output (internal context references only)

- `stock_id`: canonical stock identity reference.
- `resolution_artifact_id`: ID of persisted `query_resolution` artifact.
- `resolution_cache_key`: cache key for resolver artifact lineage/reuse.
- `resolved_symbol`: canonical symbol for downstream node queries.
- `resolution_meta_ref` (optional): lightweight pointer/summary metadata, not full candidate payload.

Heavy data (candidate lists, confidence details, resolver diagnostics) stays in artifact payload and must not be propagated as full in-memory context.

## 5) Resolution Policy (v1 Deterministic)

Resolution order:

1. Exact ticker match in `stock_catalog`.
2. Exact or normalized company-name match in `stock_catalog`.
3. Optional external provider fallback hook (only if configured).
4. Deterministic best-candidate selection when multiple candidates exist.

v1 ambiguity rule:

- Always auto-select one candidate (no interactive disambiguation).
- Persist all candidates and confidence metadata for observability/auditability.

No-candidate rule:

- Transition workflow to controlled `failed` path with concise diagnostic metadata in events.

## 6) Persistence and Cache Design

### Storage split

- `analysis_workflow_events`: timeline transitions and lightweight diagnostics only.
- `analysis_workflow_artifacts`: resolver payload and candidate/confidence details.
- `stock_catalog`: canonical stock identity records used for deterministic lookup/memory cache.

### Artifact type

- `query_resolution`

### Cache-key contract (v1 baseline)

- `symbol + input_hash + pipeline_version + artifact_type + artifact_version`

`input_hash` is derived from normalized query input; hashing algorithm must be deterministic and stable across services/environments.

## 7) Orchestrator Integration Contract

- Introduce `resolve_query` substate at the start of the linear chain.
- Emit stable, machine-readable event payload fields, including:
  - selected symbol
  - resolution source (catalog/provider)
  - ambiguity summary (for example, candidate_count)
- Keep context handoff thin: references only.

Target handoff from this slice:

`resolve_query -> deep_research`

## 8) API Compatibility Policy

- Keep existing callers functional by accepting `symbol`.
- Prefer `query` for all new callers and docs/examples.
- Internally unify both fields to `query_text` before orchestration.
- Do not change auth/session behavior in this slice beyond compatibility needs required by trigger parsing.

## 9) Validation Gates (Design-Time Acceptance)

- Happy path: ticker input resolves correctly.
- Happy path: company-name input resolves correctly.
- Ambiguity path: deterministic pick is applied and candidate metadata is persisted.
- Failure path: no candidates yields controlled `failed` transition with diagnostics.
- Persistence path: one `query_resolution` artifact row is created and linked.
- Event path: `resolve_query` substate appears in persisted events and SSE stream.

## 10) Out of Scope

- Firebase auth pivot execution.
- Deep research implementation details.
- Final `structured_output` schema stabilization.

## 11) Implementation Checklist (For Next Coding Session)

1. Define resolver request/response/context types.
2. Add minimal persistence foundations (`stock_catalog`, `analysis_workflow_artifacts`, workflow linkage fields).
3. Implement `ResolveQueryNode` with deterministic selection and artifact write.
4. Wire `resolve_query` into orchestrator state/substate event flow.
5. Update trigger request schema to support `query` + legacy `symbol`.
6. Run targeted validation scenarios for success/ambiguity/failure and persistence/event verification.

