# CFAI Roadmap

Last validated: 2026-03-10 (maintenance seed + workflow observability stabilization complete)
Purpose: single source of execution status and next actions.

## Session Briefing (mandatory order)

1. Where we are at
2. What we need to implement next
3. What we just implemented

- Where we are at: portfolio-home is implemented as the primary route with drag/add, weight edit/remove, seeded candidates, freshness/no-cache cues, and local persistence; infra baseline now targets Neon without Docker orchestration; maintenance seed and workflow observability reliability unblocks are completed.
- What we need to implement next: execute Stage P2 (portfolio metrics and candidate ranking/filtering for faster 1-2 minute decisions), starting with backend read aggregation contract for `portfolioRiskScore` / `expectedReturnRange` / `sectorConcentrationWarning`.
- What we just implemented: Neon DB migration baseline (`DATABASE_URL` pooled + `DATABASE_URL_DIRECT` for migrations), Docker artifact removal, env split (`frontend/.env.local`, `backend/.env`), maintenance seed simplification to screener-only enrichment with env-configurable Top-N + market-cap threshold plus idempotent naming (`top_us_market_cap`), and backend workflow observability upgrades (node-level timeline events, status/timeline APIs, heartbeat + stalled-no-progress monitor, structured server logs), including SQLAlchemy async session-concurrency fixes in orchestrator/reverse DCF paths.

## Module Status

- [x] Module 1 - Runtime foundation and workflow plumbing
- [x] Module 2 - Projection-backed analysis read path
- [x] Module 3 - Portfolio-first UX reframe (docs/contracts)
- [~] Module 4 - Portfolio home implementation (P1/P2) *(active)*
- [ ] Module 5 - Detail reorg + deep escalation flow (P3)
- [ ] Module 6 - Internal observation lab boundary + milestone gate (P4)

## Reality Check (2026-03-10)

- Backend analysis workflow exists end-to-end: `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` -> `audit_growth_likelihood` -> `advisor_decision`.
- Projection read model exists; `/analysis/latest` is projection-first with fallback.
- Frontend now has dedicated `/portfolio` route for primary product flow.
- `/demo/analysis` has been reduced to internal controls/status badges for observability.
- Product priority changed: portfolio builder is the intended user product, not workflow observability.
- Quota guard is still deferred; auth/rbac are intentionally relaxed in local milestone flow.

## Current Focus

- Active slice: Stage P2 portfolio metrics and candidate ranking/filtering (with Neon-backed terminal-native environment).
- Owners: user + coding agent.
- Blockers: none active for seed/observability; see `./debuglog.md` only for newly reproducible issues.

## Detailed Implementation Queue

### Stage P0 - Product Reframe and Contract Alignment (Done)
Status: `completed`
- Update canonical product hierarchy in `product-blueprint.md`.
- Lock policy: lightweight default + explicit deep.
- Lock persistence policy: local save only for v1.

### Stage P1 - Portfolio Home Skeleton (Done)
Status: `completed`
Goal: ship functional portfolio-home interactions using dedicated portfolio route.

Implementation checklist:
1. Frontend layout and state model
   - add portfolio-home two-panel layout shell (left builder, right candidate cards)
   - define client state for positions and local-save hydration
   - canonical targets:
     - `frontend/src/app/portfolio/page.tsx`
2. Portfolio interactions
   - drag/add stock into portfolio with default weight
   - weight edit and remove interactions
   - empty-state UX for start-empty flow
3. Candidate cards
   - render seeded symbol cards with freshness/no-cache cue
   - wire drag-to-add (required) and click add-to-portfolio action
4. Local persistence
   - serialize and restore working portfolio from browser storage
   - add lightweight schema version key for future migration

Acceptance:
- user can build a portfolio from empty state and recover it after page reload.

### Stage P2 - Portfolio Metrics and Candidate Ranking
Status: `pending`
Goal: make the page useful for 1-2 minute portfolio decisions.

Implementation checklist:
1. Backend read aggregation
   - expose projection-backed fields needed for metrics and card cues
   - canonical targets:
     - `backend/app/routers/workflow.py`
     - `backend/app/workflows/analysis/projections/store.py`
2. Portfolio metrics engine (v1)
   - compute/render:
     - `portfolioRiskScore`
     - `expectedReturnRange`
     - `sectorConcentrationWarning`
   - recompute on all position/weight changes
3. Candidate feed ranking/filtering
   - implement initial ranking default (to be finalized from open decision)
   - preserve responsiveness under cache-first policy

Acceptance:
- key metrics update correctly when portfolio constituents or weights change.

### Stage P3 - Detail Reorganization and Deep Escalation
Status: `pending`
Goal: preserve depth while making detail readable and controllable.

Implementation checklist:
1. Reorganize detail information hierarchy
   - summary first, evidence second, deep internals last
2. Add explicit deep action
   - show current analysis mode
   - trigger deep run only from explicit user action
3. Staleness-window UX
   - keep cached detail visible during refresh
   - show progression/status without blanking content
4. Canonical targets:
   - `frontend/src/app/demo/analysis/page.tsx`
   - `backend/app/routers/workflow.py`
   - `backend/app/workflows/analysis/orchestrator.py`

Acceptance:
- user can read organized detail quickly and intentionally escalate to deep analysis.

### Stage P4 - Internal Observation Lab Boundary
Status: `pending`
Goal: keep workflow observability available internally without steering product UX.

Implementation checklist:
1. Label and bound analysis-lab role as internal.
2. Ensure portfolio-home is the default product path.
3. Keep lab instrumentation useful for debugging and parity checks.

Acceptance:
- team can still inspect workflow internals while primary UX remains portfolio-first.

## Phase Acceptance Gates

### Module 4 Gate (P1/P2)
- Portfolio-home supports add/edit/remove flows and local persistence.
- Risk/return/concentration metrics are visible and reactive.

### Module 5 Gate (P3)
- Organized detail view and explicit deep escalation are working with clear state transitions.

### Module 6 Gate (P4, phase complete)
- Portfolio-home and internal observation lab have clear product/tool separation.

## Open Decisions (Execution-Critical)

1. Default add weight: fixed to `5%` for P1; revisit only if user requests rebalance behavior.
2. Risk/return formula shape for v1: heuristic now vs model-backed now.
3. Candidate feed default sorting: quality-first vs portfolio-impact-first.
4. Seed refresh policy for initial ~50 stocks: manual vs scheduled.

## Product Blueprint Reference

- Canonical blueprint: `./product-blueprint.md`
- This roadmap tracks execution status only; product definitions must live in blueprint.

## Working Loop (context-optimized)

1. **Brief** from this file in mandatory order.
2. **Plan** only the active slice (avoid broad refactors).
3. **Implement** focused changes.
4. **Validate** with targeted runtime checks.
5. **Record**:
   - progress here
   - rationale in `architecture-decisions.md` when decisions change
   - blockers in `debuglog.md`
   - reusable lessons in `memo.md`
