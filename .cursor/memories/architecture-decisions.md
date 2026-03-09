# CFAI Architecture Decision Log

Last updated: 2026-03-04
Purpose: record architecture decisions, alternatives, rationale, and consequences.

---

## ADR Template

### [ADR-XXXX] Decision title
- Date:
- Status: `proposed` | `accepted` | `superseded`
- Context:
- Decision:
- Alternatives considered:
  - Option A:
  - Option B:
- Consequences:
  - Pros:
  - Cons:
- Related architecture section: `./architecture.md#...`
- Related roadmap phase/step: `./roadmap.md#...`

---

## Accepted Decisions

### [ADR-0001] Split runtime into maintenance and analysis workflow domains
- Date: 2026-02-27
- Status: `accepted`
- Context:
  - Stock-data ingestion cadence and operational behavior differ from user-facing analysis execution.
  - Coupling both domains in a single workflow increases failure blast radius and complexity.
- Decision:
  - Keep stock catalog ingestion in standalone `maintenance` workflow domain.
  - Keep user-facing analysis in separate `analysis` workflow domain.
- Alternatives considered:
  - Option A: keep ingestion and analysis in one orchestration graph.
  - Option B: separate operational and user workflows.
- Consequences:
  - Pros:
    - cleaner failure boundaries
    - simpler scheduling and retries for ingestion
    - clearer ownership and observability
  - Cons:
    - extra coordination points between domains
- Related architecture section: `./architecture.md#3-workflow-domains`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0002] Ingestion-first sequencing before resolve_query implementation
- Date: 2026-02-27
- Status: `accepted`
- Context:
  - Query resolution quality depends on real catalog content and normalization characteristics.
- Decision:
  - Implement catalog ingestion first, validate seeded data quality, then finalize `resolve_query` thresholds/tie-breakers.
- Alternatives considered:
  - Option A: implement resolver first using assumed catalog structure.
  - Option B: ingest and validate data first, then finalize resolver behavior.
- Consequences:
  - Pros:
    - avoids speculative resolver heuristics
    - faster convergence on deterministic matching behavior
  - Cons:
    - resolver implementation starts later
- Related architecture section: `./architecture.md#31-maintenance-workflow-domain`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0003] v1 catalog seed scope is S&P500-first
- Date: 2026-02-27
- Status: `accepted`
- Context:
  - Need practical prototype coverage with manageable ingestion and validation scope.
- Decision:
  - Start with S&P500 (~500 symbols) for bootstrap seed.
  - Expand broader universe after prototype stabilization.
- Alternatives considered:
  - Option A: full-market seed immediately.
  - Option B: S&P500-first seed and staged expansion.
- Consequences:
  - Pros:
    - lower implementation and QA cost
    - faster path to deterministic resolver behavior
  - Cons:
    - limited symbol coverage in early versions
- Related architecture section: `./architecture.md#31-maintenance-workflow-domain`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0004] Auth implementation sequencing defers Firebase Option B pivot
- Date: 2026-02-26
- Status: `accepted`
- Context:
  - Current auth scaffold is sufficient to avoid blocking analysis workflow implementation.
  - Immediate auth pivot would reduce focus on workflow/materialization.
- Decision:
  - Keep current backend auth/session scaffold as development adapter.
  - Defer Firebase Option B pivot until workflow core is stable.
- Alternatives considered:
  - Option A: immediate teardown and Firebase rebuild.
  - Option B: defer pivot while maintaining minimal current auth path.
- Consequences:
  - Pros:
    - protects workflow delivery velocity
    - avoids unnecessary early churn
  - Cons:
    - temporary auth path persists longer
- Related architecture section: `./architecture.md#6-auth-rbac-and-quota-boundary`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0005] Read-path direction is hybrid; projection table is target read model
- Date: 2026-02-27
- Status: `accepted`
- Context:
  - Website must read processed results efficiently while preserving ability to fill missing analyses.
  - Final frontend read contract is not the immediate implementation focus.
- Decision:
  - Direction: hybrid read-miss policy.
    - if processed result exists, serve it
    - if missing, trigger analysis workflow
  - Long-term frontend read target: dedicated projection/read-model table.
  - Frontend read integration details are deferred for now.
