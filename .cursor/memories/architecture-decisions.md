# CFAI Architecture Decisions

Last validated: 2026-03-09 (local-dev policy bypass + runtime stability notes)
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
- Status: `accepted`
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

## Open Decision Candidates

- Auth/rbac/quota reintroduction plan and sequencing after core milestone completion.
- Quota model details (limits, reset cadence, role overrides, error semantics).

## References

- Architecture snapshot: `./architecture.md`
- Execution tracker: `./roadmap.md`
- Product blueprint: `./product-blueprint.md`

## Canonicality Note

- Use this file for decision rationale only.
- Product specification details should live in `./product-blueprint.md` and be referenced here.
