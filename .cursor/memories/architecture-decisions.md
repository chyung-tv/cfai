# CFAI Architecture Decisions

Last validated: 2026-03-11 (maintenance consolidation + observability/persistence fixes)
Purpose: compact ADR index with only active decision signal.

## Status Keys

- `accepted`: active and should guide implementation.
- `superseded`: kept for historical trace only.

## Accepted ADRs (Compact)

### ADR-0001 - Split maintenance and analysis workflow domains
- Date: 2026-02-27
- Status: `accepted`
- Why: ingestion and user analysis have different failure/retry/ownership patterns.
- Impact: keep separate domain packages and runtime boundaries.

### ADR-0002 - Ingestion-first sequencing before resolver hardening
- Date: 2026-02-27
- Status: `accepted`
- Why: resolver quality depends on real catalog shape.
- Impact: validate seeded catalog before finalizing resolver policy.

### ADR-0003 - v1 seed scope is ~500-symbol proxy set
- Date: 2026-02-27
- Status: `accepted`
- Why: fast deterministic prototype coverage with bounded cost.
- Impact: broader market expansion is deferred.

### ADR-0004 - Defer Firebase Option B auth pivot
- Date: 2026-02-26
- Status: `accepted`
- Why: current session auth is enough to avoid blocking workflow delivery.
- Impact: keep existing auth scaffold; revisit after Module 3 stabilization.

### ADR-0005 - Hybrid read strategy with projection as target model
- Date: 2026-02-27
- Status: `accepted`
- Why: balance responsiveness and eventual completeness.
- Impact: projection-backed reads are preferred; generation-on-miss remains allowed by policy.

### ADR-0006 - Starter-plan catalog seed uses directory+screener proxy
- Date: 2026-03-01
- Status: `accepted`
- Why: plan limits may block exact S&P500 endpoint access.
- Impact: deterministic top-500 US proxy seed is acceptable for v1.

### ADR-0007 - Deep-research payload persists markdown-first
- Date: 2026-03-01
- Status: `accepted`
- Why: unblocks downstream nodes with stable payload while citation normalization is deferred.
- Impact: keep embedded citations; defer structured citation extraction.

### ADR-0008 - Frontend-optimized projection read model
- Date: 2026-03-04
- Status: `accepted`
- Why: multi-table frontend reads were costly and brittle.
- Impact: `analysis_workflow_projections` is the UI read path with `contract_version` boundary.

### ADR-0009 - Local-first product milestone prioritizes research hub over policy hardening
- Date: 2026-03-09
- Status: `superseded`
- Why: current local objective is solving stock analysis workflow usability and decision-support flow first.
- Impact: implement summary/drill-down/compare blueprint before auth/rbac/quota hardening.

### ADR-0010 - v1 is evidence-first without explicit final recommendation label
- Date: 2026-03-09
- Status: `accepted`
- Why: user wants transparent reasoning support, not an opaque buy/hold/avoid output.
- Impact: UI emphasizes business quality + valuation legitimacy + thesis; recommendations remain optional/derived later.

### ADR-0011 - Staleness-window read policy for single-stock analysis
- Date: 2026-03-09
- Status: `accepted`
- Why: one-click flow should feel fast while still allowing refreshed analysis.
- Impact: if analysis is fresh show immediately; if stale trigger refresh and stream updates.

### ADR-0012 - Dev/test deep-research uses flash-lite preview with grounding; production keeps deep-research endpoint path
- Date: 2026-03-09
- Status: `accepted`
- Why: local workflow testing must remain low-cost while preserving full node-chain behavior and research grounding.
- Impact:
  - Dev/Test: deep-research node runs with `gemini-3.1-flash-lite-preview` and grounding enabled by env toggle.
  - Production: deep-research node can route to deep-research endpoint/model; non-deep-research structured nodes remain flash-lite.
  - Environment control is env-only (`APP_ENV`, `DEEP_RESEARCH_USE_ENDPOINT_IN_PRODUCTION`, `DEEP_RESEARCH_DEV_GROUNDING_ENABLED`, model env vars).

### ADR-0013 - Temporarily disable auth/rbac guards for local core milestone execution
- Date: 2026-03-09
- Status: `accepted`
- Why: unblock rapid core workflow/UX iteration while policy hardening is explicitly deferred in the local-first milestone.
- Impact:
  - Remove `require_auth` enforcement on `/analysis/trigger` and allow `user_id=None`.
  - Remove admin role guards on maintenance seed routes in local dev flow.
  - Reintroduce auth/rbac/quota guards as a follow-up hardening slice after core milestone completion.

### ADR-0014 - Portfolio builder is v1 primary product surface
- Date: 2026-03-10
- Status: `accepted`
- Why: user intent is portfolio construction and portfolio health monitoring; workflow visibility alone is not the product outcome.
- Impact:
  - portfolio-home becomes north-star UX
  - analysis workflow is positioned as supporting intelligence engine
  - implementation sequencing prioritizes portfolio modules over analysis-lab expansion

### ADR-0015 - Analysis UI is internal observation lab, not primary journey
- Date: 2026-03-10
- Status: `accepted`
- Why: the current analysis-heavy UI is useful for debugging engine behavior but should not define main user journey.
- Impact:
  - keep analysis UI for internal troubleshooting and parity checks
  - enforce clear product/tool boundary in roadmap and UI labeling

