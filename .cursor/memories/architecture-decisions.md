# CFAI Architecture Decision Log

Last updated: 2026-02-27
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