- Alternatives considered:
  - Option A: precompute-only serving.
  - Option B: on-demand-only serving.
  - Option C: hybrid policy with read model target.
- Consequences:
  - Pros:
    - balances responsiveness and data freshness
    - supports staged rollout without locking brittle read contracts
  - Cons:
    - requires eventual reconciliation between async generation and read consistency
- Related architecture section: `./architecture.md#42-read-model-direction`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0006] Starter-plan seed universe uses directory+screener top-500 US proxy
- Date: 2026-03-01
- Status: `accepted`
- Context:
  - Starter plan access may not include an S&P500 constituent endpoint.
  - Resolver implementation still requires a deterministic ~500-symbol seeded catalog.
- Decision:
  - Use stock directory plus screener-based market-cap ranking to derive a deterministic top-500 US active common-stock seed universe.
  - Keep endpoint strategy hybrid (prefer stable endpoints, fallback to v3).
  - Keep provider failure policy fail-closed for seed runs.
- Alternatives considered:
  - Option A: block all seed work until S&P500 endpoint access is available.
  - Option B: use directory+screener top-500 proxy for v1 seed.
- Consequences:
  - Pros:
    - unblocks ingestion-first sequencing on current subscription
    - preserves deterministic resolver readiness with bounded catalog size
  - Cons:
    - universe is not exact S&P500 membership
- Related architecture section: `./architecture.md#31-maintenance-workflow-domain`
- Related roadmap phase/step: `./roadmap.md#module-3-backend-core-fastapi-workflow-auth-rbac-quota`

### [ADR-0007] v1 deep-research payload persists as markdown-first with embedded citations
- Date: 2026-03-01
- Status: `accepted`
- Context:
  - Deep research output is long-form report content used directly by downstream workflow nodes and frontend rendering.
  - Attempting strict citation extraction from interaction metadata is schema-sensitive and not required to unblock current node sequence.
- Decision:
  - Persist deep research output as a markdown-first payload in `analysis_workflows.result_payload`.
  - Keep citations embedded in the markdown report text for v1; treat separate structured citation extraction as deferred enhancement.
  - Keep report payload reusable by downstream nodes from the same persisted result object.
- Alternatives considered:
  - Option A: require normalized citation array extraction before considering deep-research node complete.
  - Option B: accept markdown-first persistence with embedded citations for v1 and defer normalization.
- Consequences:
  - Pros:
    - unblocks downstream node implementation (`structured_output` onward) with stable persisted payload
    - minimizes parser fragility and rework risk in early integration phase
  - Cons:
    - machine-readable citation analytics are limited until normalization is implemented
- Related architecture section: `./architecture.md#4-data-architecture`
- Related roadmap phase/step: `./roadmap.md#33-analysis-workflow-submodule`

### [ADR-0008] Add frontend-optimized workflow projection read model
- Date: 2026-03-04
- Status: `accepted`
- Context:
  - Frontend pages increasingly need one-call retrieval of workflow run status + final payload + key node outputs.
  - Current read path can require combining workflow row, event timeline, and artifact rows, which increases frontend orchestration and read latency.
- Decision:
  - Keep `analysis_workflow_events` and `analysis_workflow_artifacts` as source-of-truth operational/audit stores.
  - Add a dedicated projection/read-model table for frontend-facing aggregate payloads.
  - Projection writes are event-driven on workflow transitions, with additional updates on persisted node artifacts/result payload.
  - Introduce a single projection normalization boundary that emits a versioned frontend contract (`contract_version`) with deterministic defaults and guardrails.
  - Switch `/analysis/latest` read path to projection-backed retrieval while preserving payload compatibility.
- Alternatives considered:
  - Option A: query multiple source tables from frontend for every workflow detail view.
  - Option B: aggregate into a projection table while preserving source tables.
- Consequences:
  - Pros:
    - lower frontend retrieval complexity and fewer network/database round trips
    - stable backend contract for UI rendering
    - preserves debug/replay fidelity in source tables
    - supports contract evolution via reprojection from source artifacts
  - Cons:
    - additional write/update path and consistency management
    - requires normalization/version discipline as node payloads evolve
- Related architecture section: `./architecture.md#42-read-model-direction`
- Related roadmap phase/step: `./roadmap.md#34-persistence-and-cache-submodule`