### ADR-0016 - v1 interaction policy: lightweight default, deep explicit, cache-first with freshness badge
- Date: 2026-03-10
- Status: `accepted`
- Why: balance speed, cost, and user control while preserving transparency.
- Impact:
  - symbols default to lightweight analysis mode
  - deep analysis runs only when explicitly requested by user action
  - cached projection is shown immediately with `last updated` freshness badge

### ADR-0017 - v1 portfolio state persistence is local browser storage
- Date: 2026-03-10
- Status: `accepted`
- Why: unblock rapid UX iteration without introducing account/data model complexity in this milestone.
- Impact:
  - persist one working portfolio locally in browser storage
  - defer account-backed multi-portfolio persistence to later phase

### ADR-0018 - Use Neon pooled runtime URL and direct migration URL; remove Docker local stack
- Date: 2026-03-10
- Status: `accepted`
- Why: deployment target is serverless/ephemeral compute, and local workflow preference is terminal-native without Docker orchestration.
- Impact:
  - `DATABASE_URL` is Neon pooled endpoint for backend runtime traffic.
  - `DATABASE_URL_DIRECT` is preferred for Alembic migrations.
  - Remove `docker-compose.yml` and Dockerfiles from active setup.

### ADR-0019 - Backend-first workflow observability with persisted node timeline and stalled diagnostics
- Date: 2026-03-10
- Status: `accepted`
- Why: debugging stuck traces (especially around `reverse_dcf`) required deterministic visibility in DB/API/logs instead of relying on frontend stream state.
- Impact:
  - Persist node-level progress events (`node_started`, `node_heartbeat`, `node_succeeded`, `node_failed`, `node_timeout`) in `analysis_workflow_events`.
  - Add operator-focused endpoints for trace status/timeline (`/analysis/workflows/{trace_id}/status`, `/analysis/workflows/{trace_id}/timeline`).
  - Add backend stalled-no-progress monitor with env-configurable thresholds/cooldown and structured correlation logs.
  - Keep implementation backend-first; frontend observability changes remain optional and deferred.

### ADR-0020 - P2 portfolio metrics are backend-owned; candidate default ranking is blended
- Date: 2026-03-11
- Status: `accepted`
- Why: keep portfolio metrics consistent across clients and avoid divergence from duplicated frontend-only formulas while preserving fast candidate triage.
- Impact:
  - Add backend contract endpoint for portfolio metrics (`/analysis/portfolio/metrics`) returning `portfolioRiskScore`, `expectedReturnRange`, and `sectorConcentrationWarning`.
  - Frontend `portfolio-home` consumes backend metrics contract with safe fallback behavior.
  - Candidate feed default sort for v1 is locked to `blended`.

### ADR-0021 - Internal observe page is consolidated into maintenance module controls
- Date: 2026-03-11
- Status: `accepted`
- Why: operational workflows now require one internal surface to seed/fetch catalog and trigger controlled mass analysis updates without polluting the primary portfolio UX.
- Impact:
  - `/demo/analysis` is maintained as an internal maintenance page with sections for fetch, stock catalogue, and mass update analysis.
  - Add maintenance catalog listing API for FE stock selection (`/api/v1/admin/maintenance/catalog/stocks`).
  - Mass update uses explicit operator controls (mode/force/run count) with bounded client-side concurrency.

### ADR-0022 - Analysis workflow observability uses app-level JSON logs and trace-level persistence inspection
- Date: 2026-03-11
- Status: `accepted`
- Why: access logs alone were insufficient to diagnose whether batch-triggered workflows actually persisted artifacts/snapshots; operators needed deterministic correlation per trace.
- Impact:
  - Configure backend app logging to emit JSON logs at app level with correlation fields (`trace_id`, `symbol`, `event_type`, `substate`, `duration_ms`, `error_code`).
  - Keep workflow lifecycle visibility in backend logs for enqueue, node progress, artifact persistence, projection updates, and terminal transitions.
  - Add `/analysis/workflows/{trace_id}/persistence` diagnostic API for workflow/event/artifact/snapshot linkage checks and basic stall-vs-overwrite classification.

### ADR-0023 - Projection transition updates must preserve artifact-backed payload fields
- Date: 2026-03-11
- Status: `accepted`
- Why: transition-only projection upserts could regress snapshot details/summary to null by normalizing from an empty base payload between artifact writes.
- Impact:
  - Build projection normalization base by merging existing snapshot payload when workflow payload is empty.
  - Preserve previously materialized `structuredOutput`/`reverseDcf`/`auditGrowthLikelihood`/`advisorDecision`/`reportMarkdown`/`citations` across transition updates.
  - Use this as the baseline anti-regression rule for snapshot persistence correctness.

## Open Decision Candidates

- Auth/rbac/quota reintroduction plan and sequencing after core milestone completion.
- Quota model details (limits, reset cadence, role overrides, error semantics).
- Default add weight for portfolio builder (`5%` proposed).
- v1 formula contract for portfolio risk score and expected return range.

## References

- Architecture snapshot: `./architecture.md`
- Execution tracker: `./roadmap.md`
- Product blueprint: `./product-blueprint.md`

## Canonicality Note

- Use this file for decision rationale only.
- Product specification details should live in `./product-blueprint.md` and be referenced here.
