# CFAI Roadmap

Last validated: 2026-03-09 (blueprint canonicalized)
Purpose: single source of execution status and next actions.

## Session Briefing (mandatory order)

1. Where we are at
2. What we need to implement next
3. What we just implemented

- Where we are at: Modules 1-2 are complete; core analysis workflow + projection read model + demo UI are implemented and usable locally.
- What we need to implement next: execute the next blueprint stage from `product-blueprint.md`.
- What we just implemented: consolidated product-definition content into canonical blueprint and reduced duplicate specs in other memories.

## Module Status

- [x] Module 1 - Hard cutover and pruning
- [x] Module 2 - Containerized runtime foundation
- [~] Module 3 - Backend core (workflow + auth/rbac/quota) *(active)*
- [~] Module 4 - Frontend adaptation *(active)*
- [ ] Module 5 - Phase 1 completion gate

## Reality Check (2026-03-09)

- Backend analysis workflow exists end-to-end: `resolve_query` -> `deep_research` -> `structured_output` -> `reverse_dcf` -> `audit_growth_likelihood` -> `advisor_decision`.
- Projection read model exists and `/analysis/latest` reads from `analysis_workflow_projections` with fallback.
- Maintenance seed domain exists with admin endpoints and run tracking.
- Frontend `/demo/analysis` exists with tabs-first IA and SSE timeline.
- Quota guard is not implemented in backend yet.
- Auth is enforced on trigger, but not consistently enforced across all analysis read/event routes.

## Current Focus

- Active slice: Product experience milestone (research hub + compare table).
- Owners: user + coding agent.
- Blockers: see `./debuglog.md`.

## Next Execution Queue

1. Execute Stage 0 from `./product-blueprint.md`.
2. Execute Stage 1 from `./product-blueprint.md`.
3. Execute Stage 2 from `./product-blueprint.md`.
4. Execute Stage 3 from `./product-blueprint.md`.
5. Execute Stage 4 from `./product-blueprint.md`.
6. Run local acceptance checks per stage and record outcomes here.

## Phase Acceptance Gates

### Module 3 Gate
- Trigger path is stable for local use; policy hardening remains explicitly deferred in this milestone.
- Transitions persist and stream via SSE.
- Final artifacts/results are durable and queryable.

### Module 4 Gate
- Frontend trigger + live progress + blueprint-defined summary/drill-down rendering works from backend contracts only.
- UX remains readable and stable for partial/failed payloads.

### Module 5 Gate (Phase 1 complete)
- Research hub flow and lightweight compare flow both pass in one verified local runbook.

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
